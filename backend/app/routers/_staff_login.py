"""The staff sign-in both logins share (user, 2026-10-31): POST /admin/login and POST /trainer/login
differ only in which kind of account they let in (admin_service.ensure_login_kind)."""

from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.dependencies.database import get_tenant_id_from_request
from app.schemas.admin import AdminAuthSession, AdminLoginRequest
from app.services import admin_service, sign_in_service
from app.services.device_sessions import Device
from app.utils.helpers import client_ip


def staff_sign_in(
    payload: AdminLoginRequest, request: Request, common_db: Session, db: Optional[Session], kind: Optional[str]
) -> AdminAuthSession:
    """Without a company code (`db` None) an admin's grants, or the central user registry for a
    trainer, say which company (services/sign_in_service) - an admin with several gets 409
    CHOOSE_COMPANY. With one, that company's own records decide (admin_service.login)."""
    device = Device.of(payload.deviceId, payload.deviceName, request.headers.get("user-agent"))
    if db is None:
        return sign_in_service.sign_in_staff(
            common_db, payload.username, payload.password, ip_address=client_ip(request), device=device, kind=kind
        )
    tenant_id = get_tenant_id_from_request(request)
    return admin_service.login(common_db, db, payload, tenant_id, ip_address=client_ip(request), device=device, kind=kind)
