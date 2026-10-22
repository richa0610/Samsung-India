from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_trainee, get_token_claims
from app.dependencies.database import get_common_db, get_db, get_optional_db, get_tenant_id_from_request
from app.models.trainee import Trainee
from app.schemas.trainee import (
    TokenResponse,
    TraineeLogin,
    TraineeOut,
    TraineeRegister,
    TraineeUpdate,
)
from app.services import sign_in_service, token_revocation, trainee_service
from app.services.device_sessions import Device
from app.utils.helpers import client_ip

router = APIRouter(prefix="/trainees", tags=["trainees"])


def _device(payload, request: Request) -> Device:
    return Device.of(payload.deviceId, payload.deviceName, request.headers.get("user-agent"))


# Signs the new trainee in too (a self-registered trainee has no password to log in with later).
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_trainee(
    payload: TraineeRegister,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
):
    return trainee_service.register(
        db, common_db, payload, background_tasks,
        ip_address=client_ip(request), tenant_id=get_tenant_id_from_request(request), device=_device(payload, request),
    )


# Company ID / phone + password. Limited by failed logins per account only (trainee_service.login) -
# never per caller IP, which would lock out a classroom on one venue Wi-Fi. Without a company code
# the central user registry finds the company (services/sign_in_service).
@router.post("/login", response_model=TokenResponse)
def login_trainee(
    payload: TraineeLogin,
    request: Request,
    db: Optional[Session] = Depends(get_optional_db),
    common_db: Session = Depends(get_common_db),
):
    device = _device(payload, request)
    if db is None:
        return sign_in_service.sign_in_trainee(
            common_db, payload.identifier, payload.password, ip_address=client_ip(request), device=device,
            company=payload.company,
        )
    tenant_id = get_tenant_id_from_request(request)
    return trainee_service.login(db, payload, tenant_id, ip_address=client_ip(request), common_db=common_db, device=device)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    trainee: Trainee = Depends(get_current_trainee),
    claims: dict = Depends(get_token_claims),
) -> None:
    """Signs the trainee out on this device - or, for a token from before devices were tracked, on
    every device (token_revocation.sign_out)."""
    token_revocation.sign_out(db, trainee, db, common_db, claims.get("sid"), ip_address=client_ip(request))


@router.patch("/me", response_model=TokenResponse)
def update_trainee(
    payload: TraineeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    trainee: Trainee = Depends(get_current_trainee),
    claims: dict = Depends(get_token_claims),
):
    tenant_id = get_tenant_id_from_request(request)
    return trainee_service.update_me(db, common_db, trainee, payload, tenant_id, session_id=claims.get("sid"))


@router.post("/me/photo", response_model=TraineeOut)
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return await trainee_service.upload_profile_photo(db, trainee, file, tenant_id)
