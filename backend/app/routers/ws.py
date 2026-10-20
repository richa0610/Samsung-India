import asyncio
import contextvars
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, NamedTuple, Optional

from jose import JWTError, jwt

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.tenant import tenant_manager
from app.dependencies.auth import resolve_principal
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.repositories import attendance_repository
from app.services import conference_access

router = APIRouter(tags=["ws"])
logger = logging.getLogger("ws")


class ConnectionManager:
    """Tracks live WebSocket connections two ways, both keyed by tenant so a same-named account
    or a same-uid conference in a different tenant can never receive another tenant's events:

    - `/ws/admin` connections keyed by (tenant_id, username), so a write endpoint can push a
      small "something changed" event to just the trainer who owns it (`send_to`) or to every
      other connection in the SAME tenant (`broadcast` - there is no cross-tenant variant; every
      event this app sends is about one tenant's own training/attendance/trainee data).
    - per-conference *rooms* (`/ws/live/{conferenceUid}`) keyed by (tenant_id, conferenceUid),
      that both the trainer and every joined trainee of a live session sit in, so a Live Quiz
      action can nudge the whole room to refetch (`send_to_room`). The event payload is
      deliberately thin (`{"type": "live_quiz"}`) - all real state travels over REST, same
      philosophy as src/services/liveEvents.ts. Room MEMBERSHIP is still authorized on join
      (see `_authorize_room`) - the thin payload was never a substitute for that.
    """

    def __init__(self) -> None:
        self._connections: dict[tuple[str, str], set[WebSocket]] = {}
        self._rooms: dict[tuple[str, str], set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str, username: str) -> None:
        self._connections.setdefault((tenant_id, username), set()).add(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str, username: str) -> None:
        key = (tenant_id, username)
        sockets = self._connections.get(key)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(key, None)

    # The senders below loop over a .copy() on purpose: a failed send disconnects that socket
    # (removing it from the very set/dict being looped over), and every `await` lets other
    # connections join or leave meanwhile - looping over the live collection would raise
    # "RuntimeError: Set changed size during iteration".
    async def send_to(self, tenant_id: str | None, username: str | None, event: dict) -> None:
        if not tenant_id or not username:
            return
        key = (tenant_id, username)
        for websocket in self._connections.get(key, set()).copy():
            try:
                await websocket.send_json(event)
            except Exception:
                self.disconnect(websocket, tenant_id, username)

    async def broadcast(self, tenant_id: str | None, event: dict) -> None:
        """Every OTHER connection in this same tenant - never another tenant's. If a genuine
        cross-tenant (e.g. platform-wide Super Admin) event is ever needed, it must be a
        separate, explicitly-named method, not a widened version of this one."""
        if not tenant_id:
            return
        for (t, username), sockets in self._connections.copy().items():
            if t != tenant_id:
                continue
            for websocket in sockets.copy():
                try:
                    await websocket.send_json(event)
                except Exception:
                    self.disconnect(websocket, tenant_id, username)

    # --- per-conference rooms -------------------------------------------------

    async def join_room(self, websocket: WebSocket, tenant_id: str, room: str) -> None:
        self._rooms.setdefault((tenant_id, room), set()).add(websocket)

    def leave_room(self, websocket: WebSocket, tenant_id: str, room: str) -> None:
        key = (tenant_id, room)
        sockets = self._rooms.get(key)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._rooms.pop(key, None)

    async def send_to_room(self, tenant_id: str | None, room: str | None, event: dict) -> None:
        if not tenant_id or not room:
            return
        key = (tenant_id, room)
        for websocket in self._rooms.get(key, set()).copy():
            try:
                await websocket.send_json(event)
            except Exception:
                self.leave_room(websocket, tenant_id, room)


manager = ConnectionManager()


