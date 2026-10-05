"""Who may read an uploaded file. Decided per file, from the record that owns it, with the rule the
rest of the app already applies to that record - never "any logged-in user":

    attendance_photos/...        a trainee's check-in photo: that trainee, or whoever may open the
                                 conference (admin grant / assigned trainer - conference_access)
    trainer_checkin_photos/...,  a session's trainer photos and signed attendance sheet: whoever
    trainer_checkout_photos/..., may open that conference
    attendance_sheets/...
    trainee_photos/...           a trainee's profile photo: that trainee, or whoever may see that
                                 trainee (admin grant / assigned-or-rostered trainer)
    trainer_photos/...,          a trainer's / admin's own profile photo and Aadhaar document: only
    admin_profile/...,           the account itself (the Trainer Profile screen is the only place
    trainer_documents/...        they are shown)
    the default avatars          any signed-in account (a shared placeholder, no personal data)

Anything else - an unknown folder, a path no record owns - is refused. Every lookup runs in the
caller's own tenant database, so another tenant's file is never even found."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.media import default_trainer_avatar
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.repositories import attendance_repository, conference_repository, dashboard_repository, trainee_repository
from app.services import conference_access
from app.services.access_service import resolve_scope

SHARED_FILES = frozenset({default_trainer_avatar("male"), default_trainer_avatar("female")})
_CONFERENCE_FILE_FOLDERS = frozenset({"trainer_checkin_photos", "trainer_checkout_photos", "attendance_sheets"})
_ACCOUNT_FILE_FOLDERS = frozenset({"trainer_photos", "admin_profile", "trainer_documents"})
# Every top-level folder an upload can live in (anything else is never served).
KNOWN_FOLDERS = frozenset({"attendance_photos", "trainee_photos"}) | _CONFERENCE_FILE_FOLDERS | _ACCOUNT_FILE_FOLDERS


def can_read(
    db: Session, common_db: Session, principal: Admin | AgencyTeam | Trainee, tenant_id: str, file_path: str
) -> bool:
    if file_path in SHARED_FILES:
        return True
    folder, _, rest = file_path.partition("/")
    if folder == "attendance_photos":
        return _can_read_attendance_photo(db, common_db, principal, tenant_id, file_path, rest)
    if folder == "trainee_photos":
        return _can_read_trainee_photo(db, common_db, principal, tenant_id, file_path)
    if folder in _CONFERENCE_FILE_FOLDERS:
        return not isinstance(principal, Trainee) and conference_repository.get_authorized_by_file(
            db, file_path, dashboard_repository.conference_authorization_conditions(resolve_scope(common_db, principal, tenant_id))
        ) is not None
    if folder in _ACCOUNT_FILE_FOLDERS:
        return _is_own_account_file(principal, file_path)
    return False


def _can_read_attendance_photo(db, common_db, principal, tenant_id: str, file_path: str, rest: str) -> bool:
    record = attendance_repository.get_by_check_in_photo(db, file_path)
    if isinstance(principal, Trainee):
        return record is not None and record.traineeUid == principal.traineeUid
    # Secure check-in stores photos as attendance_photos/<conferenceUid>/<traineeUid>.<ext>; the
    # record says which conference, and the folder does too when no record points at the file.
    conference_uid = record.conferenceUid if record else _conference_folder(rest)
    if not conference_uid:
        return False
    return conference_access.find_authorized_conference(db, principal, conference_uid, common_db, tenant_id) is not None


def _conference_folder(rest: str) -> Optional[str]:
    folder, separator, filename = rest.partition("/")
    return folder if separator and folder and filename and "/" not in filename else None


def _can_read_trainee_photo(db, common_db, principal, tenant_id: str, file_path: str) -> bool:
    if isinstance(principal, Trainee):
        return principal.profilePhoto == file_path
    conditions = dashboard_repository.trainee_authorization_conditions(resolve_scope(common_db, principal, tenant_id))
    return trainee_repository.get_authorized_by_photo(db, file_path, conditions) is not None


def _is_own_account_file(principal, file_path: str) -> bool:
    if isinstance(principal, Trainee):
        return False
    own_files = {getattr(principal, "profilePhoto", None), getattr(principal, "aadharImage", None)}
    return file_path in own_files
