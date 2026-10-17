from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

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
from app.services import token_revocation, trainee_service
from app.utils.helpers import client_ip

router = APIRouter(prefix="/trainees", tags=["trainees"])


# Signs the new trainee in too (a self-registered trainee has no password to log in with later).
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_trainee(
    payload: TraineeRegister, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)
):
    return trainee_service.register(
        db, payload, background_tasks, ip_address=client_ip(request), tenant_id=get_tenant_id_from_request(request)
    )


# Company ID / phone + password. Limited by failed logins per account only (trainee_service.login) -
# never per caller IP, which would lock out a classroom on one venue Wi-Fi.
@router.post("/login", response_model=TokenResponse)
def login_trainee(payload: TraineeLogin, request: Request, db: Session = Depends(get_db)):
    tenant_id = get_tenant_id_from_request(request)
    return trainee_service.login(db, payload, tenant_id, ip_address=client_ip(request))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
) -> None:
    """Revokes every token of the signed-in trainee (all devices) - see token_revocation."""
    token_revocation.revoke_all_tokens(db, trainee, db, ip_address=client_ip(request))


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
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return await trainee_service.upload_profile_photo(db, trainee, file, tenant_id)
