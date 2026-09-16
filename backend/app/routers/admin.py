from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.dependencies.database import get_common_db, get_db, get_tenant_id_from_request
from app.schemas.admin import AdminAuthSession, AdminLoginRequest
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


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
    return admin_service.login(common_db, db, payload, tenant_id)
