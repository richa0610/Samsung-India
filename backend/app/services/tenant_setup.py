"""Automatic company setup (user, 2026-10-22): a `tenants` row added with just a company name - by
hand, in DBeaver or by the PHP system - becomes a working company without anyone running a script.

Every TENANT_AUTO_SETUP_MINUTES the server looks for active rows not set up yet (`Tenant.is_set_up`:
no ID, or database details missing or only part filled in) and, for each:
  1. gives it its ID if it has none (TEN_<ABC>_<YY><seq>, models/uid_events.py) - saved first, so a
     retry names the same database;
  2. creates its database on Bluehost through cPanel's API (an account's MySQL logins can't) -
     TENANT_DB_NAME_PREFIX + the ID in lower case - and gives the ONE company login, TENANT_DB_USER,
     every privilege on it;
  3. creates the app's tables in it and copies the default company's dropdown lists
     (services/company_lists);
  4. fills in the row's database details (the password encrypted - core/secret_box) and its agency
     link (the agency registered under its company name), and clears `setup_error`.
A row whose database details were all typed in by hand (host, name and login) only gets its ID - its
own database is used, nothing is made for it. Details only part filled in are replaced by step 4.
Steps 2 and 3 are safe to repeat, so a setup cut off half way just runs again. A failure is written
to the row's `setup_error` - in words, never a secret - and that row is tried again after
RETRY_MINUTES. Until a row is set up nothing is served for it (`Tenant.is_ready`)."""

import logging
import re
from dataclasses import dataclass
from typing import Callable, Optional

from sqlalchemy import create_engine, func
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.secret_box import encryption_enabled, protect_secret
from app.core.ttl_cache import TTLCache
from app.database.connection import SAFE_ENGINE_OPTIONS, TenantBase, build_connect_args
from app.database.tenant import NOT_SET_UP as NOT_READY  # noqa: F401 - what a company still being set up is answered
from app.database.tenant import tenant_manager
from app.models.common.tenant_registry import Tenant
from app.services import company_lists
from app.services.company_ids import registered_id
from app.services.cpanel_client import CpanelClient
from app.utils.uid import next_tenant_uid

logger = logging.getLogger("tenant_setup")

RETRY_MINUTES = 10
MAX_NAME_LENGTH = 64   # MySQL's limit on a database name
# The `tenants` columns a row added by hand leaves out - loosened on the live table at startup
# (database/schema_sync.relax_columns): {column: (may be NULL, its DEFAULT)}.
SHORT_ROW_COLUMNS = {
    "tenant_uid": (True, None),
    "database_host": (True, None),
    "database_port": (True, "3306"),
    "database_name": (True, None),
    "database_username": (True, None),
    "database_password": (True, None),
    "status": (False, "'active'"),
    "created_at": (False, "CURRENT_TIMESTAMP"),
    "updated_at": (False, "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
}
# Rows that failed lately (tenants.id) - not tried again until RETRY_MINUTES have passed.
_resting = TTLCache(ttl_seconds=RETRY_MINUTES * 60, max_entries=10_000)


@dataclass(frozen=True)
class SetupConfig:
    cpanel_url: str
    cpanel_user: str
    cpanel_token: str
    verify_tls: bool
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    name_prefix: str

    @classmethod
    def from_settings(cls) -> "SetupConfig":
        return cls(
            settings.CPANEL_URL, settings.CPANEL_USER, settings.CPANEL_API_TOKEN, settings.CPANEL_VERIFY_TLS,
            settings.TENANT_DB_HOST, settings.TENANT_DB_PORT, settings.TENANT_DB_USER, settings.TENANT_DB_PASSWORD,
            settings.TENANT_DB_NAME_PREFIX,
        )

    def missing(self) -> list[str]:
        """The settings a setup needs that aren't set - names only."""
        needed = {"CPANEL_URL": self.cpanel_url, "CPANEL_USER": self.cpanel_user, "CPANEL_API_TOKEN": self.cpanel_token,
                  "TENANT_DB_HOST": self.db_host, "TENANT_DB_USER": self.db_user, "TENANT_DB_PASSWORD": self.db_password,
                  "TENANT_DB_NAME_PREFIX": self.name_prefix}
        return [name for name, value in needed.items() if not (value or "").strip()]


def database_name(prefix: str, tenant_uid: str) -> str:
    """The company's database: the prefix + its ID in lower case, anything but letters and digits
    turned into "_" (TEN_SAM_2620001 -> mmtbtwob_tops_ten_sam_2620001). ValueError past MySQL's limit."""
    slug = re.sub(r"[^a-z0-9]+", "_", tenant_uid.lower()).strip("_")
    name = f"{prefix}{slug}"
    if not slug or len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"Can't name a database for company ID {tenant_uid!r} (empty, or over {MAX_NAME_LENGTH} characters)")
    return name


