"""Running a live session: the trainer opens, re-opens, stops and advances its modules one at a time,
then ends it with a check-out photo and the signed attendance sheet. Each move is claimed atomically
first (conference_repository.claim_active_module / claim_end), so of two concurrent taps only one
takes effect."""

from collections import defaultdict

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.core.constants import LIVE_QUIZ_STATE_IDLE
from app.core.exceptions import bad_request, conflict
from app.core.media import media_subdir
from app.models.admin import Admin
from app.models.conference import Conference
from app.repositories import conference_repository
from app.schemas.training import TrainingOut
from app.services import live_quiz_service
from app.services.activity_log_service import log_activity
from app.services.module_flow import configured_modules, log_module_action, trainer_position
from app.services.training.common import nudge_session_room, owned_conference, training_out
from app.services.training.timeline import activity_log_list
from app.utils.date_utils import utc_now
from app.utils.status import title_status
from app.utils.validators import read_document_upload, read_photo_upload

# A concurrent request changed the session between reading and writing it (see
# conference_repository.claim_active_module / claim_end); this one backs off.
_SESSION_CHANGED = "The session was just changed by another action - refresh and try again"


def _ensure_running(conference: Conference) -> None:
    """Modules can only be opened, stopped or advanced while the session is live."""
    if conference.conferenceStatus != "Ongoing":
        raise conflict("Session is not currently running")


def _activate_module(
    db: Session,
    admin: Admin,
    conference: Conference,
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    tenant_id: str,
    latitude: float | None,
    longitude: float | None,
) -> TrainingOut:
    """Makes `module_key` the live module - the shared last step of Start and Restart, once each
    has checked its own rules. Claimed first, so of two concurrent taps only one opens it."""
    if not conference_repository.claim_active_module(db, conference.conferenceUid, None, module_key):
        raise conflict(_SESSION_CHANGED)
    conference.activeModuleId = module_key
    if module_key == "LIVE_QUIZ":
        conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    log_module_action(
        db, conference.conferenceUid, module_key, "STARTED", admin.username,
        **trainer_position(conference, latitude, longitude),
    )
    conference_repository.save(db, conference)
    nudge_session_room(background_tasks, conference_uid, tenant_id)
    return training_out(conference)


