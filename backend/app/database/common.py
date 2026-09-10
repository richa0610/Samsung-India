from typing import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.database.connection import build_connect_args

COMMON_DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=settings.common_db_user,
    password=settings.common_db_password,
    host=settings.common_db_host,
    port=settings.common_db_port,
    database=settings.common_db_name,
)

common_engine = create_engine(
    COMMON_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=280,
    connect_args=build_connect_args(),
)

CommonSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=common_engine,
)


def get_common_db() -> Generator[Session, None, None]:
    """Dependency for endpoints interacting with Common DB tables
    (superadmin accounts, system modules, the tenant registry)."""
    db = CommonSessionLocal()
    try:
        yield db
    finally:
        db.close()
