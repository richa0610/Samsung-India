from sqlalchemy.orm import Session

from app.core.exceptions import unauthorized
from app.core.security import create_access_token, verify_password
from app.repositories import admin_repository
from app.schemas.admin import AdminAuthSession, AdminLoginRequest, AdminOut


def login(common_db: Session, db: Session, payload: AdminLoginRequest, tenant_id: str) -> AdminAuthSession:
    """`Admin` (superadmin/internal accounts) lives in the shared Common
    Database; `AgencyTeam` (partner-agency trainers) lives in the caller's
    own tenant database - see the DB-per-tenant split in app/database/."""
    admin = admin_repository.get_admin_by_username(common_db, payload.username)
    if admin and admin.password and verify_password(payload.password, admin.password):
        token = create_access_token(subject=f"admin:{admin.username}", tenant_id=tenant_id, role=admin.role)
        return AdminAuthSession(
            access_token=token,
            admin=AdminOut(
                username=admin.username,
                name=admin.name,
                role=admin.role,
                company=admin.company,
                tenant_id=tenant_id,
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
        return AdminAuthSession(
            access_token=token,
            admin=AdminOut(
                username=agent.username,
                name=agent.name or agent.username,
                role=agent.role or "trainer",
                offerId=agent.offerId,
                company=agent.company,
                tenant_id=tenant_id,
            ),
        )

    raise unauthorized("Invalid username or password")
