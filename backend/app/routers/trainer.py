from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.dependencies.database import get_common_db, get_db
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.schemas.catalog import SelectOptionOut
from app.schemas.trainer_profile import TrainerProfileOut, TrainerProfileUpdate
from app.services import trainer_service

router = APIRouter(prefix="/admin", tags=["trainer"])


@router.get("/trainers", response_model=list[SelectOptionOut])
def list_trainers(
    company: str | None = None,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    _admin: Admin = Depends(get_current_admin),
):
    return trainer_service.list_trainers(common_db, db, company)


@router.get("/trainers/{username}")
def get_trainer_name(
    username: str,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    _admin: Admin = Depends(get_current_admin),
):
    return trainer_service.get_trainer_name(common_db, db, username)


@router.get("/profile", response_model=TrainerProfileOut)
def get_profile(admin: Admin | AgencyTeam = Depends(get_current_admin)):
    return trainer_service.get_profile(admin)


@router.patch("/profile", response_model=TrainerProfileOut)
def update_profile(
    payload: TrainerProfileUpdate,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    admin: Admin | AgencyTeam = Depends(get_current_admin),
):
    return trainer_service.update_profile(common_db, db, admin, payload)


@router.post("/profile/photo", response_model=TrainerProfileOut)
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    admin: Admin | AgencyTeam = Depends(get_current_admin),
):
    return await trainer_service.upload_profile_photo(common_db, db, admin, file)
