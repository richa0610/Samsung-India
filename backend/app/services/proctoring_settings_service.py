from app.core.config import settings
from app.database.common import CommonSessionLocal
from app.models.common.tenant_registry import Tenant


def get_proctoring_settings(tenant_id: str) -> tuple[bool, int]:
    """Resolves a tenant's live-proctoring on/off + max-warnings settings
    from the Common DB registry (admin-configurable, per company).

    Opens its own short-lived Common DB session rather than requiring a
    `common_db` dependency to be threaded through the caller's whole call
    chain - callers only need the plain `tenant_id` string, which is cheap
    to resolve at the router level via get_tenant_id_from_request. Falls
    back to enabled + the default warning count when no registry row
    exists yet (e.g. the default tenant bootstrapped from env config
    before an admin ever managed it)."""
    common_db = CommonSessionLocal()
    try:
        tenant = common_db.query(Tenant).filter(Tenant.tenant_uid == tenant_id).first()
    finally:
        common_db.close()

    if not tenant:
        return True, settings.DEFAULT_PROCTORING_MAX_WARNINGS
    return bool(tenant.live_proctoring_enabled), tenant.proctoring_max_warnings
