"""Signed-in devices (user, 2026-10-19): a person in the central user registry may be signed in on
`user_registry.max_devices` devices at once (2 unless changed). Signing in on one more signs out the
device used longest ago; signing in again on the same device replaces its own session; Logout ends
only the device it's pressed on.

Each sign-in of a registry account starts a session, kept in its registry row's `devices` - a JSON
list, no table of its own (user, 2026-10-20) - whose ID rides in the token as `sid`. The ID starts
with the row's `id` ("42.<random>"), so every request carrying one reads just that row to check the
session is still live, from a 30-second cache. A token without a `sid` - issued before devices were
tracked, or for an account not yet in the registry - is checked as before, by its token version alone.

Each item of `devices`: {"sid", "device" (the app's install ID, or null), "name", "seen" (last use),
"expires" (the token's own expiry)} - times UTC, as "YYYY-MM-DDTHH:MM:SS" so they compare as text - and
"ended" (logout / replaced / signed_in_again) once it is signed out. An ended session stays listed a
while so its device is told why; expired ones are dropped whenever the list is written."""

import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional, TypeVar

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.ttl_cache import TTLCache
from app.models.agency_team import AgencyTeam
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.repositories import user_registry_repository as registry
from app.utils import user_agent

logger = logging.getLogger("device_sessions")

LOGOUT, REPLACED, SIGNED_IN_AGAIN, EXPIRED, UNKNOWN = "logout", "replaced", "signed_in_again", "expired", "unknown"
DEFAULT_MAX_DEVICES = 2
# How often a live session's "seen" is brought up to date - what "used longest ago" goes by.
SEEN_EVERY = timedelta(minutes=5)
# Signed-out sessions kept listed (the newest), so the row stays small.
MAX_ENDED = 10
# sid -> None (live) or why it ended. A device signed out by this server stops working at once (the
# entry is dropped); one signed out by another worker process within the cache's 30 seconds.
_status = TTLCache(ttl_seconds=30, max_entries=50_000)

T = TypeVar("T")


@dataclass(frozen=True)
class Device:
    """What a sign-in says about the device: the app's install ID (an older app sends none - each of
    its sign-ins then counts as a new device) and a name to show."""

    device_id: Optional[str] = None
    device_name: Optional[str] = None

    @classmethod
    def of(cls, device_id: Optional[str], device_name: Optional[str], agent: Optional[str]) -> "Device":
        if not device_name:
            browser, system = user_agent.describe(agent)
            device_name = f"{system} ({browser})"
        return cls((device_id or "").strip() or None, device_name[:255])


def _now() -> datetime:
    return datetime.utcnow()


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S")


def _entry_id(session_id: Optional[str]) -> Optional[int]:
    """The registry row a session ID belongs to, or None for one that isn't this format."""
    head, dot, _ = (session_id or "").partition(".")
    return int(head) if dot and head.isdigit() else None


def _parse(devices: Optional[str], entry_id: int) -> list[dict]:
    try:
        parsed = json.loads(devices or "[]")
    except ValueError:
        logger.warning("Registry row %s had unreadable devices - started afresh", entry_id)
        return []
    return [item for item in parsed if isinstance(item, dict) and item.get("sid")] if isinstance(parsed, list) else []


def _tidy(devices: list[dict], now: datetime) -> list[dict]:
    """Without expired sessions, and without all but the newest MAX_ENDED signed-out ones."""
    stamp = _stamp(now)
    kept = [item for item in devices if str(item.get("expires") or "") > stamp]
    ended = [item for item in kept if item.get("ended")]
    dropped = {id(item) for item in ended[: max(0, len(ended) - MAX_ENDED)]}
    return [item for item in kept if id(item) not in dropped]


def _rewrite(common_db: Session, entry_id: int, change: Callable[[list[dict], int, datetime], T]) -> Optional[T]:
    """Runs `change(devices, max_devices, now)` on a registry row's devices with the row locked - two
    sign-ins of one person at the same moment take turns - and saves the list it leaves. Returns what
    `change` returns; None for a row that's gone."""
    row = common_db.execute(
        select(UserRegistry.max_devices, UserRegistry.devices).where(UserRegistry.id == entry_id).with_for_update()
    ).first()
    if row is None:
        return None
    now = _now()
    devices = _tidy(_parse(row.devices, entry_id), now)
    result = change(devices, row.max_devices, now)
    devices = _tidy(devices, now)
    common_db.execute(
        update(UserRegistry).where(UserRegistry.id == entry_id).values(devices=json.dumps(devices) if devices else None)
    )
    common_db.commit()
    for item in devices:
        if item.get("ended"):
            _status.discard(item["sid"])   # a device signed out here stops working at once
    return result


