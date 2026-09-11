import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.config import settings
from app.core.media import MEDIA_ROOT
from app.database.common import common_engine
from app.database.connection import CommonBase, TenantBase
from app.database.schema_sync import sync_missing_columns
from app.database.tenant import tenant_manager

# Import all models
from app.models import *
from app.routers.admin import router as admin_router
from app.routers.assessment import router as assessment_router
from app.routers.attendance import router as attendance_router
from app.routers.catalog import router as catalog_router
from app.routers.media import router as media_router
from app.routers.proctoring import router as proctoring_router
from app.routers.session import router as session_router
from app.routers.trainee import router as trainee_router
from app.routers.trainer import router as trainer_router
from app.routers.training import router as training_router
from app.routers.ws import router as ws_router

logger = logging.getLogger("main")

# 1. Initialize Common DB schema (admin, system_modules, tenants, etc.)
try:
    CommonBase.metadata.create_all(bind=common_engine)
    # create_all() only creates missing TABLES - a column added to a model
    # after its table already exists elsewhere (e.g. Tenant.
    # live_proctoring_enabled, added after `tenants` already existed on a
    # live deployment) never appears there on its own. This stack has no
    # migration framework, so this best-effort additive sync is it.
    sync_missing_columns(common_engine, CommonBase)
except Exception as e:
    logger.warning("Could not automatically create Common DB tables on startup: %s", e)

# 2. Initialize default tenant schema
try:
    default_engine = tenant_manager.get_engine(settings.DEFAULT_TENANT_ID)
    TenantBase.metadata.create_all(bind=default_engine)
    sync_missing_columns(default_engine, TenantBase)
except Exception as e:
    logger.warning("Could not automatically create default tenant tables on startup: %s", e)

app = FastAPI(
    title="Samsung India API (Multi-Tenant)",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# Global error handlers - production policy: an HTTPException (raised
# throughout the routers/services with a curated `detail`) always renders as
# written, since it's registered for that exact class; everything below is a
# safety net for whatever ISN'T one of those, so no raw exception text,
# SQL, stack trace, or file path a caller could use to fingerprint the stack
# ever reaches the response - full detail only ever goes to the server log.

# Database connection/availability failures (can't reach the tenant's MySQL
# at all) across every tenant.
@app.exception_handler(OperationalError)
async def db_operational_exception_handler(request: Request, exc: OperationalError):
    logger.error("Database connection failure on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Tenant database is temporarily unavailable"},
    )


# Any other DB-level failure (bad query, a constraint violation, a schema
# mismatch, etc.) - the database was reachable, it just rejected the query.
# More specific than the catch-all below so it logs with DB context, but the
# client-facing message is the same.
@app.exception_handler(SQLAlchemyError)
async def db_query_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Unhandled database error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please try again."},
    )


# Last-resort catch-all: any other unhandled exception (a bug, not a DB
# issue). FastAPI's own handlers for HTTPException and request-validation
# errors are registered for those specific classes and always take priority
# over this one, so existing 400/401/403/404/409/422/503 responses (and
# their exact messages) are completely unaffected by this handler existing.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please try again."},
    )


@app.on_event("shutdown")
def on_shutdown():
    tenant_manager.close_all()


MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Origins allowed to call this API from a browser (native app requests are
# unaffected - see ALLOWED_ORIGINS in core/config.py). Configure via the
# ALLOWED_ORIGINS env var; defaults to common local Expo web dev ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trainee_router)
app.include_router(session_router)
app.include_router(attendance_router)
app.include_router(assessment_router)
app.include_router(proctoring_router)
app.include_router(admin_router)
app.include_router(trainer_router)
app.include_router(catalog_router)
app.include_router(training_router)
app.include_router(ws_router)
app.include_router(media_router)


@app.get("/")
def root():
    return {
        "status": "success",
        "message": "Samsung India Backend Running 🚀",
    }