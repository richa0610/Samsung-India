"""Tenant-wide settings kept on the tenant's own registry row (Common DB `tenants`, next to the
proctoring controls). The trainee check-in reads them; only a Super Admin changes them."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.repositories import tenant_repository
from app.services.activity_log_service import log_activity


def checkin_face_detection_enabled(common_db: Session, tenant_id: str) -> bool:
    """Whether this tenant's trainees pass the face check at the security check-in, or just
    capture a photo. A tenant with no registry row (the default one bootstrapped from env config)
    keeps the check on - the stricter of the two."""
    tenant = tenant_repository.get(common_db, tenant_id)
    return True if tenant is None else bool(tenant.checkin_face_detection_enabled)


def set_checkin_face_detection(
    common_db: Session,
    tenant_db: Session,
    tenant_id: str,
    enabled: bool,
    *,
    username: str,
    ip_address: Optional[str] = None,
) -> bool:
    """Turns the check-in face check on or off for the whole tenant, and records who did it in
    that tenant's activity log."""
    tenant = tenant_repository.get(common_db, tenant_id)
    if tenant is None:
        raise not_found("Tenant not found")
    tenant.checkin_face_detection_enabled = 1 if enabled else 0
    common_db.commit()
    log_activity(
        tenant_db,
        action="UPDATE_CHECKIN_FACE_DETECTION",
        username=username,
        role="super_admin",
        remarks=f"Face detection at trainee check-in turned {'on' if enabled else 'off'}",
        ip_address=ip_address,
    )
    return enabled
