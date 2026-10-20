from sqlalchemy import BigInteger, CheckConstraint, Column, Integer, String, Text, text

from app.database.connection import CommonBase

# pending  - reserved while a registration is saving the person's company record; signs in only once
#            that record is there (the sign-in then marks it active - services/sign_in_service)
# active   - may sign in (the company record is still checked on every sign-in)
# disabled - may not; `remarks` says why ("sync: ..." when the registry sync set it)
STATUSES = ("pending", "active", "disabled")


class UserRegistry(CommonBase):
    """Every trainee and trainer of every company, in the shared Common Database (user, 2026-10-19):
    which company a person belongs to, so they can sign in without a company code.

    Their details stay in their company's own database - the source of truth; this row is the index
    into it. `user_uid` is the company record's ID (trainee.traineeUid / agencyteam.agencyTeamUid) -
    whether they are a trainee or a trainer is read from which table that record is in (user,
    2026-10-20: no type column). `username` and `hoid` are stored trimmed and lower-cased
    (repositories/user_registry_repository.login_key). `user_uid`, `username` and `hoid` are each
    unique across every company; `phone` is not. `password_hash` is a copy of the company record's
    bcrypt hash, compared with it on sign-in. `devices` holds the person's signed-in devices, at most
    `max_devices` (services/device_sessions) - JSON, no table of its own (user, 2026-10-20)."""

    __tablename__ = "user_registry"
    __table_args__ = (CheckConstraint("status IN ('pending','active','disabled')", name="ck_user_registry_status"),)

    id = Column(Integer, primary_key=True)
    tenant_uid = Column(String(100), nullable=False, index=True)
    user_uid = Column(String(100), nullable=False, unique=True)
    username = Column(String(100), unique=True)
    hoid = Column(String(100), unique=True)
    phone = Column(BigInteger, index=True)
    password_hash = Column(String(255))
    max_devices = Column(Integer, nullable=False, server_default=text("2"))
    status = Column(String(20), nullable=False, server_default=text("'pending'"))
    remarks = Column(Text)
    devices = Column(Text)
