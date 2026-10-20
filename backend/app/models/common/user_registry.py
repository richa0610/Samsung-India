from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Integer, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import CommonBase

USER_TYPES = ("trainee", "trainer")
# pending  - reserved while a registration is saving the person's company record; never signs in
# active   - may sign in (the company record is still checked on every sign-in)
# disabled - may not; `remarks` says why ("sync: ..." when the registry sync set it)
STATUSES = ("pending", "active", "disabled")


class UserRegistry(CommonBase):
    """Every trainee and trainer of every company, in the shared Common Database (user, 2026-10-19):
    which company a person belongs to, so they can sign in without a company code.

    Their details stay in their company's own database - the source of truth; this row is the index
    into it. `user_uid` is the company record's ID (trainee.traineeUid / agencyteam.agencyTeamUid);
    `username` and `hoid` are stored trimmed and lower-cased (services/user_registry_service.login_key).
    `user_uid`, `username` and `hoid` are each unique across every company; `phone` is not.
    `password_hash` is a copy of the company record's bcrypt hash, compared with it on sign-in."""

    __tablename__ = "user_registry"
    __table_args__ = (
        CheckConstraint("user_type IN ('trainee','trainer')", name="ck_user_registry_user_type"),
        CheckConstraint("status IN ('pending','active','disabled')", name="ck_user_registry_status"),
    )

    id = Column(Integer, primary_key=True)
    tenant_uid = Column(String(100), nullable=False, index=True)
    user_type = Column(String(20), nullable=False)
    user_uid = Column(String(100), nullable=False, unique=True)
    username = Column(String(100), unique=True)
    hoid = Column(String(100), unique=True)
    phone = Column(BigInteger, index=True)
    password_hash = Column(String(255))
    max_devices = Column(Integer, nullable=False, server_default=text("2"))
    status = Column(String(20), nullable=False, server_default=text("'pending'"))
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
