import logging
from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.common import get_common_db
from app.database.tenant import tenant_manager

logger = logging.getLogger("tenant_session")


def get_tenant_id_from_request(request: Request) -> str:
    """Extracts tenant ID strictly server-side:
    1. Authenticated user: read cryptographically verified JWT 'tenant_id' claim.
    2. Unauthenticated calls (onboarding, login): read 'X-Tenant-ID' header or '?tenant_id='.
    3. Default fallback: settings.DEFAULT_TENANT_ID.

    Reads the Authorization header directly off `request` rather than
    taking a FastAPI-injected credentials parameter, so this works
    identically whether it's used as a route dependency (`Depends(...)`)
    or called as a plain function from inside a handler (both patterns are
    used across the routers)."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[len("bearer "):].strip()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            tenant_id = payload.get("tenant_id")
            if tenant_id:
                return str(tenant_id).strip()
        except JWTError:
            # Token invalid/expired; let the auth dependency raise 401
            pass

    header_tenant = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")
    if header_tenant:
        return header_tenant.strip()

    query_tenant = request.query_params.get("tenant_id")
    if query_tenant:
        return query_tenant.strip()

    return settings.DEFAULT_TENANT_ID


def get_db(
    request: Request,
    common_db: Session = Depends(get_common_db),
) -> Generator[Session, None, None]:
    """Provides a database Session bound strictly to the requester's tenant
    database. Guarantees failure isolation: if the tenant's MySQL server
    goes down, returns HTTP 503 without crashing the server or affecting
    other tenants."""
    tenant_id = get_tenant_id_from_request(request)
    session = tenant_manager.get_session(tenant_id, common_db)
    try:
        yield session
    except OperationalError as exc:
        logger.error("Database connectivity error on tenant '%s': %s", tenant_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant database is temporarily unavailable",
        )
    except SQLAlchemyError as exc:
        logger.error("Database query error on tenant '%s': %s", tenant_id, exc)
        raise
    finally:
        session.close()
