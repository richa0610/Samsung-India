from sqlalchemy.orm import Session

from app.core.exceptions import unauthorized
from app.core.media import resolve_trainer_avatar
from app.core.security import create_access_token, verify_password
from app.repositories import admin_repository
from app.schemas.admin import AdminAuthSession, AdminLoginRequest, AdminOut
from app.services.activity_log_service import log_activity


def login(
    common_db: Session,
    db: Session,
    payload: AdminLoginRequest,
    tenant_id: str,
    ip_address: str | None = None,
) -> AdminAuthSession:
    """`Admin` (superadmin/internal accounts) lives in the shared Common
    Database; `AgencyTeam` (partner-agency trainers) lives in the caller's
    own tenant database - see the DB-per-tenant split in app/database/."""
    admin = admin_repository.get_admin_by_username(common_db, payload.username)
    if admin and admin.password and verify_password(payload.password, admin.password):
        token = create_access_token(subject=f"admin:{admin.username}", tenant_id=tenant_id, role=admin.role)
        # `logsmaster` is a per-tenant table (see app/models/logs_master.py) -
        # write via `db` (this tenant), never `common_db`, even though the
        # account itself was found in the Common DB.
        log_activity(db, action="LOGIN", username=admin.username, role=admin.role, ip_address=ip_address)
        return AdminAuthSession(
            access_token=token,
            admin=AdminOut(
                username=admin.username,
                name=admin.name,
                role=admin.role,
                company=admin.company,
                tenant_id=tenant_id,
                profilePicture=resolve_trainer_avatar(admin.profilePhoto, admin.gender),
            ),
        )

    # Real trainers live in `agencyteam`, not `admin` - fall back to it so
    # they can sign in the same way once they're not seeded into `admin`.
    # The login field doubles as "Company ID / Phone No", so match either
    # `username` (phone) or `offerId` (employee ID).
    agent = admin_repository.get_agency_by_username_or_offer_id(db, payload.username)
    if agent and agent.password and verify_password(payload.password, agent.password):
        token = create_access_token(
            subject=f"agencyteam:{agent.username}", tenant_id=tenant_id, role=agent.role or "trainer"
        )
        log_activity(db, action="LOGIN", username=agent.username, role=agent.role or "trainer", ip_address=ip_address)
        return AdminAuthSession(
            access_token=token,
            admin=AdminOut(
                username=agent.username,
                name=agent.name or agent.username,
                role=agent.role or "trainer",
                offerId=agent.offerId,
                company=agent.company,
                tenant_id=tenant_id,
                profilePicture=resolve_trainer_avatar(agent.profilePhoto, agent.gender),
            ),
        )

    raise unauthorized("Invalid username or password")
