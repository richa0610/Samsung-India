
"""Creating and editing a training, and the admin's approve / reject decision on it."""

from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_SESSION_TITLE
from app.core.exceptions import bad_request, conflict
from app.models.admin import Admin
from app.models.conference import Conference
from app.repositories import assessment_repository, catalog_repository, conference_repository
from app.routers.ws import manager as ws_manager
from app.schemas.training import (
    AttendanceConfig,
    ModuleConfig,
    SessionFlowConfig,
    TrainingAdminUpdate,
    TrainingCreate,
    TrainingDetailOut,
    TrainingOut,
)
from app.services import placement_rules
from app.services.access_service import resolve_scope
from app.services.account_ids import account_id, account_keys, account_name, find_account, login_name
from app.services.activity_log_service import log_activity
from app.services.assessment_builder_service import suite_category
from app.services.company_ids import company_name, require_tenant_company
from app.services.training.common import owned_conference, training_out
from app.utils.conference_format import (
    NO_FILE,
    SCHEDULED,
    assigned,
    conference_type,
    creation_note,
    is_cancelled,
    is_completed,
    is_residential,
    read_session_config,
    remark_text,
    session_status,
    stored_or_not_assigned,
    stored_place,
    stored_remark,
    stored_status,
    trainer_label,
    uploaded,
    write_session_config,
)
from app.utils.date_utils import to_stored_time, to_venue_time
from app.utils.places import place_name
from app.utils.status import title_status

# Once a session has actually started, its schedule/venue/session-flow are
# locked in (attendance may already be running against them) - only a
# training that hasn't gone live yet can still have those changed. The admin
# review fields (pax, approval/training status, message) stay editable.
_EDITABLE_CONFERENCE_STATUSES = {"scheduled", "pending", "not started"}

# Plain PATCH fields -> the conference column each one writes. (trainerEmployeeId is stored as
# the trainer's account ID - _apply_trainer; the company is the tenant's and never edited.)
_PATCH_COLUMNS = {
    "zone": "zone",
    "region": "region",
    "requestedBy": "requestedBy",
    "trainerName": "trainerName",
    "conferenceDate": "conferenceDate",
    "conferenceTime": "conferenceTime",
    "trainingHub": "trainingHub",
    "audience": "audience",
    "sessionType": "sessionType",
    "trainingType": "trainingType",
    "batchSize": "batchSize",
    "state": "state",
    "district": "district",
}
# How a sent value is stored where the other system stores it differently (user, 2026-10-17); any
# other field is stored as sent.
_STORED_FORM = {
    "conferenceTime": to_stored_time,
    "state": stored_place,
    "district": stored_place,
    "trainingHub": stored_or_not_assigned,
}
# Fields that together decide the session flow (sessionConfig, check-in, geofence, module
# question sets, residential type): when any of them is sent they are applied as one unit, the
# way the edit form always sends them.
_SESSION_FLOW_FIELDS = frozenset({"isResidential", "trainingEndDate", "sessionFlow", "venue"})

# The activity-log action each approval decision is recorded as.
_DECISION_ACTIONS = {"Approved": "APPROVE_TRAINING", "Rejected": "REJECT_TRAINING"}


def _session_flow_columns(db: Session, payload: TrainingCreate, conference_date: Optional[str]) -> dict[str, object]:
    """The conference columns the session flow decides - sessionConfig, the venue and its location,
    the module question sets, the residential type and the training's last day - built the same
    way on create and on edit, and stored the other system's way (user, 2026-10-17).
    `conference_date` is the training's date as it will be stored (an edit may not send one)."""
    flow = _session_flow(payload)
    sent_flow = payload.sessionFlow
    return {
        "conferenceType": conference_type(payload.isResidential),
        "conferenceEndsOn": _last_day(payload.isResidential, payload.trainingEndDate, conference_date),
        # The other system keeps this 0 and lists the Attendance module in sessionConfig instead
        # (module_flow.configured_modules reads it from there).
        "enableCheckIn": 0,
        "venueUid": stored_or_not_assigned(payload.venue),
        **_venue_location(db, flow.get("attendance"), payload.venue),
        "sessionConfig": write_session_config(flow, conference_date),
        # The trainee session flow (see session_service._select_current_conference
        # / get_current_session) only knows a Standard Test or Survey module
        # exists via these two columns - it doesn't read `sessionConfig` for
        # that, so the chosen question set has to be copied out here too,
        # not just stored in the JSON blob above.
        "postAssessmentUid": sent_flow.standardTest.assessmentSuiteUid if sent_flow and sent_flow.standardTest else None,
        "surveyUid": sent_flow.survey.assessmentSuiteUid if sent_flow and sent_flow.survey else None,
    }


