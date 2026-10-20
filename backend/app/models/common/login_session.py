from sqlalchemy import Column, DateTime, Index, Integer, String

from app.database.connection import CommonBase


class LoginSession(CommonBase):
    """One signed-in device of a person in the central user registry (user, 2026-10-19), in the shared
    Common Database. Its `session_id` rides in that sign-in's token (`sid`); the session is live while
    `ended_at` is empty and `expires_at` (the token's own expiry) is still ahead. A person may have
    `user_registry.max_devices` live at once - signing in on one more ends the one used longest ago
    (services/device_sessions). Times are UTC."""

    __tablename__ = "login_sessions"
    __table_args__ = (Index("ix_login_sessions_registry_live", "registry_id", "ended_at"),)

    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), nullable=False, unique=True)
    registry_id = Column(Integer, nullable=False)   # user_registry.id
    tenant_uid = Column(String(100), nullable=False)
    device_id = Column(String(100))   # the app's install ID, when it sends one
    device_name = Column(String(255))
    created_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    end_reason = Column(String(30))   # logout / replaced / signed_in_again