# At most this many WebSocket sign-in checks touch the database at once, each on one of these
# threads - never on the event loop, where one slow database would freeze every request and socket.
# The per-tenant request cap (core/tenant_limit.py) doesn't cover WebSockets, and both apps reconnect
# every few seconds, so after a deploy every open device signs in again at once: this keeps that
# burst to a few of a tenant's pooled connections and off the worker threads requests run on. A
# check over the cap waits in the pool's queue, holding neither a thread nor a connection.
HANDSHAKE_CONCURRENCY = 5
_handshake_pool = ThreadPoolExecutor(max_workers=HANDSHAKE_CONCURRENCY, thread_name_prefix="ws-auth")


class SocketIdentity(NamedTuple):
    """Who an open socket belongs to: plain values copied out of the sign-in check, so the socket
    holds no database session - nor the pooled connection a session keeps checked out - for the
    hours it may stay open."""

    tenant_id: str
    username: Optional[str]  # what `/ws/admin` events are addressed by (`ConnectionManager.send_to`)


# A channel's rule for who may join it: (principal, common_db, tenant_db, tenant_id) -> allowed.
Authorize = Callable[[object, Session, Session, str], bool]


def _verified_claims(token: str) -> Optional[tuple[dict, str]]:
    """A token's claims - signature and expiry verified - with its OWN `tenant_id` claim (never a
    header or a client-supplied value on the connection URL), or None. No database read, so it runs
    on the event loop and an expired token never takes a sign-in slot."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    tenant_id = payload.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return None
    return payload, tenant_id.strip()


def _authenticate(payload: dict, tenant_id: str, authorize: Authorize) -> Optional[SocketIdentity]:
    """Lightweight counterpart to `get_current_admin` for the WS handshake - HTTPBearer/Depends
    doesn't apply here, and neither browsers nor React Native's WebSocket can set a custom
    Authorization header, so the token arrives in the connection's first message (see
    `_open_authenticated`) - never in the URL, where proxies would log it.

    Resolves the account from the trusted database (`dependencies.auth.resolve_principal` - the
    same checks the REST dependencies make: an admin_access grant for an admin-table account, the
    trainer role for an agency account, a token that hasn't been revoked), then applies the
    channel's `authorize` rule. None when either refuses - every refusal denies, never silently
    proceeds with a partial identity. A failure on the server's side (a database error, the
    tenant's database unreachable) raises instead, so it isn't reported as a refusal.

    Blocking - runs on `_handshake_pool`. Both sessions are closed before it returns, so their
    connections are back in the pool before the socket is told it's ready."""
    # Local import (matching training.timeline._resolve_performer_names /
    # training.listing._updated_by_names_for) - a WebSocket handshake isn't part of the FastAPI Depends graph, so
    # there's no get_common_db dependency to receive here; this is what test fixtures patch to
    # substitute a synthetic common DB the same way app.dependency_overrides does for requests.
    from app.database.common import CommonSessionLocal

    common_db = CommonSessionLocal()
    tenant_db = None
    try:
        try:
            tenant_db = tenant_manager.get_session(tenant_id, common_db)
        except HTTPException as exc:
            # A suspended or unknown tenant is a refusal; its database being unavailable is not.
            if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
                raise
            return None
        principal = resolve_principal(payload, tenant_id, common_db, tenant_db)
        if principal is None or not authorize(principal, common_db, tenant_db, tenant_id):
            return None
        return SocketIdentity(tenant_id, principal.username)
    finally:
        if tenant_db is not None:
            tenant_db.close()
        common_db.close()


# How long a connection opened without a URL token may take to send its auth message.
AUTH_TIMEOUT_SECONDS = 10


async def _first_message_token(websocket: WebSocket) -> Optional[str]:
    """The token from the connection's first message, `{"type": "auth", "token": "..."}`, or None
    (anything else, malformed JSON, a disconnect, or nothing within AUTH_TIMEOUT_SECONDS)."""
    try:
        message = json.loads(await asyncio.wait_for(websocket.receive_text(), AUTH_TIMEOUT_SECONDS))
    except (asyncio.TimeoutError, WebSocketDisconnect, ValueError, KeyError, RuntimeError):
        return None
    if isinstance(message, dict) and message.get("type") == "auth" and isinstance(message.get("token"), str):
        return message["token"] or None
    return None


async def _open_authenticated(websocket: WebSocket, authorize: Authorize) -> Optional[SocketIdentity]:
    """Authenticates and authorizes a connection; returns who it belongs to, or None after closing
    it - with 1008 when the sign-in is refused, 1011 when the check itself failed.

    The connection is accepted, the first message must carry the token, and only then is anything
    joined (the server confirms with `{"type": "ready"}`). A token in the URL is ignored - URLs end
    up in proxy access logs, and every app build sends it in the first message."""
    await websocket.accept()
    token = await _first_message_token(websocket)
    claims = _verified_claims(token) if token else None
    if claims is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    payload, tenant_id = claims
    # The caller's context goes along to the worker thread, as asyncio.to_thread would carry it.
    context = contextvars.copy_context()
    try:
        identity = await asyncio.get_running_loop().run_in_executor(
            _handshake_pool, context.run, _authenticate, payload, tenant_id, authorize
        )
    except Exception:
        # WebSocket log lines carry no tenant tag (core/log_context.py), so the message names it.
        logger.exception("WebSocket sign-in check failed for tenant '%s'", tenant_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None
    if identity is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    await websocket.send_json({"type": "ready"})
    return identity


def _authorize_room(principal, common_db, tenant_db, tenant_id: str, conference_uid: str) -> bool:
    """Same rule as the REST endpoints, not a separate one: an admin-table account or a trainer
    via `conference_access.find_authorized_conference` (the exact gate `training.common.owned_conference`
    applies to start/operate a session - admin grant by scope, active trainer by assignment); a
    trainee via the same `attendance_repository.get_for_conference_and_trainee` row every
    admin write endpoint already uses to confirm a trainee belongs to a session. The conference
    is looked up ONLY in the caller's own verified tenant's database - never a client-supplied
    tenant, and a UID that doesn't exist there denies exactly like one that exists but is out of
    scope, so neither response distinguishes "wrong tenant" from "not in scope"."""
    if isinstance(principal, (Admin, AgencyTeam)):
        return conference_access.find_authorized_conference(tenant_db, principal, conference_uid, common_db, tenant_id) is not None
    if isinstance(principal, Trainee):
        return attendance_repository.get_for_conference_and_trainee(tenant_db, conference_uid, principal.traineeUid) is not None
    return False


@router.websocket("/ws/admin")
async def admin_events(websocket: WebSocket):
    # This channel is for the admin panel / trainer app only.
    identity = await _open_authenticated(websocket, lambda principal, *_: not isinstance(principal, Trainee))
    if identity is None:
        return
    await manager.connect(websocket, identity.tenant_id, identity.username)
    try:
        while True:
            # Nothing meaningful expected from the client - this just
            # blocks until the socket closes so we can clean up below.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, identity.tenant_id, identity.username)


@router.websocket("/ws/live/{conference_uid}")
async def live_quiz_events(websocket: WebSocket, conference_uid: str):
    """Per-conference Live Quiz room. Both the trainer's Session Dashboard and
    every trainee's Live Quiz screen connect here while the module is running;
    each `{"type": "live_quiz"}` nudge tells them to refetch their REST view.
    Room membership itself is authorized before joining - see `_authorize_room`."""
    identity = await _open_authenticated(
        websocket,
        lambda principal, common_db, tenant_db, tenant_id: _authorize_room(principal, common_db, tenant_db, tenant_id, conference_uid),
    )
    if identity is None:
        return
    await manager.join_room(websocket, identity.tenant_id, conference_uid)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.leave_room(websocket, identity.tenant_id, conference_uid)
