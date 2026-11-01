from typing import Optional

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.dependencies.database import get_common_db, get_db, get_optional_db, get_tenant_id_from_request
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.routers._staff_login import staff_sign_in
from app.schemas.admin import AdminAuthSession, AdminLoginRequest
from app.schemas.catalog import SelectOptionOut
from app.schemas.trainer_profile import TrainerProfileOut, TrainerProfileUpdate
from app.services import trainer_service
from app.services.access_service import TRAINER_ACCOUNT

# Staff routes: mounted at /admin for admins and /trainer for trainers (main.py).
router = APIRouter(tags=["trainer"])
# The trainer login: mounted at /trainer only.
login_router = APIRouter(tags=["trainer"])


@login_router.post("/login", response_model=AdminAuthSession)
def login(
    payload: AdminLoginRequest,
    request: Request,
    common_db: Session = Depends(get_common_db),
    db: Optional[Session] = Depends(get_optional_db),
):
    """A trainer's sign-in (user, 2026-10-31): POST /admin/login's, for trainer accounts only - an admin
    account is told to use Admin login."""
    return staff_sign_in(payload, request, common_db, db, kind=TRAINER_ACCOUNT)


@router.get("/trainers", response_model=list[SelectOptionOut])
def list_trainers(
    company: str | None = None,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    admin: Admin = Depends(get_current_admin),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return trainer_service.list_trainers(common_db, db, admin, tenant_id, company)


@router.get("/trainers/{username}")
def get_trainer_name(
    username: str,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    _admin: Admin = Depends(get_current_admin),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return trainer_service.get_trainer_name(common_db, db, _admin, username, tenant_id)


@router.get("/profile", response_model=TrainerProfileOut)
def get_profile(admin: Admin | AgencyTeam = Depends(get_current_admin)):
    return trainer_service.get_profile(admin)


@router.patch("/profile", response_model=TrainerProfileOut)
def update_profile(
    payload: TrainerProfileUpdate,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    admin: Admin | AgencyTeam = Depends(get_current_admin),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return trainer_service.update_profile(common_db, db, admin, payload, tenant_id)


@router.post("/profile/photo", response_model=TrainerProfileOut)
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    admin: Admin | AgencyTeam = Depends(get_current_admin),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return await trainer_service.upload_profile_photo(common_db, db, admin, file, tenant_id)


@router.post("/profile/aadhar", response_model=TrainerProfileOut)
async def upload_aadhar_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    admin: Admin | AgencyTeam = Depends(get_current_admin),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return await trainer_service.upload_aadhar_document(common_db, db, admin, file, tenant_id)
