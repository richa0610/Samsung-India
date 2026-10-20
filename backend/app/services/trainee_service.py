from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.exceptions import bad_request, unauthorized
from app.core.media import media_subdir
from app.core.security import create_access_token, verify_password
from app.models import uid_events
from app.models.trainee import Trainee
from app.repositories import trainee_repository
from app.routers.ws import manager as ws_manager
from app.schemas.trainee import TokenResponse, TraineeLogin, TraineeRegister, TraineeUpdate
from app.services import catalog_service, device_sessions, user_registry_service
from app.services.activity_log_service import log_activity
from app.services.device_sessions import Device
from app.services.company_ids import require_tenant_company
from app.utils.validators import read_photo_upload

LOGIN_SCOPE = "trainee-login"   # rate_limit's key prefix for this login's failure counts
# The same words for every failed sign-in - unknown ID, no password set, or a wrong one.
LOGIN_FAILED = "Couldn't sign in. Check your Company ID or Phone No and password."


def lock_key(tenant_id: str, trainee: Trainee) -> str:
    """The failed-sign-in count of one trainee: it follows the account, not the words typed - switching
    between their UID and phone number buys no extra guesses (sign_in_service uses it too)."""
    return f"{tenant_id}:trainee-{trainee.id}"


def register(
    db: Session,
    common_db: Session,
    payload: TraineeRegister,
    background_tasks: BackgroundTasks,
    tenant_id: str,
    ip_address: str | None = None,
    device: Optional[Device] = None,
) -> TokenResponse:
    """Self-registration (no password - see `login`), which also signs the new trainee in on this
    device: the app goes straight on to the session (QR join) or the trainee home."""
    existing = trainee_repository.get_by_phone_or_email(db, payload.phone, payload.email)
    if existing:
        raise bad_request("Trainee with this phone or email already exists")

    # Saved as the master list names them; the zone starts the trainee's ID (models/uid_events.py).
    zone, region = catalog_service.master_zone_region(db, payload.zone, payload.region)
    # The company is the tenant's (user, 2026-10-18) - without one, a company-scoped admin wouldn't
    # see the trainee at all.
    company = require_tenant_company(common_db, tenant_id).stored
    # Saved in the company database and the shared user registry (services/user_registry_service).
    trainee = user_registry_service.register_trainee(
        common_db, db, tenant_id,
        Trainee(**payload.model_dump(exclude={"zone", "region", "deviceId", "deviceName"}), zone=zone, region=region, company=company),
    )

    background_tasks.add_task(ws_manager.broadcast, tenant_id, {"type": "trainee_created", "traineeUid": trainee.traineeUid})

    session = _session_for(trainee, tenant_id, device_sessions.begin(common_db, trainee, tenant_id, device))
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


def login(
    db: Session,
    payload: TraineeLogin,
    tenant_id: str,
    ip_address: str | None = None,
    common_db: Optional[Session] = None,
    device: Optional[Device] = None,
) -> TokenResponse:
    """Company ID (Trainee UID / username) or phone number, plus password. Only a trainee who has a
    password can sign in here; a self-registered one (no password) is signed in once, by `register`."""
    # Only FAILED logins are limited, and only per account (keyed by tenant so one tenant's failures
    # never lock the same account elsewhere) - never per caller IP: a whole classroom shares the
    # venue Wi-Fi's one address.
    trainee = trainee_repository.get_by_login_identifier(db, payload.identifier)
    if trainee is not None and uid_events.is_trainer_uid(trainee.traineeUid):
        trainee = None   # a trainer-shaped ID never signs in as a trainee (uid_events.TRAINER_UID_PREFIX)
    # An identifier that names nobody is counted under its own text.
    account = lock_key(tenant_id, trainee) if trainee else f"{tenant_id}:typed-{payload.identifier}"
    rate_limit.ensure_account_not_locked(LOGIN_SCOPE, account)
    if not (trainee and trainee.password and verify_password(payload.password, trainee.password)):
        rate_limit.record_account_failure(LOGIN_SCOPE, account)
        raise unauthorized(LOGIN_FAILED)
    rate_limit.clear_account_failures(LOGIN_SCOPE, account)
    return signed_in(db, trainee, tenant_id, ip_address, common_db=common_db, device=device)


def signed_in(
    db: Session,
    trainee: Trainee,
    tenant_id: str,
    ip_address: str | None = None,
    *,
    common_db: Optional[Session] = None,
    device: Optional[Device] = None,
) -> TokenResponse:
    """The session for a trainee whose sign-in was just verified, recorded in their company's log. A
    trainee in the central user registry is signed in on this device (services/device_sessions) -
    past their device limit, the one used longest ago is signed out."""
    session_id = device_sessions.begin(common_db, trainee, tenant_id, device) if common_db is not None else None
    session = _session_for(trainee, tenant_id, session_id)
    log_activity(
        db, action="LOGIN", username=str(trainee.phone), role="trainee", ip_address=ip_address,
        issued_token=session.access_token,
    )
    return session


def _session_for(trainee: Trainee, tenant_id: str, session_id: Optional[str] = None) -> TokenResponse:
    """A signed-in session: the token's subject is the phone (`get_current_trainee` looks the trainee up
    by it) and it carries the account's token version, so a logout revokes it, and the device's
    session when there is one."""
    access_token = create_access_token(
        subject=str(trainee.phone), tenant_id=tenant_id, role="trainee", version=trainee.tokenVersion, session_id=session_id
    )
    return TokenResponse(access_token=access_token, trainee=trainee)


def update_me(
    db: Session, common_db: Session, trainee: Trainee, payload: TraineeUpdate, tenant_id: str, session_id: Optional[str] = None
) -> TokenResponse:
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
    # The HO ID is unique across every company - checked before anything is saved.
    if "employee_id" in updates:
        user_registry_service.ensure_available(common_db, hoid=updates["employee_id"], exclude_user_uid=trainee.traineeUid)

    for field, value in updates.items():
        setattr(trainee, field, value)

    trainee_repository.save(db, trainee)
    if {"phone", "employee_id"} & updates.keys():
        user_registry_service.sync_account(common_db, tenant_id, trainee)

    # `get_current_trainee` looks a trainee up by phone (it's the JWT
    # subject), so a changed phone number invalidates the token that was
    # just used to make this request - issue a fresh one so the trainee
    # doesn't get silently logged out by their own edit. Same device, so the same device session.
    return _session_for(trainee, tenant_id, session_id)


async def upload_profile_photo(db: Session, trainee: Trainee, file, tenant_id: str) -> Trainee:
    contents, extension = await read_photo_upload(file, size_error_detail="Image must be 5MB or smaller")

    # Named after the trainee (not the upload), so re-uploading replaces
    # the old file instead of littering the disk with orphans.
    photo_dir = media_subdir("trainee_photos", tenant_id)
    filename = f"{trainee.traineeUid}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    trainee.profilePhoto = f"trainee_photos/{filename}"
    return trainee_repository.save(db, trainee)
