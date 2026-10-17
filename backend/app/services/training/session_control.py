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
from app.utils.conference_format import (
    NO_MODULE,
    SESSION_ENDED,
    STORED_COMPLETED,
    active_module,
    is_completed,
    is_running,
    log_action,
    log_module,
    module_id,
    set_quiz_state,
)
from app.services.account_ids import account_name
from app.services.module_flow import configured_modules, log_module_action
from app.services.training.common import nudge_session_room, owned_conference, training_out
from app.services.training.timeline import activity_log_list
from app.utils.date_utils import ist_now
from app.utils.validators import read_document_upload, read_photo_upload

# A concurrent request changed the session between reading and writing it (see
# conference_repository.claim_active_module / claim_end); this one backs off.
_SESSION_CHANGED = "The session was just changed by another action - refresh and try again"


def _ensure_running(conference: Conference) -> None:
    """Modules can only be opened, stopped or advanced while the session is live."""
    if not is_running(conference):
        raise conflict("Session is not currently running")


def _activate_module(
    db: Session,
    admin: Admin,
    conference: Conference,
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    tenant_id: str,
) -> TrainingOut:
    """Makes `module_key` the live module - the shared last step of Start and Restart, once each
    has checked its own rules. Claimed first, so of two concurrent taps only one opens it."""
    stored_module = module_id(conference, module_key)
    if not conference_repository.claim_active_module(db, conference.conferenceUid, None, stored_module):
        raise conflict(_SESSION_CHANGED)
    conference.activeModuleId = stored_module
    if module_key == "LIVE_QUIZ":
        set_quiz_state(conference, LIVE_QUIZ_STATE_IDLE)
    log_module_action(db, conference, module_key, "STARTED", account_name(admin))
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
) -> TrainingOut:
    """Manually opens one module. The trainer runs the flow forward one
    Start at a time: a module can only be started once the session is live,
    nothing else is running, this module hasn't run yet, and every module
    ahead of it is finished. Powers the per-row Start button on the
    Session Dashboard's Execution Flow."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)
    if active_module(conference):
        raise conflict("Another module is still running - end it first")

    modules = configured_modules(conference)
    if module_key not in modules:
        raise bad_request("That module isn't part of this session's flow")

    logs_by_module: dict[str, set[str]] = defaultdict(set)
    for log in activity_log_list(db, conference.conferenceUid):
        logs_by_module[log_module(log)].add(log_action(log))

    if "STARTED" in logs_by_module[module_key]:
        raise conflict("That module has already run")
    index = modules.index(module_key)
    if any("STOPPED" not in logs_by_module[modules[i]] for i in range(index)):
        raise conflict("Finish the earlier modules first")

    return _activate_module(
        db, admin, conference, conference_uid, module_key, background_tasks, tenant_id
    )


def restart_module(
    db: Session,
    admin: Admin,
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
) -> TrainingOut:
    """Re-opens a module that already ran. Only allowed while no other module
    is currently live (the trainer must end the running one first). Powers
    the per-row Restart button on the Session Dashboard's Execution Flow."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)
    if active_module(conference):
        raise conflict("End the running module before restarting another")

    modules = configured_modules(conference)
    if module_key not in modules:
        raise bad_request("That module isn't part of this session's flow")

    ran_before = any(
        log_action(log) == "STARTED" and log_module(log) == module_key
        for log in activity_log_list(db, conference.conferenceUid)
    )
    if not ran_before:
        raise bad_request("That module hasn't run yet - start it instead")

    return _activate_module(
        db, admin, conference, conference_uid, module_key, background_tasks, tenant_id
    )


def stop_active_module(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
) -> TrainingOut:
    """Force-ends whatever module is currently live, without opening the
    next one - the trainer starts that manually. Never ends the session
    itself (only end_training / the red "End Session" button does that).
    Powers the blue Active Module card's End button."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)
    current = active_module(conference)
    if not current:
        raise conflict("No module is currently running")

    # Claim first (finish_quiz below commits): of two concurrent Stop taps only one stops it.
    if not conference_repository.claim_active_module(db, conference.conferenceUid, conference.activeModuleId, None):
        raise conflict(_SESSION_CHANGED)
    if current == "LIVE_QUIZ":
        live_quiz_service.finish_quiz(db, conference)
    log_module_action(db, conference, current, "STOPPED", account_name(admin))
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
) -> TrainingOut:
    """Hands the session off from its current live module to the next one
    in the configured flow (e.g. Attendance -> Survey), closing out the
    current module's Execution Flow entry and opening the next. Powers the
    trainer's "Next Module" control on the Session Dashboard."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_running(conference)

    modules = configured_modules(conference)
    current = active_module(conference)
    next_module = None
    if current in modules:
        next_index = modules.index(current) + 1
        if next_index < len(modules):
            next_module = modules[next_index]

    # Claim the move first - before anything is logged or scored (finish_quiz commits) - so of two
    # concurrent Next taps only one advances the flow.
    stored_next = module_id(conference, next_module)
    stored_current = conference.activeModuleId if current else None
    if not conference_repository.claim_active_module(db, conference.conferenceUid, stored_current, stored_next):
        raise conflict(_SESSION_CHANGED)
    if current:
        log_module_action(db, conference, current, "STOPPED", account_name(admin))

    # Score the Live Quiz the moment the flow leaves it (finish_quiz is
    # idempotent, so end_training re-calling it is harmless).
    if current == "LIVE_QUIZ":
        live_quiz_service.finish_quiz(db, conference)

    conference.activeModuleId = stored_next
    if next_module == "LIVE_QUIZ":
        set_quiz_state(conference, LIVE_QUIZ_STATE_IDLE)
    if next_module:
        log_module_action(db, conference, next_module, "STARTED", account_name(admin))

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
) -> TrainingOut:
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    if is_completed(conference):
        raise conflict("This session has already ended")
    # Only a session that was started (by its trainer or an admin - start_training) can be ended; a
    # Scheduled one is cancelled instead, never "ended" without having run.
    if not is_running(conference):
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
    if not conference_repository.claim_end(db, conference.conferenceUid):
        raise conflict("This session has already ended")

    # Stored the other system's way (user, 2026-10-17): the training's own folder, named by when.
    ended_at = ist_now()
    folder = media_subdir(conference.conferenceUid, tenant_id)
    stamp = ended_at.strftime("%Y%m%d%H%M%S")
    photo_name = f"Host_CHECKIN_CLOSE_{stamp}.{photo_ext}"
    (folder / photo_name).write_bytes(photo_bytes)
    conference.conferenceImage = f"{conference.conferenceUid}/{photo_name}"
    sheet_name = f"Host_AttendanceSheet_{stamp}.{sheet_ext}"
    (folder / sheet_name).write_bytes(sheet_bytes)
    conference.attendanceSheet = f"{conference.conferenceUid}/{sheet_name}"

    running = active_module(conference)
    if running:
        if running == "LIVE_QUIZ":
            live_quiz_service.finish_quiz(db, conference)
        log_module_action(db, conference, running, "STOPPED", account_name(admin))
    conference.activeModuleId = NO_MODULE
    log_module_action(db, conference, None, SESSION_ENDED, account_name(admin))

    conference.conferenceStatus = STORED_COMPLETED
    conference.actualEndedAt = ended_at
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
