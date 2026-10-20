"""The one way the maintenance scripts open a tenant's database."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def tenant_engine(tenant_id: str) -> Engine:
    """The tenant's database, found the way the app finds it (its registry row, else - for the
    default tenant - the DB_* settings) - without opening the app's pool or running its schema
    sync, so a script changes nothing but what it says it changes."""
    from app.database.common import CommonSessionLocal
    from app.database.connection import SAFE_ENGINE_OPTIONS, build_connect_args
    from app.database.tenant import tenant_manager

    common_db = CommonSessionLocal()
    try:
        url = tenant_manager._resolve_tenant_url(tenant_id, common_db)
    finally:
        common_db.close()
    return create_engine(url, connect_args=build_connect_args(), **SAFE_ENGINE_OPTIONS)