def _session_flow(payload: TrainingCreate) -> dict[str, dict]:
    """Each module the session flow turns on, as this app's session-flow dict."""
    if not payload.sessionFlow:
        return {}
    return {
        key: module_config.model_dump(exclude_none=True)
        for key in ("attendance", "standardTest", "liveQuiz", "survey")
        if (module_config := getattr(payload.sessionFlow, key))
    }


def _last_day(residential: bool, program_end: Optional[str], conference_date: Optional[str]) -> Optional[str]:
    """`conferenceEndsOn` - the training's last planned day: a residential program's end date, else
    the training's own date."""
    return program_end if residential and program_end else conference_date


def _venue_location(db: Session, attendance_cfg: Optional[dict], venue_uid: Optional[str]) -> dict[str, object]:
    """The chosen venue's location, when it has one on record - a training without one takes the
    trainer's at Start Session (session_start). The check-in fence is only enforced with geoFencing
    on (helpers.geofence_enabled); the radius is 100 m unless the flow sets one."""
    venue = catalog_repository.get_venue_by_uid(db, venue_uid) if venue_uid else None
    located = bool(venue and venue.latitude is not None and venue.longitude is not None)
    return {
        "geoLatitude": venue.latitude if located else None,
        "geoLongitude": venue.longitude if located else None,
        "geoRadius": (attendance_cfg or {}).get("geoRadius") or 100,
    }


def create_training(
    db: Session,
    payload: TrainingCreate,
    background_tasks: BackgroundTasks,
    admin: Admin,
    tenant_id: str = None,
    common_db: Optional[Session] = None,
) -> TrainingOut:
    # A training's company is its tenant's (user, 2026-10-18) - never the form's, so a Super Admin
    # working in one company can't file a training under another's name.
    company = require_tenant_company(common_db, tenant_id)
    placement_rules.authorize_placement(
        db, common_db, admin, resolve_scope(common_db, admin, tenant_id), tenant_id,
        company=company.name, zone=payload.zone, region=payload.region, trainer=payload.trainerEmployeeId,
    )

    trainer = find_account(db, common_db, payload.trainerEmployeeId)
    conference = Conference(
        company=company.stored,
        zone=payload.zone,
        region=payload.region,
        requestedBy=payload.requestedBy,
        conferenceDate=payload.conferenceDate,
        conferenceTime=to_stored_time(payload.conferenceTime),
        conferenceStatus=SCHEDULED,
        trainingHub=stored_or_not_assigned(payload.trainingHub),
        audience=payload.audience,
        sessionType=payload.sessionType,
        trainingType=payload.trainingType,
        batchSize=payload.batchSize,
        state=stored_place(payload.state),
        district=stored_place(payload.district),
        checklistUid=",".join(payload.checklist) if payload.checklist else None,
        # Nothing is uploaded yet - marked the way the other system marks it.
        attendanceSheet=NO_FILE,
        hotelBill=NO_FILE,
        conferenceImage=NO_FILE,
        updatedBy=account_id(admin),
        status="Pending",
        remarks=None,
        **_session_flow_columns(db, payload, payload.conferenceDate),
    )
    _apply_trainer(conference, payload, {"trainerEmployeeId"}, trainer)
    conference_repository.add(db, conference)
    conference.masterRemarks = creation_note(
        payload.isResidential, account_name(admin), account_id(admin), conference.conferenceUid
    )
    conference = conference_repository.save(db, conference)

    # The log names the assigned trainer by login name, readable whichever way the row stores them.
    assigned_to = trainer.username if trainer is not None else conference.trainerEmployeeId
    for_someone_else = f" for trainer {assigned_to}" if assigned_to and assigned_to not in account_keys(admin) else ""
    log_activity(
        db,
        action="CREATE_TRAINING",
        username=admin.username,
        role=admin.role,
        remarks=f"Created training {conference.conferenceUid}{for_someone_else}",
    )

    background_tasks.add_task(
        ws_manager.send_to,
        tenant_id,
        trainer.username if trainer is not None else conference.trainerEmployeeId,  # live updates go by login name
        {"type": "training_created", "conferenceUid": conference.conferenceUid},
    )
    background_tasks.add_task(
        ws_manager.broadcast,
        tenant_id,
        {"type": "training_created", "conferenceUid": conference.conferenceUid},
    )

    return training_out(conference)


