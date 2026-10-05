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
    other tenants.

    Authenticate before resolving the tenant: if a bearer token was presented and doesn't
    verify, this refuses before ever calling `tenant_manager` - not after. Without this, an
    invalid token alongside a client-chosen `X-Tenant-ID` still reached `get_tenant_id_from_request`'s
    header fallback and made this function open (or attempt to open) a connection to whatever
    tenant the client named, before the real auth dependency (get_current_admin /
    get_current_trainee, both of which also depend on this) ever got to reject that same token
    with 401 - a probe: garbage credentials, then read which named tenants exist or are slow to
    answer from the response. This is only a cheap decode (no lookup, no claims used) - the real
    auth dependency still does its own full check right after; the point here is only sequencing,
    a tenant is never touched on a token that was never going to be accepted anyway."""
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        try:
            jwt.decode(auth_header[len("bearer "):].strip(), settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

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
