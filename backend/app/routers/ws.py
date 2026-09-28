from jose import JWTError, jwt

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.database.tenant import tenant_manager
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.repositories import admin_repository, attendance_repository, conference_repository, trainee_repository
from app.services.access_service import resolve_scope

router = APIRouter(tags=["ws"])


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
        await websocket.accept()
        self._connections.setdefault((tenant_id, username), set()).add(websocket)

    def disconnect(self, websocket: WebSocket, tenant_id: str, username: str) -> None:
        key = (tenant_id, username)
        sockets = self._connections.get(key)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(key, None)

    async def send_to(self, tenant_id: str | None, username: str | None, event: dict) -> None:
        if not tenant_id or not username:
            return
        key = (tenant_id, username)
        for websocket in list(self._connections.get(key, ())):
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
        for (t, username), sockets in list(self._connections.items()):
            if t != tenant_id:
                continue
            for websocket in list(sockets):
                try:
                    await websocket.send_json(event)
                except Exception:
                    self.disconnect(websocket, tenant_id, username)

    # --- per-conference rooms -------------------------------------------------

    async def join_room(self, websocket: WebSocket, tenant_id: str, room: str) -> None:
        await websocket.accept()
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
        for websocket in list(self._rooms.get(key, ())):
            try:
                await websocket.send_json(event)
            except Exception:
                self.leave_room(websocket, tenant_id, room)


manager = ConnectionManager()


def _resolve_identity(token: str):
    """Lightweight counterpart to `get_current_admin` for the WS handshake - HTTPBearer/Depends
    doesn't apply here, and neither browsers nor React Native's WebSocket can set a custom
    Authorization header, so the token travels as a query param instead (visible in access logs
    - acceptable for this app's local/dev threat model, not for a public deployment).

    Decodes and verifies the token, reads its OWN `tenant_id` claim (never a header or a
    client-supplied value on the connection URL), resolves the account from the trusted
    database, and - for an admin-table account - checks the same admin_access grant
    `get_current_admin` does. Returns `None` on any failure (bad token, missing/malformed tenant
    claim, account not found, admin without a grant for that tenant, a DB error resolving the
    tenant) - every failure mode denies, never silently proceeds with a partial identity.

    Returns `(principal, tenant_id, common_db, tenant_db)` on success; the caller owns both
    sessions and must close them (a WebSocket isn't a request-scoped FastAPI dependency, so
    there's no `finally` this can do that job for)."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None

    tenant_id = payload.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return None
    tenant_id = tenant_id.strip()
    subject = payload.get("sub") or ""

    # Local import (matching training_service.py's own _resolve_performer_names /
    # _updated_by_names_for) - a WebSocket handshake isn't part of the FastAPI Depends graph, so
    # there's no get_common_db dependency to receive here; this is what test fixtures patch to
    # substitute a synthetic common DB the same way app.dependency_overrides does for requests.
    from app.database.common import CommonSessionLocal

    common_db = CommonSessionLocal()
    try:
        tenant_db = tenant_manager.get_session(tenant_id, common_db)
    except Exception:
        common_db.close()
        return None

    def deny():
        common_db.close()
        tenant_db.close()
        return None

    if subject.startswith("admin:"):
        admin = admin_repository.get_admin_by_username(common_db, subject.removeprefix("admin:"))
        if not admin:
            return deny()
        if not resolve_scope(common_db, admin, tenant_id).allowed:
            return deny()
        return admin, tenant_id, common_db, tenant_db

    if subject.startswith("agencyteam:"):
        agent = admin_repository.get_agency_by_username(tenant_db, subject.removeprefix("agencyteam:"))
        if not agent:
            return deny()
        return agent, tenant_id, common_db, tenant_db

    try:
        phone = int(subject)
    except (TypeError, ValueError):
        return deny()
    trainee = trainee_repository.get_by_phone(tenant_db, phone)
    if not trainee:
        return deny()
    return trainee, tenant_id, common_db, tenant_db


def _authorize_room(principal, common_db, tenant_db, tenant_id: str, conference_uid: str) -> bool:
    """Same rule as the REST endpoints, not a separate one: an admin-table account via
    `resolve_scope`/`allows_row` (access_service - the exact check `_get_owned_conference`
    already applies to start/operate a session); a trainer via the same ownership
    `conference_repository.get_owned_by_trainer` already gates start/end/modules with; a
    trainee via the same `attendance_repository.get_for_conference_and_trainee` row every
    admin write endpoint already uses to confirm a trainee belongs to a session. The conference
    is looked up ONLY in the caller's own verified tenant's database - never a client-supplied
    tenant, and a UID that doesn't exist there denies exactly like one that exists but is out of
    scope, so neither response distinguishes "wrong tenant" from "not in scope"."""
    conference = conference_repository.get_by_uid(tenant_db, conference_uid)
    if not conference:
        return False
    if isinstance(principal, Admin):
        return resolve_scope(common_db, principal, tenant_id).allows_row(conference.company, conference.zone, conference.region)
    if isinstance(principal, AgencyTeam):
        return conference_repository.get_owned_by_trainer(tenant_db, principal.username, conference_uid) is not None
    if isinstance(principal, Trainee):
        return attendance_repository.get_for_conference_and_trainee(tenant_db, conference_uid, principal.traineeUid) is not None
    return False


@router.websocket("/ws/admin")
async def admin_events(websocket: WebSocket, token: str = ""):
    identity = _resolve_identity(token)
    if identity is None:
        await websocket.close(code=1008)
        return
    principal, tenant_id, common_db, tenant_db = identity
    try:
        if isinstance(principal, Trainee):  # this channel is for the admin panel / trainer app only
            await websocket.close(code=1008)
            return
        username = principal.username

        await manager.connect(websocket, tenant_id, username)
        try:
            while True:
                # Nothing meaningful expected from the client - this just
                # blocks until the socket closes so we can clean up below.
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(websocket, tenant_id, username)
    finally:
        common_db.close()
        tenant_db.close()


@router.websocket("/ws/live/{conference_uid}")
async def live_quiz_events(websocket: WebSocket, conference_uid: str, token: str = ""):
    """Per-conference Live Quiz room. Both the trainer's Session Dashboard and
    every trainee's Live Quiz screen connect here while the module is running;
    each `{"type": "live_quiz"}` nudge tells them to refetch their REST view.
    Room membership itself is authorized before joining - see `_authorize_room`."""
    identity = _resolve_identity(token)
    if identity is None:
        await websocket.close(code=1008)
        return
    principal, tenant_id, common_db, tenant_db = identity
    try:
        if not _authorize_room(principal, common_db, tenant_db, tenant_id, conference_uid):
            await websocket.close(code=1008)
            return

        await manager.join_room(websocket, tenant_id, conference_uid)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            manager.leave_room(websocket, tenant_id, conference_uid)
    finally:
        common_db.close()
        tenant_db.close()