def pending(common_db: Session) -> list[Tenant]:
    """Active rows not set up yet (`Tenant.is_set_up`) - the companies waiting to be set up. The same
    test that refuses to serve a company, so no row can wait forever unseen by its setup."""
    rows = common_db.query(Tenant).filter(func.lower(func.trim(Tenant.status)) == "active").order_by(Tenant.id).all()
    return [row for row in rows if not row.is_set_up and (row.company_name or "").strip()]


def _has_own_database(row: Tenant) -> bool:
    return bool(row.database_host and row.database_name and row.database_username)


def _open_engine(url: URL) -> Engine:
    return create_engine(url, pool_pre_ping=True, connect_args=build_connect_args(), **SAFE_ENGINE_OPTIONS)


def _default_engine() -> Optional[Engine]:
    """The default company's database - where the dropdown lists are copied from."""
    try:
        return tenant_manager.get_engine(settings.DEFAULT_TENANT_ID)
    except Exception:
        logger.exception("Couldn't open the default company to copy its lists from")
        return None


def set_up_pending(
    common_db: Session,
    *,
    config: Optional[SetupConfig] = None,
    cpanel_factory: Optional[Callable[[SetupConfig], CpanelClient]] = None,
    open_engine: Callable[[URL], Engine] = _open_engine,
    default_engine: Callable[[], Optional[Engine]] = _default_engine,
) -> list[str]:
    """Sets up every company waiting for it (`pending`), each on its own - one failing never stops
    the others. Returns the IDs of the companies it finished."""
    rows = [row for row in pending(common_db) if not _resting.get(row.id)]
    if not rows:
        return []
    config = config or SetupConfig.from_settings()
    missing = config.missing()
    if missing:
        for row in rows:
            _record_failure(common_db, row, "Automatic setup isn't configured on the server - missing " + ", ".join(missing))
        return []
    cpanel_factory = cpanel_factory or (lambda c: CpanelClient(c.cpanel_url, c.cpanel_user, c.cpanel_token, verify_tls=c.verify_tls))
    finished = []
    with cpanel_factory(config) as cpanel:
        source = default_engine()
        for row in rows:
            try:
                set_up(common_db, row, config, cpanel, open_engine, source)
                finished.append(row.tenant_uid)
            except Exception as exc:
                common_db.rollback()
                logger.exception("Automatic setup of company row %s failed", row.id)
                _record_failure(common_db, row, _reason(exc))
    return finished


def set_up(common_db: Session, row: Tenant, config: SetupConfig, cpanel: CpanelClient,
           open_engine: Callable[[URL], Engine], source: Optional[Engine]) -> None:
    """One company, in the order the module docstring gives."""
    if not row.tenant_uid:
        row.tenant_uid = next_tenant_uid(common_db.connection(), row.company_name)
        try:
            common_db.commit()
        except IntegrityError:
            common_db.rollback()   # another server process numbered it at the same moment - next round
            raise RuntimeError("Its company ID was taken at the same moment - trying again shortly")
    if _has_own_database(row):   # typed in by hand - it only lacked its ID
        row.setup_error = None
        common_db.commit()
        _resting.discard(row.id)
        logger.warning("Company %s (%s) got its ID - it already had its database details", row.tenant_uid, row.company_name)
        return
    if row.database_host or row.database_name or row.database_username:
        logger.warning("Company row %s had only part of its database details - they are replaced by its new database", row.id)
    name = database_name(config.name_prefix, row.tenant_uid)
    cpanel.create_database(name)
    cpanel.grant_all(config.db_user, name)

    url = URL.create("mysql+pymysql", username=config.db_user, password=config.db_password,
                     host=config.db_host, port=config.db_port, database=name)
    engine = open_engine(url)
    try:
        TenantBase.metadata.create_all(bind=engine)
        if source is not None:
            copied = company_lists.copy_lists(source, engine)
            if copied:
                logger.info("Company %s got the default company's lists: %s", row.tenant_uid, copied)
    finally:
        engine.dispose()

    if not encryption_enabled():
        logger.warning("TENANT_SECRETS_KEYS is not set - company %s's database password is stored unencrypted", row.tenant_uid)
    row.database_host, row.database_port, row.database_name = config.db_host, config.db_port, name
    row.database_username, row.database_password = config.db_user, protect_secret(config.db_password)
    row.agency_uid = row.agency_uid or registered_id(common_db, row.company_name)
    row.setup_error = None
    common_db.commit()
    _resting.discard(row.id)
    logger.warning("Company %s (%s) is set up - database %s", row.tenant_uid, row.company_name, name)


def _reason(exc: Exception) -> str:
    """What went wrong, in words fit for the row: the first line of the error, no traceback."""
    text = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
    return text[:480]


def _record_failure(common_db: Session, row: Tenant, reason: str) -> None:
    _resting.set(row.id, True)
    try:
        row.setup_error = reason[:500]
        common_db.commit()
    except Exception:
        common_db.rollback()
        logger.exception("Couldn't note the setup failure on company row %s", row.id)
