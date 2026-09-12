from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.dependencies.auth import get_current_trainee
from app.dependencies.database import get_db, get_tenant_id_from_request
from app.models.trainee import Trainee
from app.schemas.trainee import (
    TokenResponse,
    TraineeLogin,
    TraineeOut,
    TraineeRegister,
    TraineeUpdate,
)
from app.services import trainee_service

router = APIRouter(prefix="/trainees", tags=["trainees"])


@router.post(
    "/register",
    response_model=TraineeOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_attempts=5, window_seconds=300))],
)
def register_trainee(payload: TraineeRegister, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return trainee_service.register(db, payload, background_tasks)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(max_attempts=5, window_seconds=300))],
)
def login_trainee(payload: TraineeLogin, request: Request, db: Session = Depends(get_db)):
    tenant_id = get_tenant_id_from_request(request)
    return trainee_service.login(db, payload, tenant_id)


@router.patch("/me", response_model=TokenResponse)
def update_trainee(
    payload: TraineeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    tenant_id = get_tenant_id_from_request(request)
    return trainee_service.update_me(db, trainee, payload, tenant_id)


@router.post("/me/photo", response_model=TraineeOut)
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return await trainee_service.upload_profile_photo(db, trainee, file)