def start_module(
    db: Session,
    admin: Admin,
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> TrainingOut:
    """Manually opens one module. The trainer runs the flow forward one
    Start at a time: a module can only be started once the session is live,
    nothing else is running, this module hasn't run yet, and every module
    ahead of it is finished. Powers the per-row Start button on the
    Session Dashboard's Execution Flow."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)
    if conference.activeModuleId:
        raise conflict("Another module is still running - end it first")

    modules = configured_modules(conference)
    if module_key not in modules:
        raise bad_request("That module isn't part of this session's flow")

    logs_by_module: dict[str, set[str]] = defaultdict(set)
    for log in activity_log_list(db, conference.conferenceUid):
        logs_by_module[log.moduleId].add(log.action)

    if "STARTED" in logs_by_module[module_key]:
        raise conflict("That module has already run")
    index = modules.index(module_key)
    if any("STOPPED" not in logs_by_module[modules[i]] for i in range(index)):
        raise conflict("Finish the earlier modules first")

    return _activate_module(
        db, admin, conference, conference_uid, module_key, background_tasks, tenant_id, latitude, longitude
    )


def restart_module(
    db: Session,
    admin: Admin,
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> TrainingOut:
    """Re-opens a module that already ran. Only allowed while no other module
    is currently live (the trainer must end the running one first). Powers
    the per-row Restart button on the Session Dashboard's Execution Flow."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)
    if conference.activeModuleId:
        raise conflict("End the running module before restarting another")

    modules = configured_modules(conference)
    if module_key not in modules:
        raise bad_request("That module isn't part of this session's flow")

    ran_before = any(
        log.action == "STARTED" and log.moduleId == module_key
        for log in activity_log_list(db, conference.conferenceUid)
    )
    if not ran_before:
        raise bad_request("That module hasn't run yet - start it instead")

    return _activate_module(
        db, admin, conference, conference_uid, module_key, background_tasks, tenant_id, latitude, longitude
    )


def stop_active_module(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> TrainingOut:
    """Force-ends whatever module is currently live, without opening the
    next one - the trainer starts that manually. Never ends the session
    itself (only end_training / the red "End Session" button does that).
    Powers the blue Active Module card's End button."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)
    if not conference.activeModuleId:
        raise conflict("No module is currently running")

    current = conference.activeModuleId
    # Claim first (finish_quiz below commits): of two concurrent Stop taps only one stops it.
    if not conference_repository.claim_active_module(db, conference.conferenceUid, current, None):
        raise conflict(_SESSION_CHANGED)
    if current == "LIVE_QUIZ":
        live_quiz_service.finish_quiz(db, conference)
    log_module_action(
        db, conference.conferenceUid, current, "STOPPED", admin.username,
        **trainer_position(conference, latitude, longitude),
    )
    conference.activeModuleId = None
    conference_repository.save(db, conference)
    nudge_session_room(background_tasks, conference_uid, tenant_id)

    return training_out(conference)


def advance_module(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> TrainingOut:
    """Hands the session off from its current live module to the next one
    in the configured flow (e.g. Attendance -> Survey), closing out the
    current module's Execution Flow entry and opening the next. Powers the
    trainer's "Next Module" control on the Session Dashboard."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)

    modules = configured_modules(conference)
    current = conference.activeModuleId
    next_module = None
    if current in modules:
        next_index = modules.index(current) + 1
        if next_index < len(modules):
            next_module = modules[next_index]

    # Claim the move first - before anything is logged or scored (finish_quiz commits) - so of two
    # concurrent Next taps only one advances the flow.
    if not conference_repository.claim_active_module(db, conference.conferenceUid, current, next_module):
        raise conflict(_SESSION_CHANGED)
    if current:
        log_module_action(
            db, conference.conferenceUid, current, "STOPPED", admin.username,
            **trainer_position(conference, latitude, longitude),
        )

    # Score the Live Quiz the moment the flow leaves it (finish_quiz is
    # idempotent, so end_training re-calling it is harmless).
    if current == "LIVE_QUIZ":
        live_quiz_service.finish_quiz(db, conference)

    conference.activeModuleId = next_module
    if next_module == "LIVE_QUIZ":
        conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    if next_module:
        log_module_action(
            db, conference.conferenceUid, next_module, "STARTED", admin.username,
            **trainer_position(conference, latitude, longitude),
        )

    conference_repository.save(db, conference)
    nudge_session_room(background_tasks, conference_uid, tenant_id)

    return training_out(conference)


async def end_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    photo: UploadFile,
    attendance_sheet: UploadFile,
    total_pax: int,
    common_db: Session = None,
    tenant_id: str = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> TrainingOut:
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    if conference.conferenceEndsOn is not None:
        raise conflict("This session has already ended")
    # Only a session that was started (by its trainer or an admin - start_training sets Ongoing)
    # can be ended; a Scheduled one is cancelled instead, never "ended" without having run.
    if title_status(conference.conferenceStatus) != "Ongoing":
        raise conflict("This session hasn't been started yet")
    if total_pax < 0:
        raise bad_request("Total Pax can't be negative")

    # Security Check-Out: the trainer captures a face photo and attaches the
    # signed attendance sheet - both required to close the session. Validated
    # before any state change so a bad upload leaves the session running.
    photo_bytes, photo_ext = await read_photo_upload(photo, size_error_detail="Photo must be 5MB or smaller")
    sheet_bytes, sheet_ext = await read_document_upload(
        attendance_sheet, size_error_detail="Attendance sheet must be 5MB or smaller"
    )

    # Claim the end atomically before writing anything: of two concurrent End requests only one
    # proceeds (same transaction - a failed write below rolls the claim back).
    ends_on = utc_now().strftime("%Y-%m-%d %H:%M:%S")
    if not conference_repository.claim_end(db, conference.conferenceUid, ends_on):
        raise conflict("This session has already ended")

    photo_dir = media_subdir("trainer_checkout_photos", tenant_id)
    (photo_dir / f"{conference.conferenceUid}.{photo_ext}").write_bytes(photo_bytes)
    conference.conferenceImage = f"trainer_checkout_photos/{conference.conferenceUid}.{photo_ext}"

    sheet_dir = media_subdir("attendance_sheets", tenant_id)
    (sheet_dir / f"{conference.conferenceUid}.{sheet_ext}").write_bytes(sheet_bytes)
    conference.attendanceSheet = f"attendance_sheets/{conference.conferenceUid}.{sheet_ext}"

    if conference.activeModuleId:
        if conference.activeModuleId == "LIVE_QUIZ":
            live_quiz_service.finish_quiz(db, conference)
        log_module_action(
            db, conference.conferenceUid, conference.activeModuleId, "STOPPED", admin.username,
            **trainer_position(conference, latitude, longitude),
        )
        conference.activeModuleId = None
    log_module_action(
        db, conference.conferenceUid, None, "SESSION_ENDED", admin.username,
        **trainer_position(conference, latitude, longitude),
    )

    conference.conferenceEndsOn = ends_on
    conference.conferenceStatus = "Completed"
    conference.actualEndedAt = utc_now()
    conference.confirmedPax = str(total_pax)
    conference_repository.save(db, conference)
    nudge_session_room(background_tasks, conference_uid, tenant_id)

    log_activity(
        db,
        action="END_SESSION",
        username=admin.username,
        role=admin.role,
        remarks=f"Ended session {conference.conferenceUid}",
        file_path=f"{conference.conferenceImage}, {conference.attendanceSheet}",
    )

    return training_out(conference)
