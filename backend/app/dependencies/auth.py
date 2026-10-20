from typing import NamedTuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import forbidden, invalid_session, unauthorized
from app.core.security import is_token_current
from app.dependencies.database import get_common_db, get_db, get_tenant_id_from_request
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.repositories import admin_repository, trainee_repository
from app.services import device_sessions
from app.services.access_service import resolve_scope

bearer_scheme = HTTPBearer()


def _decode_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """The verified claims of a bearer token - signature and expiry checked - or the one generic
    invalid-session 401, whatever the reason it didn't verify."""
    try:
        return jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise invalid_session()


def get_token_claims(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """The verified claims of the request's token, for an endpoint that needs one - Logout, the token's
    device session. Use it beside the account dependency, which makes the real checks."""
    return _decode_token(credentials)


SIGNED_IN_ELSEWHERE = "You were signed out because this account signed in on another device."


def _ensure_live_session(payload: dict, common_db: Session) -> None:
    """A token naming a device session (services/device_sessions) is good only while that session is:
    a device signed out by a newer sign-in is told so, any other ended session gets the usual 401."""
    reason = device_sessions.why_ended(common_db, payload["sid"]) if payload.get("sid") else None
    if reason == device_sessions.REPLACED:
        raise unauthorized(SIGNED_IN_ELSEWHERE)
    if reason is not None:
        raise invalid_session()


def get_current_trainee(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
) -> Trainee:
    refused = invalid_session()
    payload = _decode_token(credentials)

    try:
        phone = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise refused

    trainee = trainee_repository.get_by_phone(db, phone)
    if not trainee or not is_token_current(payload, trainee):
        raise refused
    _ensure_live_session(payload, common_db)

    return trainee


ADMIN_SUBJECT_PREFIX = "admin:"
AGENCY_TEAM_SUBJECT_PREFIX = "agencyteam:"


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
) -> Admin | AgencyTeam:
    """`Admin` (superadmin/internal accounts) lives in the shared Common
    Database; `AgencyTeam` (partner-agency trainers) lives in the caller's
    own tenant database - see the DB-per-tenant split in app/database/."""
    payload = _decode_token(credentials)
    subject = payload.get("sub") or ""

    if subject.startswith(ADMIN_SUBJECT_PREFIX):
        return _authenticate_admin(payload, subject.removeprefix(ADMIN_SUBJECT_PREFIX), common_db)
    if subject.startswith(AGENCY_TEAM_SUBJECT_PREFIX):
        return _authenticate_trainer(payload, subject.removeprefix(AGENCY_TEAM_SUBJECT_PREFIX), db, common_db)
    raise invalid_session()


def _authenticate_admin(payload: dict, username: str, common_db: Session) -> Admin:
    admin = admin_repository.get_admin_by_username(common_db, username)
    if not admin or not is_token_current(payload, admin):
        raise invalid_session()
    # The token's own tenant claim, not anything a header on this request could carry - see
    # get_tenant_id_from_request, which already prefers this same verified claim once a
    # token decodes. Re-checked on every request (not just at login) via the same
    # admin_access grant everything else in the admin panel already goes through, so a
    # grant revoked after the token was issued stops working immediately, and a token
    # minted for one tenant can never be reused against another.
    token_tenant = payload.get("tenant_id")
    if not isinstance(token_tenant, str) or not token_tenant.strip():
        raise invalid_session()
    if not resolve_scope(common_db, admin, token_tenant).allowed:
        raise forbidden("Not authorized for this tenant")
    _ensure_live_session(payload, common_db)
    return admin


def _authenticate_trainer(payload: dict, username: str, tenant_db: Session, common_db: Session) -> AgencyTeam:
    agent = admin_repository.get_agency_by_username(tenant_db, username)
    if not agent or not is_token_current(payload, agent):
        raise invalid_session()
    # Only an agency account with the trainer role is a trainer (the approved rule - a NULL or
    # any other role is refused, and login no longer issues such tokens either). Re-checked on
    # every request, so a role changed after the token was issued stops working at once.
    if not resolve_scope(common_db, agent, payload.get("tenant_id")).is_trainer:
        raise forbidden("This action requires an active trainer account")
    _ensure_live_session(payload, common_db)
    return agent


class AuthenticatedAccount(NamedTuple):
    principal: Admin | AgencyTeam | Trainee
    tenant_id: str


def resolve_principal(
    payload: dict, tenant_id: str, common_db: Session, tenant_db: Session
) -> Admin | AgencyTeam | Trainee | None:
    """The verified account behind a decoded token, in the token's own tenant, or None: an
    admin-table account only with an admin_access grant for that tenant, an agency account only
    with the trainer role, a trainee by phone in that tenant's database - and in every case only
    while the token hasn't been revoked, nor its device session ended. Shared by the WebSocket
    handshake and `get_current_account`, so both trust exactly what the REST dependencies trust."""
    principal = _find_principal(payload.get("sub") or "", tenant_id, common_db, tenant_db)
    if principal is None or not is_token_current(payload, principal):
        return None
    if payload.get("sid") and device_sessions.why_ended(common_db, payload["sid"]) is not None:
        return None
    return principal


def _find_principal(
    subject: str, tenant_id: str, common_db: Session, tenant_db: Session
) -> Admin | AgencyTeam | Trainee | None:
    if subject.startswith(ADMIN_SUBJECT_PREFIX):
        admin = admin_repository.get_admin_by_username(common_db, subject.removeprefix(ADMIN_SUBJECT_PREFIX))
        return admin if admin and resolve_scope(common_db, admin, tenant_id).allowed else None
    if subject.startswith(AGENCY_TEAM_SUBJECT_PREFIX):
        agent = admin_repository.get_agency_by_username(tenant_db, subject.removeprefix(AGENCY_TEAM_SUBJECT_PREFIX))
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
    refused = invalid_session()
    payload = _decode_token(credentials)
    tenant_id = payload.get("tenant_id")
    if not isinstance(tenant_id, str) or not tenant_id.strip():
        raise refused
    principal = resolve_principal(payload, tenant_id.strip(), common_db, db)
    if principal is None:
        raise refused
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


def require_super_admin(
    request: Request,
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
) -> Admin:
    """require_admin_role, narrowed to an active Super Admin grant - re-resolved from admin_access on
    every request in the token's own tenant, never taken from a claim. For tenant-wide settings
    and maintenance reports that no other admin role may reach."""
    if not resolve_scope(common_db, admin, get_tenant_id_from_request(request)).is_super:
        raise forbidden("This action requires a Super Admin account")
    return admin
