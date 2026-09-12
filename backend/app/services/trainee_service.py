from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.core.media import media_subdir
from app.core.security import create_access_token
from app.models.trainee import Trainee
from app.repositories import trainee_repository
from app.routers.ws import manager as ws_manager
from app.schemas.trainee import TokenResponse, TraineeLogin, TraineeRegister, TraineeUpdate
from app.utils.validators import validate_image_upload


def register(db: Session, payload: TraineeRegister, background_tasks: BackgroundTasks) -> Trainee:
    existing = trainee_repository.get_by_phone_or_email(db, payload.phone, payload.email)
    if existing:
        raise bad_request("Trainee with this phone or email already exists")

    trainee = trainee_repository.create(db, Trainee(**payload.model_dump()))

    background_tasks.add_task(ws_manager.broadcast, {"type": "trainee_created", "traineeUid": trainee.traineeUid})

    return trainee


def login(db: Session, payload: TraineeLogin, tenant_id: str) -> TokenResponse:
    trainee = trainee_repository.get_by_phone(db, payload.phone)
    if not trainee:
        raise not_found("No trainee found with this phone number")

    access_token = create_access_token(subject=str(trainee.phone), tenant_id=tenant_id, role="trainee")
    return TokenResponse(access_token=access_token, trainee=trainee)


def update_me(db: Session, trainee: Trainee, payload: TraineeUpdate, tenant_id: str) -> TokenResponse:
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "phone" in updates or "email" in updates:
        conflict = trainee_repository.get_update_conflict(
            db,
            trainee.id,
            updates.get("phone", trainee.phone),
            updates.get("email", trainee.email),
        )
        if conflict:
            raise bad_request("Another trainee already uses this phone or email")

    for field, value in updates.items():
        setattr(trainee, field, value)

    trainee_repository.save(db, trainee)

    # `get_current_trainee` looks a trainee up by phone (it's the JWT
    # subject), so a changed phone number invalidates the token that was
    # just used to make this request - issue a fresh one so the trainee
    # doesn't get silently logged out by their own edit.
    access_token = create_access_token(subject=str(trainee.phone), tenant_id=tenant_id, role="trainee")
    return TokenResponse(access_token=access_token, trainee=trainee)


async def upload_profile_photo(db: Session, trainee: Trainee, file) -> Trainee:
    contents = await file.read()
    extension = validate_image_upload(file.content_type, contents, size_error_detail="Image must be 5MB or smaller")

    # Named after the trainee (not the upload), so re-uploading replaces
    # the old file instead of littering the disk with orphans.
    photo_dir = media_subdir("trainee_photos")
    filename = f"{trainee.traineeUid}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    trainee.profilePhoto = f"trainee_photos/{filename}"
    return trainee_repository.save(db, trainee)
