from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.core.media import media_subdir
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.repositories import admin_repository
from app.schemas.catalog import SelectOptionOut
from app.schemas.trainer_profile import TrainerProfileOut, TrainerProfileUpdate
from app.utils.validators import validate_image_upload


def _find_trainer(common_db: Session, db: Session, username: str) -> Admin | AgencyTeam | None:
    """Real trainers live in `agencyteam` (tenant DB), not `admin` (Common
    DB) - same fallback the login endpoint uses - check both so this
    doesn't 404 for accounts only seeded into `agencyteam`."""
    trainer = admin_repository.get_admin_by_username_and_role(common_db, username, "trainer")
    if trainer:
        return trainer
    return admin_repository.get_agency_by_username_and_role(db, username, "trainer")


def list_trainers(common_db: Session, db: Session, company: str | None = None) -> list[SelectOptionOut]:
    """Powers the Add Training and New Trainee forms' Trainer ID pickers.
    `label` shows the employee ID alongside the name (e.g.
    "OFF26001 - Aditya Kumar") so trainers sharing a name are still
    distinguishable; `value` stays the login username since that's what
    `trainerEmployeeId` is matched against for ownership, and `name`
    carries the bare name for the "Trainer Name" field to display.

    When `company` is given (the New Trainee form, which maps a trainee to
    one company's trainer) the list is the `agencyteam` trainers of that
    company only. Without it, both the `admin` and `agencyteam` trainer
    rows are merged (the Add Training form's behaviour)."""
    if company:
        trainers = admin_repository.list_agency_trainers(db, company=company)
    else:
        trainers = [
            *admin_repository.list_admin_trainers(common_db),
            *admin_repository.list_agency_trainers(db),
        ]

    seen: set[str] = set()
    options: list[SelectOptionOut] = []
    for trainer in trainers:
        if not trainer.username or trainer.username in seen:
            continue
        seen.add(trainer.username)
        display_name = trainer.name or trainer.username
        employee_id = getattr(trainer, "offerId", None) or trainer.username
        options.append(
            SelectOptionOut(label=f"{employee_id} - {display_name}", value=trainer.username, name=display_name)
        )
    return sorted(options, key=lambda o: o.name or o.label)


def get_trainer_name(common_db: Session, db: Session, username: str) -> dict:
    trainer = _find_trainer(common_db, db, username)
    if not trainer:
        raise not_found("Trainer not found")

    return {"username": trainer.username, "name": trainer.name}


def _admin_to_profile(admin: Admin) -> TrainerProfileOut:
    """Admin-backed login: almost every TrainerProfile field has a real
    matching column on `admin` (see models/admin.py)."""
    return TrainerProfileOut(
        name=admin.name or "",
        email=admin.email or "",
        mobileNumber=str(admin.phone) if admin.phone else "",
        altPhone=str(admin.altPhone) if admin.altPhone else "",
        gender=admin.gender or "",
        dob=admin.dob or "",
        city=admin.localCity or "",
        district=admin.localDistrict or "",
        state=admin.localState or "",
        pincode=admin.localPinCode or "",
        landmark=admin.localLandmark or "",
        permanentSameAsLocal=True,
        aadharNumber=admin.aadharNo or "",
        aadharFile=admin.aadharImage or "",
        profilePicture=admin.profilePhoto or "",
        about=admin.about or "",
        resume=admin.resume or "",
        otherDocument=admin.otherDocument or "",
        facebookUsername=admin.facebook or "",
        twitterUsername=admin.twitter or "",
        instagramUsername=admin.instagram or "",
        linkedinUsername=admin.linkedin or "",
        youtubeUsername=admin.youtube or "",
        github=admin.github or "",
        jobStatus=admin.jobStatus or "",
        joinedOn=admin.joinedOn or "",
        role=admin.role or "",
        designation=admin.designation or "",
        salary=admin.salary or "",
        companyEmail=admin.companyEmail or "",
        visitingCard=admin.visitingCard or "",
        idCard=admin.idCard or "",
        offerLetter=admin.offerLetter or "",
        letterhead=admin.letterHead or "",
        promocode=admin.promoCode or "",
        username=admin.username or "",
        password="",
        remarks=admin.remarks or "",
        agreedToTerms=True,
    )


