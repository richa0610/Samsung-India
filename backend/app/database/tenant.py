import logging
import threading
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.core.secret_box import SecretUnavailable, decrypt_secret
from app.core.ttl_cache import TTLCache
from app.database import common as common_database
from app.database.common import common_engine
from app.database.connection import SAFE_ENGINE_OPTIONS, TenantBase, build_connect_args
from app.database.schema_sync import sync_missing_columns, sync_missing_indexes
from app.models.common.tenant_registry import Tenant
from app.repositories import tenant_repository

logger = logging.getLogger("tenant_manager")

# The one key of TenantConnectionManager._uid_cache: the registry's IDs, by code_key.
_SPELLINGS = "spellings"


# A company row added without its database (services/tenant_setup) isn't served until it is set up.
NOT_SET_UP = "This company is still being set up. Please try again in a few minutes."


def _inactive_tenant_error() -> HTTPException:
    """The one refusal for a tenant whose registry status isn't "active" (suspended, inactive, ...)."""
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant account is suspended or inactive")


def _same_target(a: URL, b: URL) -> bool:
    """True when two connection URLs point at the exact same physical
    database (host, port, schema, user) - used to avoid opening a second
    connection pool to a server a pool is already open against."""
    return (a.host, a.port, a.database, a.username) == (b.host, b.port, b.database, b.username)


