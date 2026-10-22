from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, func, text

from app.database.connection import CommonBase


class Tenant(CommonBase):
    """Registry of all onboarded client tenants, stored in the Common
    Database. Contains database connection credentials for each tenant's
    isolated MySQL instance, resolved lazily by app.database.tenant's
    TenantConnectionManager.

    A row may be added with only `company_name` (user, 2026-10-22): its ID and its database
    details stay empty until the server sets the company up - creates its database, its tables and
    fills those in (services/tenant_setup). Until then it is served nowhere (`is_ready`)."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    # Empty on a row added by hand until its setup gives it TEN_<ABC>_<YY><seq> (models/uid_events.py).
    tenant_uid = Column(String(100), unique=True, nullable=True, index=True)
    company_name = Column(String(200), nullable=False)
    # The company's agency ID in the shared registry (`agency.agencyUid`) - filled by its setup or by
    # scripts/link_tenant_agencies.py once the company is registered there.
    agency_uid = Column(String(100))
    # Where the company's database is - all empty until it is set up.
    database_host = Column(String(255), nullable=True)
    database_port = Column(Integer, nullable=True, default=3306)
    database_name = Column(String(100), nullable=True)
    database_username = Column(String(100), nullable=True)
    database_password = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active", server_default=text("'active'"))  # 'active', 'inactive', 'suspended'
    # Why the company's automatic setup last failed - empty once it is set up (services/tenant_setup).
    setup_error = Column(Text)

    # Company-level proctoring controls, decided by the admin per tenant.
    # `live_proctoring_enabled` gates whether this company's trainees can use
    # the camera-based proctoring flow at all (see /proctoring endpoints);
    # `proctoring_max_warnings` is how many times a trainee may be flagged
    # (e.g. multiple faces in frame) before the session is considered failed.
    live_proctoring_enabled = Column(Integer, nullable=False, server_default=text("0"))  # 0 = off, 1 = on
    proctoring_max_warnings = Column(Integer, nullable=False, server_default=text("3"))
    # Trainee security check-in: 1 = the face check runs before the photo (place face, look
    # straight, move head; one face in the photo), 0 = the photo is just captured. Super Admin only.
    checkin_face_detection_enabled = Column(Integer, nullable=False, server_default=text("1"))

    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now(), nullable=False
    )

    @property
    def is_active(self) -> bool:
        """Only an "active" tenant (any letter case) is served; suspended / inactive ones are refused."""
        return (self.status or "").strip().lower() == "active"

    @property
    def is_set_up(self) -> bool:
        """Whether the company has its ID and database - a row added by hand doesn't until its setup."""
        return bool(self.tenant_uid and self.database_host and self.database_name and self.database_username)

    @property
    def is_ready(self) -> bool:
        """Active and set up: the only companies anything is served for."""
        return self.is_active and self.is_set_up
