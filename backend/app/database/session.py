import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import invalid_session, unauthorized
from app.database.common import get_common_db
from app.database.tenant import tenant_manager

logger = logging.getLogger("tenant_session")

_BEARER_PREFIX = "bearer "


def bearer_token(request: Request) -> str | None:
    """The token of an `Authorization: Bearer <token>` header (scheme matched in any case), or None
    without one. An empty token is returned as "" - it was presented, and must fail verification."""
    auth_header = request.headers.get("Authorization")  # Starlette header lookups ignore case
    if auth_header and auth_header.lower().startswith(_BEARER_PREFIX):
        return auth_header[len(_BEARER_PREFIX):].strip()
    return None


COMPANY_REQUIRED = "Company code is required"


def _requested_tenant(request: Request) -> tuple[Optional[str], bool]:
    """The tenant a request names, and whether a client named it (rather than a verified token):
    1. Authenticated user: the cryptographically verified JWT 'tenant_id' claim.
    2. Before sign-in (login, registration, QR join): the company code the app sends as the
       'X-Tenant-ID' header (Starlette header lookups ignore case), or '?tenant_id='.
    None when neither names one - there is no default company (user, 2026-10-18).

    Reads the Authorization header directly off `request` rather than taking a FastAPI-injected
    credentials parameter, so it works the same as a route dependency and as a plain call."""
    token = bearer_token(request)
    if token is not None:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            tenant_id = payload.get("tenant_id")
            if tenant_id:
                return str(tenant_id).strip(), False
        except JWTError:
            # Token invalid/expired; let the auth dependency raise 401
            pass

    sent = (request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id") or "").strip()
    return (sent, True) if sent else (None, False)


def get_tenant_id_from_request(request: Request) -> str:
    """The tenant this request is served by. An ID a client sent is put in the registry's own
    spelling (tenant_manager.canonical_uid), so "SAMSUNG" and "samsung" are one tenant everywhere.
    A request that names no company is refused with a 401, before any tenant is touched: a token
    that didn't verify gets the usual invalid-session answer (its session is over); no token at all
    gets COMPANY_REQUIRED - so an anonymous call to a signed-in route is a 401 as ever, and a
    sign-in without a company code says what is missing.
    May read the registry: call it from a worker thread (any regular endpoint or dependency), never
    on the event loop - see `tenant_slot_key`."""
    tenant_id, client_named = _requested_tenant(request)
    if tenant_id is None:
        raise invalid_session() if bearer_token(request) is not None else unauthorized(COMPANY_REQUIRED)
    return tenant_manager.canonical_uid(tenant_id) if client_named else tenant_id


def tenant_slot_key(request: Request) -> str:
    """The same tenant as `get_tenant_id_from_request`, as a key that needs no database - for code
    on the event loop (the per-tenant concurrency limit). Lower-cased, so one tenant's spellings
    share one key. Never refuses: a request naming no company shares the "" key - the routes that
    need no company (company lookup, place names) and requests its endpoint will refuse."""
    tenant_id, _ = _requested_tenant(request)
    return (tenant_id or "").lower()


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
    token = bearer_token(request)
    if token is not None:
        try:
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            raise invalid_session()

    tenant_id = get_tenant_id_from_request(request)
    session = tenant_manager.get_session(tenant_id, common_db)
    try:
        yield session
    except OperationalError:
        logger.exception("Database connectivity error on tenant '%s'", tenant_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant database is temporarily unavailable",
        )
    except SQLAlchemyError:
        logger.exception("Database query error on tenant '%s'", tenant_id)
        raise
    finally:
        session.close()
