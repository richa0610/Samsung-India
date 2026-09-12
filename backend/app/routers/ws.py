from jose import JWTError, jwt

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings

router = APIRouter(tags=["ws"])


class ConnectionManager:
    """Tracks live WebSocket connections two ways:

    - `/ws/admin` connections keyed by trainer/admin username, so a write
      endpoint can push a small "something changed" event to just the trainer
      who owns it (`send_to`) or to everyone (`broadcast`).
    - per-conference *rooms* (`/ws/live/{conferenceUid}`) that both the trainer
      and every joined trainee of a live session sit in, so a Live Quiz action
      can nudge the whole room to refetch (`send_to_room`). The event payload is
      deliberately thin (`{"type": "live_quiz"}`) - all real state travels over
      REST, same philosophy as src/services/liveEvents.ts.
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self._connections.setdefault(username, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, username: str) -> None:
        sockets = self._connections.get(username)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(username, None)

    async def send_to(self, username: str | None, event: dict) -> None:
        if not username:
            return
        for websocket in list(self._connections.get(username, ())):
            try:
                await websocket.send_json(event)
            except Exception:
                self.disconnect(websocket, username)

    async def broadcast(self, event: dict) -> None:
        for username, sockets in list(self._connections.items()):
            for websocket in list(sockets):
                try:
                    await websocket.send_json(event)
                except Exception:
                    self.disconnect(websocket, username)

    # --- per-conference rooms -------------------------------------------------

    async def join_room(self, websocket: WebSocket, room: str) -> None:
        await websocket.accept()
        self._rooms.setdefault(room, set()).add(websocket)

    def leave_room(self, websocket: WebSocket, room: str) -> None:
        sockets = self._rooms.get(room)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._rooms.pop(room, None)

    async def send_to_room(self, room: str | None, event: dict) -> None:
        if not room:
            return
        for websocket in list(self._rooms.get(room, ())):
            try:
                await websocket.send_json(event)
            except Exception:
                self.leave_room(websocket, room)


manager = ConnectionManager()


def _decode_subject(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    return payload.get("sub") or None


def _resolve_username(token: str) -> str | None:
    """Lightweight counterpart to `get_current_admin` for the WS handshake -
    HTTPBearer/Depends doesn't apply here, and neither browsers nor React
    Native's WebSocket can set a custom Authorization header, so the token
    travels as a query param instead (visible in access logs - acceptable
    for this app's local/dev threat model, not for a public deployment)."""
    subject = _decode_subject(token) or ""
    if subject.startswith("admin:"):
        return subject.removeprefix("admin:")
    if subject.startswith("agencyteam:"):
        return subject.removeprefix("agencyteam:")
    return None


def _is_valid_token(token: str) -> bool:
    """Any decodable admin / agencyteam / trainee (bare phone `sub`) token may
    join a Live Quiz room - it only receives thin "refetch" nudges, so no
    per-conference membership check is needed here."""
    subject = _decode_subject(token)
    return bool(subject)


@router.websocket("/ws/admin")
async def admin_events(websocket: WebSocket, token: str = ""):
    username = _resolve_username(token)
    if not username:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, username)
    try:
        while True:
            # Nothing meaningful expected from the client - this just
            # blocks until the socket closes so we can clean up below.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, username)


@router.websocket("/ws/live/{conference_uid}")
async def live_quiz_events(websocket: WebSocket, conference_uid: str, token: str = ""):
    """Per-conference Live Quiz room. Both the trainer's Session Dashboard and
    every trainee's Live Quiz screen connect here while the module is running;
    each `{"type": "live_quiz"}` nudge tells them to refetch their REST view."""
    if not _is_valid_token(token):
        await websocket.close(code=1008)
        return

    await manager.join_room(websocket, conference_uid)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.leave_room(websocket, conference_uid)
