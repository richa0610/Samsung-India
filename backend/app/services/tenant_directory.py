"""Which company (tenant) the app is talking to: the company code a person types before signing in,
and the company a signed-in account belongs to - both answered from the tenant registry (Common DB)."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.database.tenant import NOT_SET_UP
from app.models.common.tenant_registry import Tenant
from app.repositories import tenant_repository
from app.schemas.tenant import TenantOut

# One answer for a code nobody registered and for a company that is suspended / inactive, so the
# lookup tells an outsider nothing beyond "you can't sign in to this".
UNKNOWN_COMPANY = "Company code not found"


def _out(tenant: Tenant) -> TenantOut:
    return TenantOut(tenantId=tenant.tenant_uid, companyName=tenant.company_name)


def lookup(common_db: Session, code: str) -> TenantOut:
    """The active company a typed code names - its ID in any letter case."""
    tenant = tenant_repository.find_by_code(common_db, code)
    if tenant is None or not tenant.is_active:
        raise not_found(UNKNOWN_COMPANY)
    if not tenant.is_set_up:   # added moments ago - its automatic setup hasn't finished (services/tenant_setup)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=NOT_SET_UP)
    return _out(tenant)


def describe(common_db: Session, tenant_id: str) -> TenantOut:
    """The company a verified token was issued for."""
    tenant = tenant_repository.get(common_db, tenant_id)
    if tenant is None:
        raise not_found(UNKNOWN_COMPANY)
    return _out(tenant)
