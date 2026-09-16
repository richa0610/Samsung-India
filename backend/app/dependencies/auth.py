from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies.database import get_common_db, get_db
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.repositories import admin_repository, trainee_repository

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
    if not trainee:
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
        if not admin:
            raise unauthorized
        return admin

    if subject.startswith("agencyteam:"):
        agent = admin_repository.get_agency_by_username(db, subject.removeprefix("agencyteam:"))
        if not agent:
            raise unauthorized
        return agent

    raise unauthorized


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Any decodable trainee / admin / agencyteam token - no DB lookup, no
    role check. For endpoints (like serving an uploaded media file) that only
    need "some logged-in user", not a specific one, mirroring the same
    decode-only trust level `routers/ws.py` already uses for its sockets."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return subject


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
