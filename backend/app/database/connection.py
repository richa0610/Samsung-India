from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


def build_connect_args() -> dict:
    """Shared connection options for every MySQL engine this app opens
    (default tenant, Common DB, and each additional tenant created via
    tenant_provisioner) - kept here so they can't drift between engines."""
    connect_args: dict = {"connect_timeout": 5, "read_timeout": 10, "write_timeout": 10}
    if settings.DB_SSL_CA:
        connect_args["ssl"] = {"ca": settings.DB_SSL_CA}
    return connect_args


# URL.create safely encodes characters such as @, :, and / in database
# credentials. Building the URL with an f-string makes those characters look
# like URL delimiters and prevents the API from starting.
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    # Proactively discard a pooled connection once it's this old, rather
    # than waiting to discover it's gone dead (managed MySQL providers and
    # the network path to them commonly close idle connections server-side
    # around the 5-10 minute mark - without this, reusing one of those after
    # it's silently died just hangs, since pool_pre_ping's own health-check
    # query can hang exactly the same way without the connect/read timeouts
    # above). 280s keeps every connection well under that window.
    pool_recycle=280,
    connect_args=build_connect_args(),
)

# This engine now backs the *default* tenant only (see app/database/tenant.py) -
# every other tenant gets its own isolated engine, resolved lazily from the
# Common DB's tenant registry.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Two declarative bases, matching the DB-per-tenant split:
# - CommonBase: tables shared globally in one Common Database (admin,
#   system_modules, the tenant registry itself).
# - TenantBase: every other table, duplicated into each tenant's own
#   isolated MySQL database.
# `Base` stays as an alias for `TenantBase` so none of the existing model
# files (which all do `from app.database.connection import Base`) need to
# change - only the handful of genuinely-common models are updated to
# import `CommonBase` instead.
CommonBase = declarative_base()
TenantBase = declarative_base()
Base = TenantBase