def get_training_detail(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> TrainingDetailOut:
    """Full editable detail for one training, pre-filled into the admin's
    edit form - the read counterpart to `update_training` below. Same access grant as operating
    the session (`owned_conference`): an out-of-scope training looks absent, not merely
    un-editable."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    flow = read_session_config(conference.sessionConfig)
    session_flow = _form_session_flow(db, conference, flow) if flow else None

    venue_uid = assigned(conference.venueUid)
    venue_name = None
    if venue_uid:
        venue = catalog_repository.get_venue_by_uid(db, venue_uid)
        venue_name = venue.name if venue else None

    return TrainingDetailOut(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
        zone=conference.zone,
        region=conference.region,
        # The form shows the company's name and picks the trainer by login name.
        company=company_name(common_db, conference.company),
        requestedBy=conference.requestedBy,
        trainerEmployeeId=login_name(db, common_db, conference.trainerEmployeeId),
        trainerName=conference.trainerName,
        state=place_name(conference.state) or None,
        district=place_name(conference.district) or None,
        venue=venue_uid,
        venueName=venue_name,
        isResidential=is_residential(conference),
        conferenceDate=conference.conferenceDate,
        conferenceTime=to_venue_time(conference.conferenceTime),
        trainingEndDate=_program_end(conference, flow),
        trainingHub=assigned(conference.trainingHub),
        audience=conference.audience,
        sessionType=conference.sessionType,
        trainingType=conference.trainingType,
        batchSize=conference.batchSize,
        sessionFlow=session_flow,
        checklist=conference.checklistUid.split(",") if conference.checklistUid else [],
        conferenceStatus=session_status(conference.conferenceStatus),
        approvalStatus=title_status(conference.status),
        attendanceSheetPax=conference.attendanceSheetPax,
        confirmedPax=conference.confirmedPax,
        remarks=remark_text(conference.remarks),
        checkInPhoto=uploaded(conference.startConferenceImage),
        checkOutPhoto=uploaded(conference.conferenceImage),
        attendanceSheet=uploaded(conference.attendanceSheet),
        scheduleEditable=_schedule_editable(conference),
    )


def _schedule_editable(conference: Conference) -> bool:
    return (conference.conferenceStatus or "").strip().lower() in _EDITABLE_CONFERENCE_STATUSES


def _form_session_flow(db: Session, conference: Conference, flow: dict) -> SessionFlowConfig:
    """The session flow as the edit form fills it in. The other system's stored list has no picker
    category or check-in radius, so those come from each question set and the conference row."""
    attendance = flow.get("attendance")
    if attendance and attendance.get("geoFencing") and not attendance.get("geoRadius") and conference.geoRadius:
        attendance = {**attendance, "geoRadius": conference.geoRadius}
    return SessionFlowConfig(
        attendance=AttendanceConfig(**attendance) if attendance else None,
        standardTest=_form_module(db, flow.get("standardTest")),
        liveQuiz=_form_module(db, flow.get("liveQuiz")),
        survey=_form_module(db, flow.get("survey")),
    )


def _form_module(db: Session, block: Optional[dict]) -> Optional[ModuleConfig]:
    if not block:
        return None
    if not block.get("category") and block.get("assessmentSuiteUid"):
        suite = assessment_repository.get_suite_by_uid(db, block["assessmentSuiteUid"])
        if suite is not None:
            block = {**block, "category": suite_category(suite)}
    return ModuleConfig(**block)


def _program_end(conference: Conference, flow: dict) -> Optional[str]:
    """A residential program's end date: `conferenceEndsOn` (a row written before kept it in its
    session-flow dict instead)."""
    if not is_residential(conference):
        return None
    return flow.get("trainingEndDate") or conference.conferenceEndsOn


def _apply_trainer(conference: Conference, payload: TrainingCreate, sent: set[str], trainer) -> None:
    """The trainer as the other system stores them (user, 2026-10-17): the account ID and
    "Name (username)" (as sent when no account matches). `trainer` is the account
    `payload.trainerEmployeeId` names."""
    if "trainerEmployeeId" in sent:
        if trainer is None:
            conference.trainerEmployeeId, conference.trainerName = payload.trainerEmployeeId, payload.trainerName
        else:
            conference.trainerEmployeeId = account_id(trainer)
            conference.trainerName = trainer_label(trainer.name, trainer.username)


def _apply_schedule_fields(
    db: Session, common_db: Optional[Session], conference: Conference, payload: TrainingCreate, sent: set[str]
) -> None:
    """Writes only the fields the request sent (`sent` = payload.model_fields_set) - a field left
    out keeps its stored value; one sent as null clears it. Stored the other system's way."""
    for field, column in _PATCH_COLUMNS.items():
        if field in sent:
            value = getattr(payload, field)
            stored_form = _STORED_FORM.get(field)
            setattr(conference, column, stored_form(value) if stored_form else value)
    trainer = find_account(db, common_db, payload.trainerEmployeeId) if "trainerEmployeeId" in sent else None
    _apply_trainer(conference, payload, sent, trainer)
    if "checklist" in sent:
        conference.checklistUid = ",".join(payload.checklist) if payload.checklist else None
    if sent & _SESSION_FLOW_FIELDS:
        for column, value in _session_flow_columns(db, payload, conference.conferenceDate).items():
            setattr(conference, column, value)
    elif "conferenceDate" in sent:
        _follow_new_date(conference)


