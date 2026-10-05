from typing import NamedTuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import is_token_current
from app.dependencies.database import get_common_db, get_db
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.repositories import admin_repository, trainee_repository
from app.services.access_service import resolve_scope

bearer_scheme = HTTPBearer()


def get_current_trainee(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Trainee:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired session",
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise unauthorized

    try:
        phone = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise unauthorized

    trainee = trainee_repository.get_by_phone(db, phone)
    if not trainee or not is_token_current(payload, trainee):
        raise unauthorized

    return trainee


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
) -> Admin | AgencyTeam:
    """`Admin` (superadmin/internal accounts) lives in the shared Common
    Database; `AgencyTeam` (partner-agency trainers) lives in the caller's
    own tenant database - see the DB-per-tenant split in app/database/."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired session",
    )
    not_authorized_for_tenant = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized for this tenant",
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise unauthorized

    subject = payload.get("sub") or ""

    if subject.startswith("admin:"):
        admin = admin_repository.get_admin_by_username(common_db, subject.removeprefix("admin:"))
        if not admin or not is_token_current(payload, admin):
            raise unauthorized
        # The token's own tenant claim, not anything a header on this request could carry - see
        # get_tenant_id_from_request, which already prefers this same verified claim once a
        # token decodes. Re-checked on every request (not just at login) via the same
        # admin_access grant everything else in the admin panel already goes through, so a
        # grant revoked after the token was issued stops working immediately, and a token
        # minted for one tenant can never be reused against another.
        token_tenant = payload.get("tenant_id")
        if not isinstance(token_tenant, str) or not token_tenant.strip():
            raise unauthorized
        if not resolve_scope(common_db, admin, token_tenant).allowed:
            raise not_authorized_for_tenant
        return admin

    if subject.startswith("agencyteam:"):
        agent = admin_repository.get_agency_by_username(db, subject.removeprefix("agencyteam:"))
        if not agent or not is_token_current(payload, agent):
            raise unauthorized
        # Only an agency account with the trainer role is a trainer (the approved rule - a NULL or
        # any other role is refused, and login no longer issues such tokens either). Re-checked on
        # every request, so a role changed after the token was issued stops working at once.
        if not resolve_scope(common_db, agent, payload.get("tenant_id")).is_trainer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This action requires an active trainer account")
        return agent

    raise unauthorized


class AuthenticatedAccount(NamedTuple):
    principal: Admin | AgencyTeam | Trainee
    tenant_id: str


def resolve_principal(
    payload: dict, tenant_id: str, common_db: Session, tenant_db: Session
) -> Admin | AgencyTeam | Trainee | None:
    """The verified account behind a decoded token, in the token's own tenant, or None: an
    admin-table account only with an admin_access grant for that tenant, an agency account only
    with the trainer role, a trainee by phone in that tenant's database - and in every case only
    while the token hasn't been revoked. Shared by the WebSocket handshake and
    `get_current_account`, so both trust exactly what the REST dependencies trust."""
    principal = _find_principal(payload.get("sub") or "", tenant_id, common_db, tenant_db)
    return principal if principal is not None and is_token_current(payload, principal) else None


def _find_principal(
    subject: str, tenant_id: str, common_db: Session, tenant_db: Session
) -> Admin | AgencyTeam | Trainee | None:
    if subject.startswith("admin:"):
        admin = admin_repository.get_admin_by_username(common_db, subject.removeprefix("admin:"))
        return admin if admin and resolve_scope(common_db, admin, tenant_id).allowed else None
    if subject.startswith("agencyteam:"):
        agent = admin_repository.get_agency_by_username(tenant_db, subject.removeprefix("agencyteam:"))
        return agent if agent and resolve_scope(common_db, agent, tenant_id).is_trainer else None
    try:
        phone = int(subject)
    except (TypeError, ValueError):
        return None
    return trainee_repository.get_by_phone(tenant_db, phone)


def get_current_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
) -> AuthenticatedAccount:
    """Any verified account - admin, trainer or trainee - with the tenant its token was issued
    for. For endpoints (like serving an uploaded file) that authorize per resource rather than
    per role; the resource check itself decides what this account may reach."""
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise unauthorized
    tenant_id = payload.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise unauthorized
    principal = resolve_principal(payload, tenant_id.strip(), common_db, db)
    if principal is None:
        raise unauthorized
    return AuthenticatedAccount(principal, tenant_id.strip())


def require_admin_role(admin: Admin | AgencyTeam = Depends(get_current_admin)) -> Admin:
    """Same auth as get_current_admin, but only lets role="admin" accounts
    through - for the admin-only review/assessment-builder endpoints that
    a trainer account must not be able to reach."""
    if getattr(admin, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires an admin account",
        )
    return admin
