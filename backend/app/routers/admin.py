from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.core.ttl_cache import TTLCache
from app.dependencies.auth import get_current_admin, require_admin_role
from app.dependencies.database import get_common_db, get_db, get_tenant_id_from_request
from app.dependencies.filters import ConferenceFilters, get_conference_filters
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.schemas.admin import AdminAccessScopeOut, AdminAuthSession, AdminDashboardStatsOut, AdminLoginRequest
from app.services import admin_service, token_revocation
from app.services.access_service import resolve_scope, scope_summary
from app.utils.helpers import client_ip

router = APIRouter(prefix="/admin", tags=["admin"])

# Dashboard stats are the same for a given admin + filter for a short while, and
# computing them costs a couple of database round trips - so repeat opens are
# served from memory for STATS_CACHE_SECONDS. Anything that must be current
# (pull-to-refresh, a live "training changed" event) sends `fresh=true`, which
# skips the cache and refreshes it.
STATS_CACHE_SECONDS = 30
_stats_cache = TTLCache(ttl_seconds=STATS_CACHE_SECONDS, max_entries=500)


def stats_cache_key(tenant_id: str, admin, scoped_filters: ConferenceFilters) -> tuple:
    """Who is asking and what they are allowed to see: the tenant, the exact
    account (its table + id) and the fully scoped filters (company / zone scope
    included), so one admin can never be served another's numbers."""
    return (tenant_id, type(admin).__name__, admin.id, repr(scoped_filters))


@router.post(
    "/login",
    response_model=AdminAuthSession,
    dependencies=[Depends(rate_limit(max_attempts=5, window_seconds=300))],
)
def login(
    payload: AdminLoginRequest,
    request: Request,
    common_db: Session = Depends(get_common_db),
    db: Session = Depends(get_db),
):
    tenant_id = get_tenant_id_from_request(request)
    return admin_service.login(common_db, db, payload, tenant_id, ip_address=client_ip(request))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    admin: Admin | AgencyTeam = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    db: Session = Depends(get_db),
) -> None:
    """Revokes every token of the signed-in account (all devices) - see token_revocation."""
    account_db = common_db if isinstance(admin, Admin) else db
    token_revocation.revoke_all_tokens(account_db, admin, db, ip_address=client_ip(request))


@router.get("/dashboard/stats", response_model=AdminDashboardStatsOut)
def get_admin_dashboard_stats(
    request: Request,
    fresh: bool = Query(False),
    common_db: Session = Depends(get_common_db),
    db: Session = Depends(get_db),
    filters: ConferenceFilters = Depends(get_conference_filters),
    admin: Admin = Depends(require_admin_role),
):
    # Authorization is the admin_access grant, resolved inside build_admin_dashboard_stats - not
    # apply_identity_scope's legacy company/zone columns. Cache isolation doesn't depend on that:
    # the key already carries admin.id, so two accounts never share an entry regardless of scope.
    tenant_id = get_tenant_id_from_request(request)
    key = stats_cache_key(tenant_id, admin, filters)
    if not fresh:
        cached = _stats_cache.get(key)
        if cached is not None:
            return cached
    stats = admin_service.build_admin_dashboard_stats(common_db, db, filters, admin=admin, tenant_id=tenant_id)
    _stats_cache.set(key, stats)
    return stats


@router.get("/access/scope", response_model=AdminAccessScopeOut)
def get_admin_access_scope(
    request: Request,
    common_db: Session = Depends(get_common_db),
    admin: Admin = Depends(require_admin_role),
):
    """The caller's own admin_access grant (Training List RBAC, Phase 3) - lets the app hide
    filter options and actions the caller isn't authorized for. Display only: every request
    that actually reads or changes a training is still checked server-side regardless of this."""
    scope = resolve_scope(common_db, admin, get_tenant_id_from_request(request))
    return scope_summary(scope)