def _follow_new_date(conference: Conference) -> None:
    """A changed date moves what is stored with it: each module's date in sessionConfig, and the
    training's last day - a residential program keeps its own end date."""
    flow = read_session_config(conference.sessionConfig)
    if flow:
        conference.sessionConfig = write_session_config(flow, conference.conferenceDate)
    conference.conferenceEndsOn = _last_day(is_residential(conference), _program_end(conference, flow), conference.conferenceDate)


def update_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    payload: TrainingAdminUpdate,
    background_tasks: Optional[BackgroundTasks] = None,
    common_db: Session = None,
    tenant_id: str = None,
) -> TrainingOut:
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)

    if _schedule_editable(conference):
        _update_schedule(db, common_db, admin, conference, payload, tenant_id)

    if payload.confirmedPax is not None:
        conference.confirmedPax = payload.confirmedPax

    message = (payload.message or "").strip()
    decision = _apply_approval_decision(conference, payload.approvalStatus, message)
    _apply_training_status(conference, payload.trainingStatus)
    if message:
        conference.remarks = stored_remark(message)

    conference.updatedBy = account_id(admin)
    conference_repository.save(db, conference)

    action, remarks = _update_log_entry(conference.conferenceUid, decision, message)
    log_activity(db, action=action, username=admin.username, role=admin.role, remarks=remarks, reason=message or None)

    if background_tasks:
        background_tasks.add_task(
            ws_manager.send_to,
            tenant_id,
            login_name(db, common_db, conference.trainerEmployeeId),  # live updates go by login name
            {"type": "training_updated", "conferenceUid": conference.conferenceUid},
        )

    return training_out(conference)


