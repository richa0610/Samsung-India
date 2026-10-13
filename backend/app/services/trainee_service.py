from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.exceptions import bad_request, unauthorized
from app.core.media import media_subdir
from app.core.security import create_access_token, verify_password
from app.models.trainee import Trainee
from app.repositories import trainee_repository
from app.routers.ws import manager as ws_manager
from app.schemas.trainee import TokenResponse, TraineeLogin, TraineeRegister, TraineeUpdate
from app.services.activity_log_service import log_activity
from app.utils.validators import read_photo_upload

LOGIN_SCOPE = "trainee-login"   # rate_limit's key prefix for this login's failure counts


def register(
    db: Session,
    payload: TraineeRegister,
    background_tasks: BackgroundTasks,
    tenant_id: str,
    ip_address: str | None = None,
) -> TokenResponse:
    """Self-registration (no password - see `login`), which also signs the new trainee in: the app goes
    straight on to the session (QR join) or the trainee home."""
    existing = trainee_repository.get_by_phone_or_email(db, payload.phone, payload.email)
    if existing:
        raise bad_request("Trainee with this phone or email already exists")

    trainee = trainee_repository.create(db, Trainee(**payload.model_dump()))

    background_tasks.add_task(ws_manager.broadcast, tenant_id, {"type": "trainee_created", "traineeUid": trainee.traineeUid})

    session = _session_for(trainee, tenant_id)
    log_activity(
        db,
        action="REGISTER",
        username=str(trainee.phone),
        role="trainee",
        remarks=f"Self-registered as {trainee.traineeUid}",
        ip_address=ip_address,
        issued_token=session.access_token,
    )
    return session


def login(db: Session, payload: TraineeLogin, tenant_id: str, ip_address: str | None = None) -> TokenResponse:
    """Company ID (Trainee UID / username) or phone number, plus password. Only a trainee who has a
    password can sign in here; a self-registered one (no password) is signed in once, by `register`."""
    # Only FAILED logins are limited - per caller IP (a whole classroom shares the venue Wi-Fi's one
    # address, so successes must not count) and per account, keyed by tenant so one tenant's failures
    # never lock the same account elsewhere.
    rate_limit.ensure_caller_not_locked(LOGIN_SCOPE, ip_address)
    trainee = trainee_repository.get_by_login_identifier(db, payload.identifier)
    # The account lock follows the trainee, not the words typed - switching between their UID and phone
    # number buys no extra guesses. An identifier that names nobody is counted under its own text.
    account = f"{tenant_id}:trainee-{trainee.id}" if trainee else f"{tenant_id}:typed-{payload.identifier}"
    rate_limit.ensure_account_not_locked(LOGIN_SCOPE, account)
    if not (trainee and trainee.password and verify_password(payload.password, trainee.password)):
        rate_limit.record_caller_failure(LOGIN_SCOPE, ip_address)
        rate_limit.record_account_failure(LOGIN_SCOPE, account)
        # The same words for every failure - unknown ID, no password set, or a wrong one.
        raise unauthorized("Couldn't sign in. Check your Company ID or Phone No and password.")
    rate_limit.clear_account_failures(LOGIN_SCOPE, account)

    session = _session_for(trainee, tenant_id)
    log_activity(
        db, action="LOGIN", username=str(trainee.phone), role="trainee", ip_address=ip_address,
        issued_token=session.access_token,
    )
    return session


def _session_for(trainee: Trainee, tenant_id: str) -> TokenResponse:
    """A signed-in session: the token's subject is the phone (`get_current_trainee` looks the trainee up
    by it) and it carries the account's token version, so a logout revokes it."""
    access_token = create_access_token(subject=str(trainee.phone), tenant_id=tenant_id, role="trainee", version=trainee.tokenVersion)
    return TokenResponse(access_token=access_token, trainee=trainee)


def update_me(db: Session, trainee: Trainee, payload: TraineeUpdate, tenant_id: str) -> TokenResponse:
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)

    # State is compulsory (it drives the State Ranking) - a profile save must
    # leave the trainee with one, whether it's already saved or sent now.
    if not (updates.get("state") or "").strip() and not (trainee.state or "").strip():
        raise bad_request("State is required")
    if "state" in updates:
        updates["state"] = updates["state"].strip()

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
    return _session_for(trainee, tenant_id)


async def upload_profile_photo(db: Session, trainee: Trainee, file, tenant_id: str) -> Trainee:
    contents, extension = await read_photo_upload(file, size_error_detail="Image must be 5MB or smaller")

    # Named after the trainee (not the upload), so re-uploading replaces
    # the old file instead of littering the disk with orphans.
    photo_dir = media_subdir("trainee_photos", tenant_id)
    filename = f"{trainee.traineeUid}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    trainee.profilePhoto = f"trainee_photos/{filename}"
    return trainee_repository.save(db, trainee)
