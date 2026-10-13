
"""Creating and editing a training, and the admin's approve / reject decision on it."""

import json
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_SESSION_TITLE
from app.core.exceptions import bad_request, conflict
from app.models.admin import Admin
from app.models.conference import Conference
from app.repositories import catalog_repository, conference_repository
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
from app.services.activity_log_service import log_activity
from app.services.training.common import owned_conference, training_out
from app.utils.status import title_status

# Once a session has actually started, its schedule/venue/session-flow are
# locked in (attendance may already be running against them) - only a
# training that hasn't gone live yet can still have those changed. The admin
# review fields (pax, approval/training status, message) stay editable.
_EDITABLE_CONFERENCE_STATUSES = {"Scheduled", "Pending", "Not Started"}

# Plain PATCH fields -> the conference column each one writes.
_PATCH_COLUMNS = {
    "zone": "zone",
    "region": "region",
    "company": "company",
    "requestedBy": "requestedBy",
    "trainerEmployeeId": "trainerEmployeeId",
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
# Fields that together decide the session flow (sessionConfig, check-in, geofence, module
# question sets, residential type): when any of them is sent they are applied as one unit, the
# way the edit form always sends them.
_SESSION_FLOW_FIELDS = frozenset({"isResidential", "trainingEndDate", "sessionFlow", "venue"})

# The activity-log action each approval decision is recorded as.
_DECISION_ACTIONS = {"Approved": "APPROVE_TRAINING", "Rejected": "REJECT_TRAINING"}


def _session_flow_columns(db: Session, payload: TrainingCreate) -> dict[str, object]:
    """The conference columns the session flow decides - sessionConfig, check-in, geofence, the
    module question sets and the residential type - built the same way on create and on edit."""
    session_config = _session_config(payload)
    attendance_cfg = session_config.get("attendance")
    flow = payload.sessionFlow
    return {
        "conferenceType": "Residential Conference" if payload.isResidential else "Non Residential Conference",
        "enableCheckIn": 1 if attendance_cfg else 0,
        "venueUid": payload.venue,
        **_geofence_columns(db, attendance_cfg, payload.venue),
        "sessionConfig": json.dumps(session_config) if session_config else None,
        # The trainee session flow (see session_service._select_current_conference
        # / get_current_session) only knows a Standard Test or Survey module
        # exists via these two columns - it doesn't read `sessionConfig` for
        # that, so the chosen question set has to be copied out here too,
        # not just stored in the JSON blob above.
        "postAssessmentUid": flow.standardTest.assessmentSuiteUid if flow and flow.standardTest else None,
        "surveyUid": flow.survey.assessmentSuiteUid if flow and flow.survey else None,
    }


def _session_config(payload: TrainingCreate) -> dict[str, object]:
    """The `sessionConfig` JSON: a residential training's end date, plus each module the session
    flow turns on."""
    session_config = {}
    if payload.isResidential and payload.trainingEndDate:
        session_config["trainingEndDate"] = payload.trainingEndDate
    if payload.sessionFlow:
        for key in ("attendance", "standardTest", "liveQuiz", "survey"):
            module_config = getattr(payload.sessionFlow, key)
            if module_config:
                session_config[key] = module_config.model_dump(exclude_none=True)
    return session_config


def _geofence_columns(db: Session, attendance_cfg: Optional[dict], venue_uid: Optional[str]) -> dict[str, object]:
    """Geofenced attendance: pin the check-in radius to the chosen venue's coordinates. Only
    meaningful if geoFencing is on AND the venue has coordinates on record - otherwise the
    coordinates stay NULL and the check-in geofence is simply not enforced."""
    if not (attendance_cfg and attendance_cfg.get("geoFencing")):
        return {"geoLatitude": None, "geoLongitude": None, "geoRadius": None}
    venue = catalog_repository.get_venue_by_uid(db, venue_uid) if venue_uid else None
    pinned = bool(venue and venue.latitude is not None and venue.longitude is not None)
    return {
        "geoLatitude": venue.latitude if pinned else None,
        "geoLongitude": venue.longitude if pinned else None,
        "geoRadius": attendance_cfg.get("geoRadius") or 100,
    }


def create_training(
    db: Session,
    payload: TrainingCreate,
    background_tasks: BackgroundTasks,
    admin: Admin,
    tenant_id: str = None,
    common_db: Optional[Session] = None,
) -> TrainingOut:
    placement_rules.authorize_placement(
        db, common_db, admin, resolve_scope(common_db, admin, tenant_id), tenant_id,
        company=payload.company, zone=payload.zone, region=payload.region, trainer=payload.trainerEmployeeId,
    )

    conference = Conference(
        zone=payload.zone,
        region=payload.region,
        company=payload.company,
        requestedBy=payload.requestedBy,
        trainerEmployeeId=payload.trainerEmployeeId,
        trainerName=payload.trainerName,
        conferenceDate=payload.conferenceDate,
        conferenceTime=payload.conferenceTime,
        conferenceStatus="Scheduled",
        trainingHub=payload.trainingHub,
        audience=payload.audience,
        sessionType=payload.sessionType,
        trainingType=payload.trainingType,
        batchSize=payload.batchSize,
        state=payload.state,
        district=payload.district,
        checklistUid=",".join(payload.checklist) if payload.checklist else None,
        updatedBy=admin.username,
        # Auto-approved on creation for now - the trainer can start it straight
        # away without waiting on an admin review (see approve_training and the
        # check in session_start.start_training).
        status="Approved",
        **_session_flow_columns(db, payload),
    )
    conference = conference_repository.create(db, conference)

    assigned_to = conference.trainerEmployeeId
    for_someone_else = f" for trainer {assigned_to}" if assigned_to and assigned_to != admin.username else ""
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
        conference.trainerEmployeeId,
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
    session_config = json.loads(conference.sessionConfig) if conference.sessionConfig else {}

    session_flow = None
    if session_config:
        session_flow = SessionFlowConfig(
            attendance=AttendanceConfig(**session_config["attendance"]) if session_config.get("attendance") else None,
            standardTest=ModuleConfig(**session_config["standardTest"]) if session_config.get("standardTest") else None,
            liveQuiz=ModuleConfig(**session_config["liveQuiz"]) if session_config.get("liveQuiz") else None,
            survey=ModuleConfig(**session_config["survey"]) if session_config.get("survey") else None,
        )

    venue_name = None
    if conference.venueUid:
        venue = catalog_repository.get_venue_by_uid(db, conference.venueUid)
        venue_name = venue.name if venue else None

    return TrainingDetailOut(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
        zone=conference.zone,
        region=conference.region,
        company=conference.company,
        requestedBy=conference.requestedBy,
        trainerEmployeeId=conference.trainerEmployeeId,
        trainerName=conference.trainerName,
        state=conference.state,
        district=conference.district,
        venue=conference.venueUid,
        venueName=venue_name,
        isResidential=conference.conferenceType == "Residential Conference",
        conferenceDate=conference.conferenceDate,
        conferenceTime=conference.conferenceTime,
        trainingEndDate=session_config.get("trainingEndDate"),
        trainingHub=conference.trainingHub,
        audience=conference.audience,
        sessionType=conference.sessionType,
        trainingType=conference.trainingType,
        batchSize=conference.batchSize,
        sessionFlow=session_flow,
        checklist=conference.checklistUid.split(",") if conference.checklistUid else [],
        conferenceStatus=title_status(conference.conferenceStatus),
        approvalStatus=title_status(conference.status),
        attendanceSheetPax=conference.attendanceSheetPax,
        confirmedPax=conference.confirmedPax,
        remarks=conference.remarks,
        checkInPhoto=conference.startConferenceImage,
        checkOutPhoto=conference.conferenceImage,
        attendanceSheet=conference.attendanceSheet,
        scheduleEditable=conference.conferenceStatus in _EDITABLE_CONFERENCE_STATUSES,
    )


def _apply_schedule_fields(db: Session, conference: Conference, payload: TrainingCreate, sent: set[str]) -> None:
    """Writes only the fields the request sent (`sent` = payload.model_fields_set) - a field left
    out keeps its stored value; one sent as null clears it."""
    for field, column in _PATCH_COLUMNS.items():
        if field in sent:
            setattr(conference, column, getattr(payload, field))
    if "checklist" in sent:
        conference.checklistUid = ",".join(payload.checklist) if payload.checklist else None
    if sent & _SESSION_FLOW_FIELDS:
        for column, value in _session_flow_columns(db, payload).items():
            setattr(conference, column, value)


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

    if conference.conferenceStatus in _EDITABLE_CONFERENCE_STATUSES:
        _update_schedule(db, common_db, admin, conference, payload, tenant_id)

    if payload.confirmedPax is not None:
        conference.confirmedPax = payload.confirmedPax

    message = (payload.message or "").strip()
    decision = _apply_approval_decision(conference, payload.approvalStatus, message)
    _apply_training_status(conference, payload.trainingStatus)
    if message:
        conference.remarks = message

    conference.updatedBy = admin.username
    conference_repository.save(db, conference)

    action, remarks = _update_log_entry(conference.conferenceUid, decision, message)
    log_activity(db, action=action, username=admin.username, role=admin.role, remarks=remarks, reason=message or None)

    if background_tasks:
        background_tasks.add_task(
            ws_manager.send_to,
            tenant_id,
            conference.trainerEmployeeId,
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
    merged = {
        field: getattr(payload, field) if field in sent else getattr(conference, column)
        for field, column in (("company", "company"), ("zone", "zone"), ("region", "region"), ("trainerEmployeeId", "trainerEmployeeId"))
    }
    placement_rules.authorize_placement(
        db, common_db, admin, resolve_scope(common_db, admin, tenant_id), tenant_id,
        company=merged["company"], zone=merged["zone"], region=merged["region"],
        trainer=merged["trainerEmployeeId"], current_trainer=conference.trainerEmployeeId,
    )
    _apply_schedule_fields(db, conference, payload, sent)


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
    if not training_status or training_status == title_status(conference.conferenceStatus):
        return
    # A finished training is final - its status can't be changed to anything else.
    if title_status(conference.conferenceStatus) == "Completed":
        raise conflict("A completed training's status can't be changed")
    conference.conferenceStatus = training_status


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
    if title_status(conference.conferenceStatus) in ("Completed", "Cancelled"):
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
    conference.updatedBy = admin.username
    if reason:
        conference.remarks = reason
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