def entry_for(common_db: Session, record: Trainee | AgencyTeam) -> Optional[UserRegistry]:
    """The active registry entry of a company record, or None (not registered yet: no device limit)."""
    user_uid = record.traineeUid if isinstance(record, Trainee) else record.agencyTeamUid
    entry = registry.get_by_uid(common_db, user_uid)
    return entry if entry is not None and entry.status == "active" else None


def begin(common_db: Session, record: Trainee | AgencyTeam, tenant_uid: str, device: Optional[Device]) -> Optional[str]:
    """The session ID for a sign-in's token, or None for an account the registry doesn't hold (yet) in
    this company - its token is checked by its version alone, as before devices were tracked."""
    entry = entry_for(common_db, record)
    if entry is None or entry.tenant_uid != tenant_uid:
        return None
    return start(common_db, entry, device or Device())


def start(common_db: Session, entry: UserRegistry, device: Device) -> Optional[str]:
    """Starts a session for `entry` on `device`, lasting as long as a token, and returns its ID. Makes
    room first: the same device's own session ends; then, while the person is at their limit, the live
    session used longest ago."""

    def sign_in(devices: list[dict], max_devices: int, now: datetime) -> str:
        live = sorted((item for item in devices if not item.get("ended")), key=lambda item: str(item.get("seen") or ""))
        if device.device_id:
            for item in [item for item in live if item.get("device") == device.device_id]:
                item["ended"] = SIGNED_IN_AGAIN
                live.remove(item)
        limit = max(1, max_devices or DEFAULT_MAX_DEVICES)
        while len(live) >= limit:
            live.pop(0)["ended"] = REPLACED
        session_id = f"{entry.id}.{secrets.token_urlsafe(24)}"
        devices.append({
            "sid": session_id, "device": device.device_id, "name": device.device_name, "seen": _stamp(now),
            "expires": _stamp(now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        })
        return session_id

    return _rewrite(common_db, entry.id, sign_in)


def _seen(common_db: Session, entry_id: int, session_id: str) -> None:
    def note(devices: list[dict], _max_devices: int, now: datetime) -> None:
        for item in devices:
            if item["sid"] == session_id and not item.get("ended"):
                item["seen"] = _stamp(now)

    try:
        _rewrite(common_db, entry_id, note)
    except SQLAlchemyError:
        common_db.rollback()
        logger.exception("Couldn't note a session of registry row %s as seen", entry_id)


def why_ended(common_db: Session, session_id: str) -> Optional[str]:
    """None while the session is live, else why it isn't (LOGOUT, REPLACED, ...). Keeps its "seen" up
    to date every SEEN_EVERY. A Common DB that can't be read counts as live - logged: the token's
    signature, expiry and version still hold, and one database blip mustn't sign everyone out."""
    cached = _status.get(session_id)
    if cached is not None:
        return cached or None
    entry_id = _entry_id(session_id)
    session = None
    if entry_id is not None:
        try:
            devices = common_db.execute(select(UserRegistry.devices).where(UserRegistry.id == entry_id)).scalar()
        except SQLAlchemyError:
            common_db.rollback()
            logger.exception("Couldn't check session - let through")
            return None
        session = next((item for item in _parse(devices, entry_id) if item["sid"] == session_id), None)
    now = _now()
    if session is None:
        reason = UNKNOWN
    elif session.get("ended"):
        reason = session["ended"]
    elif str(session.get("expires") or "") <= _stamp(now):
        reason = EXPIRED
    else:
        reason = None
        if str(session.get("seen") or "") <= _stamp(now - SEEN_EVERY):
            _seen(common_db, entry_id, session_id)
    _status.set(session_id, reason or "")
    return reason


def end(common_db: Session, session_id: str, reason: str = LOGOUT) -> None:
    """Ends one session - Logout on that device."""

    def sign_out(devices: list[dict], _max_devices: int, _now: datetime) -> None:
        for item in devices:
            if item["sid"] == session_id and not item.get("ended"):
                item["ended"] = reason

    entry_id = _entry_id(session_id)
    if entry_id is not None:
        _rewrite(common_db, entry_id, sign_out)
    _status.discard(session_id)
