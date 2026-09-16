from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, text

from app.database.connection import CommonBase


class Tenant(CommonBase):
    """Registry of all onboarded client tenants, stored in the Common
    Database. Contains database connection credentials for each tenant's
    isolated MySQL instance, resolved lazily by app.database.tenant's
    TenantConnectionManager."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    tenant_uid = Column(String(100), unique=True, nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    database_host = Column(String(255), nullable=False)
    database_port = Column(Integer, nullable=False, default=3306)
    database_name = Column(String(100), nullable=False)
    database_username = Column(String(100), nullable=False)
    database_password = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="active")  # 'active', 'inactive', 'suspended'

    # Company-level proctoring controls, decided by the admin per tenant.
    # `live_proctoring_enabled` gates whether this company's trainees can use
    # the camera-based proctoring flow at all (see /proctoring endpoints);
    # `proctoring_max_warnings` is how many times a trainee may be flagged
    # (e.g. multiple faces in frame) before the session is considered failed.
    live_proctoring_enabled = Column(Integer, nullable=False, server_default=text("0"))  # 0 = off, 1 = on
    proctoring_max_warnings = Column(Integer, nullable=False, server_default=text("3"))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
