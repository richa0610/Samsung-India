from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin, get_token_claims, require_admin_role, require_super_admin
from app.dependencies.database import get_common_db, get_db, get_optional_db, get_tenant_id_from_request
from app.dependencies.filters import ConferenceFilters, get_conference_filters
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.schemas.admin import (
    AdminAccessScopeOut,
    AdminAuthSession,
    AdminDashboardStatsOut,
    AdminLoginRequest,
    CheckInSettingsOut,
    CheckInSettingsUpdate,
    CompanyChoiceRequest,
)
from app.services import admin_service, media_migration, sign_in_service, tenant_settings_service, token_revocation
from app.services.access_service import resolve_scope, scope_summary
from app.services.device_sessions import Device
from app.utils.helpers import client_ip

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminAuthSession)
def login(
    payload: AdminLoginRequest,
    request: Request,
    common_db: Session = Depends(get_common_db),
    db: Optional[Session] = Depends(get_optional_db),
):
    device = Device.of(payload.deviceId, payload.deviceName, request.headers.get("user-agent"))
    # Without a company code: an admin's grants, or the central user registry for a trainer, say
    # which company (services/sign_in_service) - an admin with several gets 409 CHOOSE_COMPANY.
    if db is None:
        return sign_in_service.sign_in_staff(
            common_db, payload.username, payload.password, ip_address=client_ip(request), device=device
        )
    tenant_id = get_tenant_id_from_request(request)
    return admin_service.login(common_db, db, payload, tenant_id, ip_address=client_ip(request), device=device)


@router.post("/login/company", response_model=AdminAuthSession)
def choose_login_company(payload: CompanyChoiceRequest, request: Request, common_db: Session = Depends(get_common_db)):
    """The company an admin with access to several picked after `POST /admin/login` answered 409
    CHOOSE_COMPANY - with that answer's ticket."""
    return sign_in_service.choose_company(common_db, payload.ticket, payload.tenantId, ip_address=client_ip(request))


@router.get("/maintenance/media-plan", dependencies=[Depends(require_super_admin)])
def get_media_migration_plan(common_db: Session = Depends(get_common_db)) -> dict:
    """READ-ONLY report of how pre-split uploads on this server would move into tenant folders
    (services/media_migration.py) - for a host without a shell. Super Admin only; moves nothing."""
    return media_migration.current_report(common_db)


@router.get("/settings/check-in", response_model=CheckInSettingsOut, dependencies=[Depends(require_super_admin)])
def get_check_in_settings(
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    """This tenant's trainee security check-in settings. Super Admin only."""
    return CheckInSettingsOut(
        faceDetectionEnabled=tenant_settings_service.checkin_face_detection_enabled(common_db, tenant_id)
    )


@router.put("/settings/check-in", response_model=CheckInSettingsOut)
def update_check_in_settings(
    payload: CheckInSettingsUpdate,
    request: Request,
    admin: Admin = Depends(require_super_admin),
    common_db: Session = Depends(get_common_db),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    """Turns the face check at the trainee security check-in on or off for this whole tenant
    (off = the trainee just captures a photo). Super Admin only; logged."""
    enabled = tenant_settings_service.set_checkin_face_detection(
        common_db, db, tenant_id, payload.faceDetectionEnabled, username=admin.username, ip_address=client_ip(request)
    )
    return CheckInSettingsOut(faceDetectionEnabled=enabled)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    admin: Admin | AgencyTeam = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    db: Session = Depends(get_db),
    claims: dict = Depends(get_token_claims),
) -> None:
    """Signs a trainer out on this device; an admin-table account (whose tokens name no device) - or
    a token from before devices were tracked - on every device (token_revocation.sign_out)."""
    account_db = common_db if isinstance(admin, Admin) else db
    token_revocation.sign_out(account_db, admin, db, common_db, claims.get("sid"), ip_address=client_ip(request))


@router.get("/dashboard/stats", response_model=AdminDashboardStatsOut)
def get_admin_dashboard_stats(
    request: Request,
    # Still accepted from the app (pull-to-refresh sends it); every answer is computed fresh anyway.
    fresh: bool = Query(False),
    common_db: Session = Depends(get_common_db),
    db: Session = Depends(get_db),
    filters: ConferenceFilters = Depends(get_conference_filters),
    admin: Admin = Depends(require_admin_role),
):
    # Authorization is the admin_access grant, resolved inside build_admin_dashboard_stats on every
    # request. Never cached: other servers and systems write to the same database, so a remembered
    # answer could be stale - the whole dashboard is one database round trip anyway.
    return admin_service.build_admin_dashboard_stats(
        common_db, db, filters, admin=admin, tenant_id=get_tenant_id_from_request(request)
    )


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