def _update_schedule(
    db: Session,
    common_db: Optional[Session],
    admin: Admin,
    conference: Conference,
    payload: TrainingAdminUpdate,
    tenant_id: Optional[str],
) -> None:
    """A PATCH changes only the fields it sends; the training as it WILL be after the change (sent
    values over stored ones) must be inside the caller's grant, and a changed trainer must be one
    they may assign."""
    sent = payload.model_fields_set
    # Checked by name, as grants and the form name them - a stored company / trainer ID reads back
    # as its name / login name, so an unchanged one stays unchanged. The company isn't editable.
    stored_company = company_name(common_db, conference.company)
    stored_trainer = login_name(db, common_db, conference.trainerEmployeeId)
    placement_rules.authorize_placement(
        db, common_db, admin, resolve_scope(common_db, admin, tenant_id), tenant_id,
        company=stored_company,
        zone=payload.zone if "zone" in sent else conference.zone,
        region=payload.region if "region" in sent else conference.region,
        trainer=payload.trainerEmployeeId if "trainerEmployeeId" in sent else stored_trainer,
        current_trainer=stored_trainer,
    )
    _apply_schedule_fields(db, common_db, conference, payload, sent)


def _apply_approval_decision(conference: Conference, approval_status: Optional[str], message: str) -> Optional[str]:
    """Sets a changed approval status and returns it as the decision to log - None when it's
    unchanged. Approving or rejecting needs a message saying why."""
    if not approval_status or approval_status == title_status(conference.status):
        return None
    _ensure_approval_open(conference)
    if approval_status in ("Approved", "Rejected") and not message:
        raise bad_request("Add a message explaining why you are approving or rejecting this training.")
    conference.status = approval_status
    return approval_status


def _apply_training_status(conference: Conference, training_status: Optional[str]) -> None:
    if not training_status or training_status == session_status(conference.conferenceStatus):
        return
    # A finished training is final - its status can't be changed to anything else.
    if is_completed(conference):
        raise conflict("A completed training's status can't be changed")
    conference.conferenceStatus = stored_status(training_status)


def _update_log_entry(conference_uid: str, decision: Optional[str], message: str) -> tuple[str, str]:
    """The activity-log action and remarks for an edit - an approval decision is logged as that
    decision, with its message."""
    if not decision:
        return "UPDATE_TRAINING", f"Updated training {conference_uid}"
    remarks = f"{decision} training {conference_uid}: {message}".rstrip(": ")
    return _DECISION_ACTIONS.get(decision, "UPDATE_TRAINING"), remarks


def _ensure_approval_open(conference: Conference) -> None:
    """Approval is decided before a training runs: a Completed or Cancelled one can't be
    approved or rejected any more."""
    if is_completed(conference) or is_cancelled(conference):
        raise conflict("A completed or cancelled training can't be approved or rejected")


def _decide_approval(
    db: Session,
    admin: Admin,
    conference_uid: str,
    decision: str,
    reason: Optional[str],
    background_tasks: Optional[BackgroundTasks],
    common_db: Optional[Session],
    tenant_id: Optional[str],
) -> TrainingOut:
    """Records an admin's Approved / Rejected decision, with the optional reason as the remark."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _ensure_approval_open(conference)
    conference.status = decision
    conference.updatedBy = account_id(admin)
    if reason:
        conference.remarks = stored_remark(reason)
    conference_repository.save(db, conference)
    summary = f"{decision} training {conference.conferenceUid}"
    log_activity(
        db,
        action=_DECISION_ACTIONS[decision],
        username=admin.username,
        role=admin.role,
        remarks=f"{summary}: {reason}" if reason else summary,
        reason=reason,
    )
    if background_tasks:
        background_tasks.add_task(
            ws_manager.broadcast,
            tenant_id,
            {"type": "training_status_changed", "conferenceUid": conference.conferenceUid},
        )
    return training_out(conference)


def approve_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    reason: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None,
    common_db: Session = None,
    tenant_id: str = None,
) -> TrainingOut:
    return _decide_approval(db, admin, conference_uid, "Approved", reason, background_tasks, common_db, tenant_id)


def reject_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    reason: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None,
    common_db: Session = None,
    tenant_id: str = None,
) -> TrainingOut:
    return _decide_approval(db, admin, conference_uid, "Rejected", reason, background_tasks, common_db, tenant_id)
