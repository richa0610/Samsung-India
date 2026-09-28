from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

# Deliberately NOT `CommonBase` (app/database/connection.py).
#
# `app.main` runs `CommonBase.metadata.create_all(...)` against the live shared database every
# time the backend starts. A model on that metadata would therefore create this table on the
# next real restart, before anyone has reviewed it. This table has its OWN metadata so startup
# can never create it; it is created only by the reviewed SQL in docs/admin_access_table.sql
# (or, once that is approved, by moving it onto CommonBase). tests/test_access_model.py pins
# this, and pins that the SQL file matches this model.
AccessBase = declarative_base()

ROLES = ("super_admin", "company_admin", "coordinator", "sub_coordinator", "trainer")


class AdminAccess(AccessBase):
    """One grant of access to one admin-table account (shared database).

    An account can hold several grants; its access is their union. No grant = no access.
    Rows are written by trusted server-side tooling only, never from a request.

      role             what the grant is
      tenant_uid       the tenant it applies to; NULL only for `super_admin` (all tenants)
      company          required for company_admin / coordinator / sub_coordinator
      zone             required for coordinator (all of that zone's regions)
      region           required for sub_coordinator (that region only)
      company_admin_key  "<tenant>|<company>" (trimmed, lower-case) on an ACTIVE company_admin grant
                       and NULL on every other row. Its UNIQUE constraint is what guarantees
                       ONE Company Admin per company in each tenant, enforced by the database
                       itself (build it with access_service.company_admin_key).

    `trainer` grants give an admin-table trainer tenant membership (agency-team trainers live
    inside their own tenant's database and are members of it implicitly).
    """

    __tablename__ = "admin_access"

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, nullable=False, index=True)
    role = Column(String(30), nullable=False)
    tenant_uid = Column(String(100), nullable=True)
    company = Column(String(150), nullable=True)
    zone = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    active = Column(Integer, nullable=False, server_default=text("1"))
    granted_by = Column(String(100), nullable=True)
    note = Column(String(255), nullable=True)
    company_admin_key = Column(String(300), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin','company_admin','coordinator','sub_coordinator','trainer')",
            name="ck_admin_access_role",
        ),
        # Only a super admin is tenant-less; every other grant belongs to exactly one tenant.
        CheckConstraint(
            "(role = 'super_admin' AND tenant_uid IS NULL) OR (role <> 'super_admin' AND tenant_uid IS NOT NULL)",
            name="ck_admin_access_tenant",
        ),
        CheckConstraint(
            "role NOT IN ('company_admin','coordinator','sub_coordinator') OR company IS NOT NULL",
            name="ck_admin_access_company",
        ),
        CheckConstraint("role <> 'coordinator' OR zone IS NOT NULL", name="ck_admin_access_zone"),
        CheckConstraint("role <> 'sub_coordinator' OR region IS NOT NULL", name="ck_admin_access_region"),
        # The key exists exactly when this is an active company_admin grant; NULLs never collide in a
        # UNIQUE index, so every other row (and every deactivated one) is unaffected.
        CheckConstraint("(role = 'company_admin' AND active = 1) = (company_admin_key IS NOT NULL)", name="ck_admin_access_company_key"),
        UniqueConstraint("company_admin_key", name="uq_admin_access_one_company_admin"),
    )
