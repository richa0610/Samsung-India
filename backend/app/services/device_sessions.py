"""Signed-in devices (user, 2026-10-19): a person in the central user registry may be signed in on
`user_registry.max_devices` devices at once (2 unless changed). Signing in on one more signs out the
device used longest ago; signing in again on the same device replaces its own session; Logout ends
only the device it's pressed on.

Each sign-in of a registry account starts a session (models/common/login_session.py) whose ID rides
in the token as `sid`; every request carrying one checks it is still live (`end_reason` of None), from
a 30-second cache. A token without a `sid` - issued before devices were tracked, or for an account not
yet in the registry - is checked as before, by its token version alone."""

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.ttl_cache import TTLCache
from app.models.agency_team import AgencyTeam
from app.models.common.login_session import LoginSession
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.repositories import user_registry_repository as registry
from app.utils import user_agent

logger = logging.getLogger("device_sessions")

LOGOUT, REPLACED, SIGNED_IN_AGAIN, EXPIRED, UNKNOWN = "logout", "replaced", "signed_in_again", "expired", "unknown"
DEFAULT_MAX_DEVICES = 2
# How often a live session's `last_seen_at` is brought up to date - what "used longest ago" goes by.
SEEN_EVERY = timedelta(minutes=5)
# sid -> None (live) or why it ended. A device signed out by this server stops working at once (the
# entry is dropped); one signed out by another worker process within the cache's 30 seconds.
_status = TTLCache(ttl_seconds=30, max_entries=50_000)


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


def entry_for(common_db: Session, record: Trainee | AgencyTeam) -> Optional[UserRegistry]:
    """The active registry entry of a company record, or None (not registered yet: no device limit)."""
    user_uid = record.traineeUid if isinstance(record, Trainee) else record.agencyTeamUid
    entry = registry.get_by_uid(common_db, user_uid)
    return entry if entry is not None and entry.status == "active" else None


def _end(session: LoginSession, reason: str, now: datetime) -> None:
    session.ended_at, session.end_reason = now, reason
    _status.discard(session.session_id)


def begin(common_db: Session, record: Trainee | AgencyTeam, tenant_uid: str, device: Optional[Device]) -> Optional[str]:
    """The session ID for a sign-in's token, or None for an account the registry doesn't hold (yet) in
    this company - its token is checked by its version alone, as before devices were tracked."""
    entry = entry_for(common_db, record)
    if entry is None or entry.tenant_uid != tenant_uid:
        return None
    return start(common_db, entry, device or Device())


def start(common_db: Session, entry: UserRegistry, device: Device) -> str:
    """Starts a session for `entry` on `device`, lasting as long as a token, and returns its ID. Makes
    room first: the same device's own session ends; then, while the person is at their limit, the live
    session used longest ago. The registry row is locked meanwhile, so two sign-ins of one person at
    the same moment take turns."""
    now = _now()
    common_db.query(UserRegistry).filter(UserRegistry.id == entry.id).with_for_update().one()
    live = (
        common_db.query(LoginSession)
        .filter(LoginSession.registry_id == entry.id, LoginSession.ended_at.is_(None), LoginSession.expires_at > now)
        .order_by(LoginSession.last_seen_at)
        .all()
    )
    if device.device_id:
        for session in [s for s in live if s.device_id == device.device_id]:
            _end(session, SIGNED_IN_AGAIN, now)
            live.remove(session)
    limit = max(1, entry.max_devices or DEFAULT_MAX_DEVICES)
    while len(live) >= limit:
        _end(live.pop(0), REPLACED, now)

    session_id = secrets.token_urlsafe(24)
    common_db.add(LoginSession(
        session_id=session_id, registry_id=entry.id, tenant_uid=entry.tenant_uid, device_id=device.device_id,
        device_name=device.device_name, created_at=now, last_seen_at=now,
        expires_at=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    ))
    common_db.commit()
    return session_id


def why_ended(common_db: Session, session_id: str) -> Optional[str]:
    """None while the session is live, else why it isn't (LOGOUT, REPLACED, ...). Keeps `last_seen_at`
    up to date every SEEN_EVERY. A Common DB that can't be read counts as live - logged: the token's
    signature, expiry and version still hold, and one database blip mustn't sign everyone out."""
    cached = _status.get(session_id)
    if cached is not None:
        return cached or None
    try:
        session = common_db.query(LoginSession).filter(LoginSession.session_id == session_id).first()
    except SQLAlchemyError:
        common_db.rollback()
        logger.exception("Couldn't check session - let through")
        return None
    now = _now()
    if session is None:
        reason = UNKNOWN
    elif session.ended_at is not None:
        reason = session.end_reason or LOGOUT
    elif session.expires_at <= now:
        reason = EXPIRED
    else:
        reason = None
        if session.last_seen_at <= now - SEEN_EVERY:
            try:
                common_db.execute(update(LoginSession).where(LoginSession.id == session.id).values(last_seen_at=now))
                common_db.commit()
            except SQLAlchemyError:
                common_db.rollback()
                logger.exception("Couldn't note session %s as seen", session.id)
    _status.set(session_id, reason or "")
    return reason


def end(common_db: Session, session_id: str, reason: str = LOGOUT) -> None:
    """Ends one session - Logout on that device."""
    session = common_db.query(LoginSession).filter(LoginSession.session_id == session_id).first()
    if session is not None and session.ended_at is None:
        _end(session, reason, _now())
        common_db.commit()
    _status.discard(session_id)
