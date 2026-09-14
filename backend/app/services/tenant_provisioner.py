import logging

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session

from app.database.connection import TenantBase, build_connect_args
from app.models.common.tenant_registry import Tenant

logger = logging.getLogger("tenant_provisioner")


def provision_new_tenant(
    tenant_uid: str,
    company_name: str,
    database_host: str,
    database_port: int,
    database_name: str,
    database_username: str,
    database_password: str,
    common_db: Session,
    status: str = "active",
) -> Tenant:
    """Provisions a new tenant database by:
    1. Creating every tenant table in the specified MySQL database instance.
    2. Registering the tenant in the Common DB tenants registry.
    """
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=database_username,
        password=database_password,
        host=database_host,
        port=database_port,
        database=database_name,
    )

    logger.info("Initializing schema for tenant '%s' at %s:%s/%s", tenant_uid, database_host, database_port, database_name)

    tenant_engine = create_engine(db_url, pool_pre_ping=True, connect_args=build_connect_args())
    try:
        TenantBase.metadata.create_all(bind=tenant_engine)
    finally:
        tenant_engine.dispose()

    existing = common_db.query(Tenant).filter(Tenant.tenant_uid == tenant_uid).first()
    if existing:
        existing.company_name = company_name
        existing.database_host = database_host
        existing.database_port = database_port
        existing.database_name = database_name
        existing.database_username = database_username
        existing.database_password = database_password
        existing.status = status
        tenant_record = existing
    else:
        tenant_record = Tenant(
            tenant_uid=tenant_uid,
            company_name=company_name,
            database_host=database_host,
            database_port=database_port,
            database_name=database_name,
            database_username=database_username,
            database_password=database_password,
            status=status,
        )
        common_db.add(tenant_record)

    common_db.commit()
    common_db.refresh(tenant_record)
    logger.info("Successfully provisioned and registered tenant '%s'", tenant_uid)
    return tenant_record