def _agency_to_profile(agent: AgencyTeam) -> TrainerProfileOut:
    """AgencyTeam-backed login (the real trainers seeded via
    seed_more_trainers.py etc.): that table has no Aadhar/documents/
    social-media/salary/official-docs columns at all, so those fields
    come back blank rather than fabricated."""
    return TrainerProfileOut(
        name=agent.name or "",
        email=agent.email or "",
        mobileNumber=str(agent.phone) if agent.phone else "",
        altPhone=str(agent.altPhone) if agent.altPhone else "",
        gender=agent.gender or "",
        dob=agent.dob or "",
        city=agent.jobCity or "",
        district="",
        state=agent.jobState or "",
        pincode=agent.jobPincode or "",
        landmark="",
        permanentSameAsLocal=True,
        aadharNumber="",
        aadharFile="",
        profilePicture=agent.profilePhoto or "",
        about="",
        resume="",
        otherDocument="",
        facebookUsername="",
        twitterUsername="",
        instagramUsername="",
        linkedinUsername="",
        youtubeUsername="",
        github="",
        jobStatus=agent.status or "",
        joinedOn="",
        role=agent.role or "",
        designation=agent.designation or "",
        salary="",
        companyEmail=agent.officialEmail or "",
        visitingCard="No",
        idCard="No",
        offerLetter="No",
        letterhead="No",
        promocode="No",
        username=agent.username or "",
        password="",
        remarks="",
        agreedToTerms=True,
    )


_ADMIN_FIELD_MAP = {
    "name": "name",
    "email": "email",
    "gender": "gender",
    "dob": "dob",
    "city": "localCity",
    "district": "localDistrict",
    "state": "localState",
    "pincode": "localPinCode",
    "landmark": "localLandmark",
    "aadharNumber": "aadharNo",
    "aadharFile": "aadharImage",
    "profilePicture": "profilePhoto",
    "about": "about",
    "resume": "resume",
    "otherDocument": "otherDocument",
    "facebookUsername": "facebook",
    "twitterUsername": "twitter",
    "instagramUsername": "instagram",
    "linkedinUsername": "linkedin",
    "youtubeUsername": "youtube",
    "github": "github",
    "jobStatus": "jobStatus",
    "joinedOn": "joinedOn",
    "designation": "designation",
    "salary": "salary",
    "companyEmail": "companyEmail",
    "visitingCard": "visitingCard",
    "idCard": "idCard",
    "offerLetter": "offerLetter",
    "letterhead": "letterHead",
    "promocode": "promoCode",
    "username": "username",
    "remarks": "remarks",
}

_AGENCY_FIELD_MAP = {
    "name": "name",
    "email": "email",
    "gender": "gender",
    "dob": "dob",
    "city": "jobCity",
    "state": "jobState",
    "pincode": "jobPincode",
    "profilePicture": "profilePhoto",
    "designation": "designation",
    "companyEmail": "officialEmail",
    "username": "username",
}


def _apply_profile_update(target: Admin | AgencyTeam, updates: dict, field_map: dict) -> None:
    for source, value in updates.items():
        if source == "mobileNumber":
            target.phone = int(value) if value else None
        elif source == "altPhone":
            target.altPhone = int(value) if value else None
        elif source == "password":
            if value:
                target.password = hash_password(value)
        elif source in field_map:
            setattr(target, field_map[source], value)
        # Anything else either isn't persisted anywhere (permanentSameAsLocal,
        # agreedToTerms - no backing column on either table) or has no
        # column on this particular table (e.g. district/landmark/aadhar/
        # documents/social/salary on agencyteam) - silently accepted, not
        # applied, rather than erroring the whole PATCH.


def get_profile(admin: Admin | AgencyTeam) -> TrainerProfileOut:
    if isinstance(admin, Admin):
        return _admin_to_profile(admin)
    return _agency_to_profile(admin)


def update_profile(
    common_db: Session, db: Session, admin: Admin | AgencyTeam, payload: TrainerProfileUpdate
) -> TrainerProfileOut:
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    # Self-service role changes would be a privilege-escalation risk (the
    # Official Info section's form happens to include a `role` field) -
    # never applied here regardless of what's sent.
    updates.pop("role", None)

    if isinstance(admin, Admin):
        _apply_profile_update(admin, updates, _ADMIN_FIELD_MAP)
        # `admin` was loaded from the Common DB (see get_current_admin) -
        # must be saved through that same session, not the tenant one.
        admin_repository.save(common_db, admin)
    else:
        _apply_profile_update(admin, updates, _AGENCY_FIELD_MAP)
        admin_repository.save(db, admin)

    return get_profile(admin)


async def upload_profile_photo(
    common_db: Session, db: Session, admin: Admin | AgencyTeam, file
) -> TrainerProfileOut:
    """Same pattern as the trainee's own profile-photo upload
    (trainee_service.upload_profile_photo): named after the account so a
    re-upload replaces the old file instead of littering the disk with
    orphans. Admin (Common DB) and AgencyTeam (tenant DB) ids come from
    separate auto-increment sequences and can collide, so which table this
    account is in has to be part of the filename."""
    contents = await file.read()
    extension = validate_image_upload(file.content_type, contents, size_error_detail="Image must be 5MB or smaller")

    photo_dir = media_subdir("trainer_photos")
    is_admin = isinstance(admin, Admin)
    filename = f"{'admin' if is_admin else 'agency'}_{admin.id}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    admin.profilePhoto = f"trainer_photos/{filename}"
    if is_admin:
        admin_repository.save(common_db, admin)
    else:
        admin_repository.save(db, admin)

    return get_profile(admin)
