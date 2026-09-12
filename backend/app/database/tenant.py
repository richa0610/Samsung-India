import logging
import threading
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.database.common import common_engine
from app.database.connection import build_connect_args
from app.models.common.tenant_registry import Tenant

logger = logging.getLogger("tenant_manager")


def _same_target(a: URL, b: URL) -> bool:
    """True when two connection URLs point at the exact same physical
    database (host, port, schema, user) - used to avoid opening a second
    connection pool to a server a pool is already open against."""
    return (a.host, a.port, a.database, a.username) == (b.host, b.port, b.database, b.username)


class TenantConnectionManager:
    """Manages isolated MySQL database connection pools for each tenant.
    Guarantees failure isolation: an outage on one tenant's database does not
    affect other tenants or the FastAPI application."""

    def __init__(self) -> None:
        self._engines: Dict[str, Engine] = {}
        self._sessionmakers: Dict[str, sessionmaker] = {}
        self._lock = threading.Lock()

    def _build_tenant_url(
        self, user: str, password: str, host: str, port: int, db_name: str
    ) -> URL:
        return URL.create(
            drivername="mysql+pymysql",
            username=user,
            password=password,
            host=host,
            port=port,
            database=db_name,
        )

    def register_engine(self, tenant_uid: str, engine: Engine) -> None:
        """Register or override an engine directly (useful for testing and setup)."""
        with self._lock:
            self._engines[tenant_uid] = engine
            self._sessionmakers[tenant_uid] = sessionmaker(
                autocommit=False, autoflush=False, bind=engine
            )

    def get_engine(
        self, tenant_uid: str, common_db: Optional[Session] = None
    ) -> Engine:
        """Resolves or lazily creates a dedicated connection pool Engine for the tenant."""
        if tenant_uid in self._engines:
            return self._engines[tenant_uid]

        with self._lock:
            if tenant_uid in self._engines:
                return self._engines[tenant_uid]

            tenant_record: Optional[Tenant] = None
            if common_db is not None:
                try:
                    tenant_record = (
                        common_db.query(Tenant)
                        .filter(Tenant.tenant_uid == tenant_uid)
                        .first()
                    )
                except SQLAlchemyError as exc:
                    logger.error("Failed to query tenant registry from Common DB: %s", exc)

            if tenant_record:
                if tenant_record.status.lower() != "active":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tenant account is suspended or inactive",
                    )
                db_url = self._build_tenant_url(
                    user=tenant_record.database_username,
                    password=tenant_record.database_password,
                    host=tenant_record.database_host,
                    port=tenant_record.database_port,
                    db_name=tenant_record.database_name,
                )
            elif tenant_uid == settings.DEFAULT_TENANT_ID:
                # Fallback for default tenant using environment configuration
                db_url = self._build_tenant_url(
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    db_name=settings.DB_NAME,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant '{tenant_uid}' not found",
                )

            try:
                # Reuse an already-open pool - Common DB's, or another
                # tenant's - when it points at the exact same physical
                # database, rather than opening a second independent pool to
                # the same server. Without this, a tenant whose credentials
                # happen to match Common DB's (the default tenant, until its
                # `tenants` row - if any - or COMMON_DB_* is set to somewhere
                # else) doubles the connection count against the database's
                # connection limit for no reason, which on a small managed
                # MySQL plan (e.g. Aiven's lower tiers) can exhaust it and
                # surface as "Tenant database is temporarily unavailable"
                # even though the database itself is perfectly healthy.
                if _same_target(db_url, common_engine.url):
                    engine = common_engine
                else:
                    engine = next(
                        (e for e in self._engines.values() if _same_target(db_url, e.url)),
                        None,
                    ) or create_engine(
                        db_url,
                        poolclass=QueuePool,
                        pool_size=settings.TENANT_POOL_SIZE,
                        max_overflow=settings.TENANT_MAX_OVERFLOW,
                        pool_timeout=settings.TENANT_POOL_TIMEOUT,
                        pool_recycle=settings.TENANT_POOL_RECYCLE,
                        pool_pre_ping=True,
                        connect_args=build_connect_args(),
                    )
                self._engines[tenant_uid] = engine
                self._sessionmakers[tenant_uid] = sessionmaker(
                    autocommit=False, autoflush=False, bind=engine
                )
                return engine
            except SQLAlchemyError as exc:
                logger.error("Failed to initialize engine for tenant '%s': %s", tenant_uid, exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Tenant database is temporarily unavailable",
                )

    def get_session(
        self, tenant_uid: str, common_db: Optional[Session] = None
    ) -> Session:
        """Returns a new Session bound to the tenant's isolated database connection pool."""
        self.get_engine(tenant_uid, common_db)
        maker = self._sessionmakers[tenant_uid]
        return maker()

    def ping_all(self) -> None:
        """Runs a trivial query against every tenant's pooled connection.
        Called periodically from a background loop (see main.py) purely to
        keep each pool's connection alive - Aiven (and the network path to
        it) closes idle connections well before pool_recycle's 280s would,
        so without this the *first* login after a few quiet minutes pays for
        a fresh TCP+TLS handshake to the remote DB inline, which is what
        made that one login take ~10s. Paying that cost here instead, off
        the request path, is the whole point."""
        for tenant_uid, engine in list(self._engines.items()):
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except SQLAlchemyError as exc:
                logger.warning("Keep-alive ping failed for tenant '%s': %s", tenant_uid, exc)

    def close_all(self) -> None:
        """Disposes all active tenant connection pools."""
        with self._lock:
            for tenant_uid, engine in self._engines.items():
                try:
                    engine.dispose()
                except Exception as exc:
                    logger.warning("Error disposing engine for tenant '%s': %s", tenant_uid, exc)
            self._engines.clear()
            self._sessionmakers.clear()


tenant_manager = TenantConnectionManager()