class TenantConnectionManager:
    """Manages isolated MySQL database connection pools for each tenant.
    Guarantees failure isolation: an outage on one tenant's database does not
    affect other tenants or the FastAPI application."""

    # How long a "this tenant is active" verdict is trusted before the registry is asked again -
    # same order of magnitude as the admin dashboard's own stats cache (admin.py), chosen for the
    # same reason: bound the extra Common DB round trip this adds to every tenant-scoped request,
    # while still noticing a suspension within a bounded, short window rather than never (see
    # `_check_tenant_active`).
    STATUS_CACHE_SECONDS = 30

    def __init__(self) -> None:
        self._engines: Dict[str, Engine] = {}
        self._sessionmakers: Dict[str, sessionmaker] = {}
        self._lock = threading.Lock()
        self._status_cache = TTLCache(ttl_seconds=self.STATUS_CACHE_SECONDS, max_entries=500)
        self._uid_cache = TTLCache(ttl_seconds=self.STATUS_CACHE_SECONDS, max_entries=1)

    def clear_status_cache(self) -> None:
        """Forgets every cached registry read - status verdicts and ID spellings - so the next call
        for every tenant re-reads the registry. Tests use this so they don't have to wait out
        STATUS_CACHE_SECONDS after changing a tenant's row; production has no caller for this today
        (the cache expiring on its own is what normal operation relies on)."""
        self._status_cache.clear()
        self._uid_cache.clear()

    def canonical_uid(self, tenant_id: str) -> str:
        """The registry's own spelling of a tenant ID an app sent or a person typed before login
        ("SAMSUNG " -> "samsung"), so every per-tenant key - connection pool, token claim,
        admin_access grant, media folder, WebSocket room - sees one spelling of one tenant. An ID
        the registry doesn't know (or can't be asked about) comes back as sent, trimmed: get_engine
        then refuses it exactly as before.

        Reads the whole (small) registry at most once per STATUS_CACHE_SECONDS, never once per ID
        asked about, so made-up IDs cost nothing. A tenant registered within that window is matched
        in its exact spelling straight away, in another letter case once the window ends."""
        sent = tenant_id.strip()
        spellings = self._uid_cache.get(_SPELLINGS)
        if spellings is None:
            spellings = self._read_spellings()
            if spellings is None:
                return sent
            self._uid_cache.set(_SPELLINGS, spellings)
        return spellings.get(tenant_repository.code_key(sent), sent)

    @staticmethod
    def _read_spellings() -> Optional[Dict[str, str]]:
        """Every registered tenant ID by its `code_key`, or None when the registry can't be read."""
        common_db = common_database.CommonSessionLocal()
        try:
            return {tenant_repository.code_key(uid): uid for uid in tenant_repository.list_uids(common_db)}
        except SQLAlchemyError:
            logger.exception("Failed to read the tenant registry's IDs")
            return None
        finally:
            common_db.close()

    def _check_tenant_active(self, tenant_uid: str, common_db: Optional[Session]) -> None:
        """Re-verifies the tenant is still active on every call - not just when its connection
        pool is first created. Without this, a tenant suspended after its first request (which
        creates and caches the Engine) would keep working indefinitely on the cached pool, since
        `get_engine`'s fast path below never touched the registry again. A short TTL cache (not a
        live query every call) bounds the added cost to one Common DB round trip per tenant per
        `STATUS_CACHE_SECONDS`, not per request.

        Fails safe in both directions: a cached "not active" verdict always raises, even before
        touching the database again; a Common DB error while checking is logged and treated as
        "unknown, trust what's already running" rather than taking down an otherwise-healthy
        tenant connection - consistent with this class's own failure-isolation guarantee, and
        with how a Common DB error is already handled in the cold path below."""
        cached = self._status_cache.get(tenant_uid)
        if cached is not None:
            if not cached:
                raise _inactive_tenant_error()
            return
        if common_db is None:
            return
        try:
            record = tenant_repository.get(common_db, tenant_uid)
        except SQLAlchemyError:
            logger.exception("Failed to re-check tenant status for '%s'", tenant_uid)
            return
        if record is None:
            return
        self._remember_status(tenant_uid, record)

    def _remember_status(self, tenant_uid: str, record: Tenant) -> None:
        """Caches the verdict just read from the registry - so get_engine's fast path doesn't
        re-query Common DB on the very next call - and refuses a tenant that isn't active."""
        self._status_cache.set(tenant_uid, record.is_active)
        if not record.is_active:
            raise _inactive_tenant_error()

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
            self._check_tenant_active(tenant_uid, common_db)
            return self._engines[tenant_uid]

        with self._lock:
            if tenant_uid in self._engines:
                self._check_tenant_active(tenant_uid, common_db)
                return self._engines[tenant_uid]

            db_url = self._resolve_tenant_url(tenant_uid, common_db)
            try:
                engine = self._engine_for(db_url)
                self._sync_schema(tenant_uid, engine)
                self._engines[tenant_uid] = engine
                self._sessionmakers[tenant_uid] = sessionmaker(
                    autocommit=False, autoflush=False, bind=engine
                )
                return engine
            except SQLAlchemyError:
                logger.exception("Failed to initialize engine for tenant '%s'", tenant_uid)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Tenant database is temporarily unavailable",
                )

    def _resolve_tenant_url(self, tenant_uid: str, common_db: Optional[Session]) -> URL:
        """Where the tenant's database is: its registry row in Common DB (refused unless active),
        else - for the default tenant only - the DB_* settings. Any other tenant is a 404."""
        tenant_record: Optional[Tenant] = None
        if common_db is not None:
            try:
                tenant_record = tenant_repository.get(common_db, tenant_uid)
            except SQLAlchemyError:
                logger.exception("Failed to query tenant registry from Common DB")

        if tenant_record:
            return self._registry_url(tenant_uid, tenant_record)
        if tenant_uid == settings.DEFAULT_TENANT_ID:
            # Fallback for default tenant using environment configuration
            return self._build_tenant_url(
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                db_name=settings.DB_NAME,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_uid}' not found",
        )

    def _registry_url(self, tenant_uid: str, tenant_record: Tenant) -> URL:
        """The connection URL from an active tenant's registry row, its password decrypted."""
        self._remember_status(tenant_uid, tenant_record)
        if not tenant_record.is_set_up:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=NOT_SET_UP)
        try:
            database_password = decrypt_secret(tenant_record.database_password)
        except SecretUnavailable:
            # Fail closed for this tenant only; the message names no secret (secret_box raises
            # it with fixed text and `from None`, so the traceback carries no key material).
            logger.exception("Cannot decrypt the database password of tenant '%s'", tenant_uid)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Tenant database is temporarily unavailable",
            )
        return self._build_tenant_url(
            user=tenant_record.database_username,
            password=database_password,
            host=tenant_record.database_host,
            port=tenant_record.database_port,
            db_name=tenant_record.database_name,
        )

    def _engine_for(self, db_url: URL) -> Engine:
        """Reuse an already-open pool - Common DB's, or another tenant's - when it points at the
        exact same physical database, rather than opening a second independent pool to the same
        server. Without this, a tenant whose credentials happen to match Common DB's (the default
        tenant, until its `tenants` row - if any - or COMMON_DB_* is set to somewhere else) doubles
        the connection count against the database's connection limit for no reason, which on a
        small managed MySQL plan (e.g. Aiven's lower tiers) can exhaust it and surface as "Tenant
        database is temporarily unavailable" even though the database itself is perfectly healthy.
        Called with `_lock` held."""
        if _same_target(db_url, common_engine.url):
            return common_engine
        return next(
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
            **SAFE_ENGINE_OPTIONS,
        )

    @staticmethod
    def _sync_schema(tenant_uid: str, engine: Engine) -> None:
        """The same additive-only column/index sync main.py runs for the default tenant at
        startup, once per tenant when its pool is first created - so a column added to a tenant
        model (e.g. tokenVersion) reaches every tenant database, not just the default one, before
        any query selects it. Best-effort: a failure is logged and never blocks the tenant
        (failure isolation). Skipped under tests, which must never run DDL."""
        if settings.TESTING:
            return
        try:
            sync_missing_columns(engine, TenantBase)
            sync_missing_indexes(engine, TenantBase)
        except SQLAlchemyError:
            logger.exception("Schema sync skipped for tenant '%s'", tenant_uid)

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
        # Snapshot under the lock: this runs on the keep-alive worker thread while request threads
        # add tenants (get_engine), and iterating the live dict would raise "dictionary changed
        # size during iteration" - ending the keep-alive loop for good.
        with self._lock:
            engines = list(self._engines.items())
        for tenant_uid, engine in engines:
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
