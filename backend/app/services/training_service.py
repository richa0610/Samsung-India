import json
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Optional

from fastapi import BackgroundTasks, HTTPException, UploadFile, status as http_status
from sqlalchemy.orm import Session

from app.core.constants import LIVE_QUIZ_STATE_IDLE, MODULE_LABELS, PASS_THRESHOLD_PERCENT
from app.core.exceptions import bad_request, conflict, forbidden, not_found
from app.core.media import media_subdir
from app.models.admin import Admin
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.repositories import (
    activity_log_repository,
    admin_repository,
    assessment_repository,
    attendance_repository,
    catalog_repository,
    conference_repository,
    trainee_repository,
)
from app.routers.ws import manager as ws_manager
from app.utils.date_utils import to_utc_iso
from app.utils.helpers import geofence_enabled, within_geofence
from app.utils.status import title_status
from app.utils.validators import validate_document_upload, validate_image_upload
from app.schemas.training import (
    AssessmentSummary,
    AttendanceListItemOut,
    AttendanceMarkRequest,
    AudienceBreakdown,
    AuditLogEntry,
    ExecutionFlowItem,
    PendingSessionItem,
    ProctoringUnlockRequest,
    SessionDashboardOut,
    SessionHeroStat,
    SessionReportOut,
    SessionReportParticipant,
    SessionReportSummary,
    TopPerformer,
    TraineeRow,
    TrainerAgendaResponse,
    TrainingAgendaItem,
    TrainingCreate,
    TrainingOut,
)
from app.services import live_quiz_service
from app.services.module_flow import (
    auto_advance_if_due,
    configured_modules,
    live_quiz_suite_uid,
    log_module_action,
)


def _execution_flow(db: Session, conference: Conference) -> list[ExecutionFlowItem]:
    modules = configured_modules(conference)
    if not modules:
        return []

    logs = activity_log_list(db, conference.conferenceUid)
    logs_by_module: dict[str, list[ConferenceActivityLog]] = {}
    for log in logs:
        logs_by_module.setdefault(log.moduleId, []).append(log)

    now = datetime.now()
    items: list[ExecutionFlowItem] = []
    for module_key in modules:
        module_logs = logs_by_module.get(module_key, [])
        starts = [entry for entry in module_logs if entry.action == "STARTED"]
        stops = [entry for entry in module_logs if entry.action == "STOPPED"]

        # A module can run more than once (Restart), so compare counts rather
        # than "has a STARTED / has a STOPPED": more starts than stops means
        # it's live right now; the latest pair is the run we report on.
        if len(starts) > len(stops):
            item_status = "Running"
            first_started = starts[0]
            last_started = starts[-1]
            elapsed = int((now - last_started.timestamp).total_seconds())
            started_at = to_utc_iso(first_started.timestamp)
            ended_at = None
        elif starts:
            item_status = "Completed"
            first_started = starts[0]
            last_stopped = stops[-1]
            elapsed = int((last_stopped.timestamp - starts[-1].timestamp).total_seconds())
            started_at = to_utc_iso(first_started.timestamp)
            ended_at = to_utc_iso(last_stopped.timestamp)
        else:
            item_status = "Pending"
            elapsed = None
            started_at = None
            ended_at = None

        items.append(
            ExecutionFlowItem(
                moduleKey=module_key,
                label=MODULE_LABELS.get(module_key, module_key.title()),
                status=item_status,
                startedAt=started_at,
                endedAt=ended_at,
                elapsedSeconds=elapsed,
            )
        )

    # `canStart`: session live, nothing else running, this module hasn't run
    # yet, every module ahead of it is done - the trainer walks the flow
    # forward one manual Start at a time.
    # `canRestart`: a finished module can be re-run, but only while no other
    # module is currently live.
    session_idle = conference.conferenceStatus == "Ongoing" and conference.activeModuleId is None
    for index, item in enumerate(items):
        item.canStart = (
            session_idle
            and item.status == "Pending"
            and all(earlier.status == "Completed" for earlier in items[:index])
        )
        item.canRestart = session_idle and item.status == "Completed"
    return items


def activity_log_list(db: Session, conference_uid: str) -> list[ConferenceActivityLog]:
    return activity_log_repository.list_for_conference(db, conference_uid)


def _suite_for_module(conference: Conference, module_key: str) -> Optional[str]:
    """Which assessment suite a module runs against. Only STANDARD_TEST and
    LIVE_QUIZ have one."""
    if module_key == "STANDARD_TEST":
        return conference.postAssessmentUid
    if module_key == "LIVE_QUIZ":
        return live_quiz_suite_uid(conference)
    return None


def _active_module_question_count(db: Session, conference: Conference) -> Optional[int]:
    """Question count of the currently-live module's suite - drives the
    "Targeted N QPs" pill on the Active Module card."""
    suite_uid = _suite_for_module(conference, conference.activeModuleId or "")
    if not suite_uid:
        return None
    return assessment_repository.count_questions_for_suite(db, suite_uid)


def _session_heroes(db: Session, conference: Conference) -> list[SessionHeroStat]:
    """Per-module quiz/test summary (participants, average %, best %, top
    scorer) for the Session Heroes cards - from the latest attempt each
    trainee made on that module's suite."""
    hero_modules = [m for m in ("LIVE_QUIZ", "STANDARD_TEST") if m in configured_modules(conference)]
    if not hero_modules:
        return []

    all_results = assessment_repository.list_results_for_conferences(db, [conference.conferenceUid])
    latest_by_suite: dict[str, dict[str, object]] = {}
    for r in all_results:  # ordered attemptNumber desc -> first seen per trainee is latest
        latest_by_suite.setdefault(r.assessmentSuiteUid, {}).setdefault(r.traineeUid, r)

    per_module = []
    for module_key in hero_modules:
        suite_uid = _suite_for_module(conference, module_key)
        rows = list(latest_by_suite.get(suite_uid, {}).values()) if suite_uid else []
        best = max(rows, key=lambda r: float(r.percentage)) if rows else None
        per_module.append((module_key, rows, best))

    best_uids = {best.traineeUid for _, _, best in per_module if best}
    names = (
        {t.traineeUid: t.name for t in trainee_repository.get_by_uids(db, best_uids)} if best_uids else {}
    )

    heroes: list[SessionHeroStat] = []
    for module_key, rows, best in per_module:
        pcts = [float(r.percentage) for r in rows]
        heroes.append(
            SessionHeroStat(
                moduleKey=module_key,
                label=MODULE_LABELS.get(module_key, module_key),
                participants=len(rows),
                averagePercent=round(sum(pcts) / len(pcts), 1) if pcts else 0.0,
                bestPercent=round(max(pcts), 1) if pcts else 0.0,
                topName=names.get(best.traineeUid) if best else None,
            )
        )
    return heroes


def _pair_runs(
    module_logs: list[ConferenceActivityLog],
) -> list[tuple[ConferenceActivityLog, Optional[ConferenceActivityLog]]]:
    """Turns a module's chronological STARTED/STOPPED events into
    (started, stopped) run pairs - a module can run more than once if
    `advance-module` ever cycles back around to it."""
    runs: list[tuple[ConferenceActivityLog, Optional[ConferenceActivityLog]]] = []
    open_start: Optional[ConferenceActivityLog] = None
    for log in module_logs:
        if log.action == "STARTED":
            if open_start is not None:
                runs.append((open_start, None))
            open_start = log
        elif log.action == "STOPPED" and open_start is not None:
            runs.append((open_start, log))
            open_start = None
    if open_start is not None:
        runs.append((open_start, None))
    return runs


def _resolve_performer_names(db: Session, usernames: set[str]) -> dict[str, str]:
    if not usernames:
        return {}
    names: dict[str, str] = {}
    for admin in admin_repository.get_admins_by_usernames(db, usernames):
        names[admin.username] = admin.name or admin.username
    remaining = usernames - names.keys()
    if remaining:
        for agent in admin_repository.get_agents_by_usernames(db, remaining):
            names[agent.username] = agent.name or agent.username
    return names


def _audit_log(db: Session, conference: Conference) -> list[AuditLogEntry]:
    modules = configured_modules(conference)
    if not modules:
        return []

    logs = activity_log_list(db, conference.conferenceUid)
    logs_by_module: dict[str, list[ConferenceActivityLog]] = {}
    for log in logs:
        logs_by_module.setdefault(log.moduleId, []).append(log)

    performer_names = _resolve_performer_names(db, {log.performedBy for log in logs if log.performedBy})

    now = datetime.now()
    entries: list[AuditLogEntry] = []
    for module_key in modules:
        runs = _pair_runs(logs_by_module.get(module_key, []))
        for run_number, (started, stopped) in enumerate(runs, start=1):
            end_point = stopped.timestamp if stopped else now
            elapsed = int((end_point - started.timestamp).total_seconds())
            entries.append(
                AuditLogEntry(
                    moduleKey=module_key,
                    label=MODULE_LABELS.get(module_key, module_key.title()),
                    runNumber=run_number,
                    startedAt=to_utc_iso(started.timestamp),
                    endedAt=to_utc_iso(stopped.timestamp) if stopped else None,
                    elapsedSeconds=elapsed,
                    isRunning=stopped is None,
                    startedBy=performer_names.get(started.performedBy, started.performedBy) if started.performedBy else None,
                )
            )
    return entries


def create_training(db: Session, payload: TrainingCreate, background_tasks: BackgroundTasks, admin: Admin) -> TrainingOut:
    session_config = {}
    if payload.isResidential and payload.trainingEndDate:
        session_config["trainingEndDate"] = payload.trainingEndDate
    if payload.sessionFlow:
        if payload.sessionFlow.attendance:
            session_config["attendance"] = payload.sessionFlow.attendance.model_dump(exclude_none=True)
        if payload.sessionFlow.standardTest:
            session_config["standardTest"] = payload.sessionFlow.standardTest.model_dump(exclude_none=True)
        if payload.sessionFlow.liveQuiz:
            session_config["liveQuiz"] = payload.sessionFlow.liveQuiz.model_dump(exclude_none=True)
        if payload.sessionFlow.survey:
            session_config["survey"] = payload.sessionFlow.survey.model_dump(exclude_none=True)

    # Geofenced attendance: pin the check-in radius to the chosen venue's
    # coordinates. Only meaningful if geoFencing is on AND the venue has
    # coordinates on record - otherwise the columns stay NULL and the check-in
    # geofence is simply not enforced.
    geo_latitude = geo_longitude = None
    geo_radius = None
    attendance_cfg = session_config.get("attendance")
    if attendance_cfg and attendance_cfg.get("geoFencing"):
        geo_radius = attendance_cfg.get("geoRadius") or 100
        if payload.venue:
            venue = catalog_repository.get_venue_by_uid(db, payload.venue)
            if venue and venue.latitude is not None and venue.longitude is not None:
                geo_latitude = venue.latitude
                geo_longitude = venue.longitude

    conference = Conference(
        zone=payload.zone,
        region=payload.region,
        company=payload.company,
        requestedBy=payload.requestedBy,
        trainerEmployeeId=payload.trainerEmployeeId,
        trainerName=payload.trainerName,
        conferenceType="Residential Conference" if payload.isResidential else "Non Residential Conference",
        conferenceDate=payload.conferenceDate,
        conferenceTime=payload.conferenceTime,
        conferenceStatus="Scheduled",
        enableCheckIn=1 if session_config.get("attendance") else 0,
        trainingHub=payload.trainingHub,
        audience=payload.audience,
        sessionType=payload.sessionType,
        trainingType=payload.trainingType,
        batchSize=payload.batchSize,
        state=payload.state,
        district=payload.district,
        venueUid=payload.venue,
        geoLatitude=geo_latitude,
        geoLongitude=geo_longitude,
        geoRadius=geo_radius,
        checklistUid=",".join(payload.checklist) if payload.checklist else None,
        sessionConfig=json.dumps(session_config) if session_config else None,
        # The trainee session flow (see session_service._select_current_conference
        # / get_current_session) only knows a Standard Test or Survey module
        # exists via these two columns - it doesn't read `sessionConfig` for
        # that, so the chosen question set has to be copied out here too,
        # not just stored in the JSON blob above.
        postAssessmentUid=payload.sessionFlow.standardTest.assessmentSuiteUid
        if payload.sessionFlow and payload.sessionFlow.standardTest
        else None,
        surveyUid=payload.sessionFlow.survey.assessmentSuiteUid
        if payload.sessionFlow and payload.sessionFlow.survey
        else None,
        updatedBy=admin.username,
        # Every new training needs an admin to review and approve it (see
        # list_pending_trainings + approve_training) before the trainer can
        # start it - see the check in start_training.
        status="Pending",
    )
    conference = conference_repository.create(db, conference)

    background_tasks.add_task(
        ws_manager.send_to,
        conference.trainerEmployeeId,
        {"type": "training_created", "conferenceUid": conference.conferenceUid},
    )

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def _get_owned_conference(db: Session, admin: Admin, conference_uid: str) -> Conference:
    conference = conference_repository.get_owned_by_trainer(db, admin.username, conference_uid)
    if not conference:
        raise not_found("Training not found")
    return conference


def _real_trainee_uids_by_conference(db: Session, conference_uids: list[str]) -> dict[str, set[str]]:
    """Real headcount per conference - the same "who actually showed up or
    attempted the test" definition used by the single-session dashboard
    (see `_build_dashboard`) - rather than the planned `batchSize` field,
    which is just whatever capacity number the trainer typed in at
    creation time and never reflects who was actually trained."""
    by_conference: dict[str, set[str]] = defaultdict(set)
    if not conference_uids:
        return by_conference

    for conference_uid, trainee_uid in attendance_repository.list_present_pairs(db, conference_uids):
        by_conference[conference_uid].add(trainee_uid)

    for conference_uid, trainee_uid in assessment_repository.list_submitted_pairs(db, conference_uids):
        by_conference[conference_uid].add(trainee_uid)

    return by_conference


def _venue_names_for(db: Session, conferences: list[Conference]) -> dict[str, str]:
    venue_uids = {c.venueUid for c in conferences if c.venueUid}
    if not venue_uids:
        return {}
    return {v.venueUid: v.name for v in catalog_repository.get_venues_by_uids(db, venue_uids) if v.name}


def _updated_by_names_for(db: Session, conferences: list[Conference]) -> dict[str, str]:
    """`conference.updatedBy` stores whoever last saved the row as a bare
    username (a trainer's phone number, or an admin's login) - resolve those
    to display names in one batch, the same way `_venue_names_for` resolves
    venue UIDs. Anything that doesn't match a real admin/agencyteam account
    (old seed-script rows, which stamped the script's filename instead of a
    real username) is left for the caller to fall back to the raw value."""
    usernames = {c.updatedBy for c in conferences if c.updatedBy}
    if not usernames:
        return {}
    names: dict[str, str] = {}
    for admin in admin_repository.get_admins_by_usernames(db, usernames):
        if admin.name:
            names[admin.username] = admin.name
    for agent in admin_repository.get_agents_by_usernames(db, usernames):
        if agent.name:
            names.setdefault(agent.username, agent.name)
    return names


def _to_agenda_item(
    conference: Conference,
    trainee_count: int,
    venue_name_by_uid: dict[str, str],
    updated_by_name_by_username: dict[str, str],
) -> TrainingAgendaItem:
    return TrainingAgendaItem(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or "Training Session",
        trainerName=conference.trainerName,
        hoid=conference.trainerEmployeeId,
        conferenceDate=conference.conferenceDate,
        conferenceTime=conference.conferenceTime,
        conferenceStatus=title_status(conference.conferenceStatus),
        approvalStatus=title_status(conference.status),
        location=", ".join(filter(None, [conference.district, conference.state])) or None,
        batchSize=conference.batchSize,
        trainingType=conference.trainingType,
        state=conference.state,
        district=conference.district,
        trainingHub=conference.trainingHub,
        venueName=venue_name_by_uid.get(conference.venueUid),
        updatedBy=(
            updated_by_name_by_username.get(conference.updatedBy, conference.updatedBy)
            if conference.updatedBy
            else None
        ),
        updationOn=conference.updationOn.strftime("%Y-%m-%d %H:%M:%S") if conference.updationOn else None,
        timestamp=conference.timestamp.strftime("%Y-%m-%d %H:%M:%S") if conference.timestamp else None,
        traineeCount=trainee_count,
    )


def list_trainer_trainings(
    db: Session, admin: Admin, start: Optional[str], end: Optional[str], all_sessions: bool
) -> TrainerAgendaResponse:
    """Powers the trainer's Home agenda, and (with `all_sessions=true`) the
    Training List / Pending Training List / Sessions screens that need this
    trainer's complete history rather than just today. `start`/`end` are
    `YYYY-MM-DD` strings (matching how `conferenceDate` is stored) and are
    compared lexicographically, which sorts correctly for that format.

    With neither `start`/`end` nor `all_sessions` given - the dashboard's
    initial, unfiltered landing view - this deliberately mixes scopes:
    totalSessions/completed/pending only cover TODAY, while totalTrainees is
    an all-time cumulative headcount across every session this trainer has
    ever run ("who have I trained so far" isn't naturally a single-day
    question). As soon as the trainer applies an explicit start/end (or a
    caller asks for `all_sessions`), every number (including totalTrainees)
    is scoped to that range/scope instead."""
    is_default_view = start is None and end is None and not all_sessions

    if all_sessions:
        conferences = conference_repository.list_all_for_trainer(db, admin.username)
    elif is_default_view:
        conferences = conference_repository.list_for_trainer(db, admin.username, exact_date=date.today().isoformat())
    else:
        conferences = conference_repository.list_for_trainer(db, admin.username, start=start, end=end)

    conference_uids = [c.conferenceUid for c in conferences]
    trainee_uids_by_conference = _real_trainee_uids_by_conference(db, conference_uids)
    venue_name_by_uid = _venue_names_for(db, conferences)
    updated_by_name_by_username = _updated_by_names_for(db, conferences)

    result = [
        _to_agenda_item(
            conference,
            len(trainee_uids_by_conference.get(conference.conferenceUid, set())),
            venue_name_by_uid,
            updated_by_name_by_username,
        )
        for conference in conferences
    ]

    if is_default_view:
        # All-time headcount across every session this trainer has ever run,
        # not just today's - a trainee trained last month still counts.
        all_conference_uids = [c.conferenceUid for c in conference_repository.list_all_for_trainer(db, admin.username)]
        trainee_source = _real_trainee_uids_by_conference(db, all_conference_uids)
    else:
        # De-duplicated across every session in the filtered range - a
        # trainee trained in more than one of these sessions still counts once.
        trainee_source = trainee_uids_by_conference

    all_trainee_uids: set[str] = set()
    for uids in trainee_source.values():
        all_trainee_uids |= uids

    total_sessions = len(conferences)
    completed = sum(1 for c in conferences if title_status(c.conferenceStatus) == "Completed")
    # Pending = incoming AND approved: not yet started (excludes Ongoing/Live -
    # that's running right now, not "incoming"), not Completed, and actually
    # Approved (a training still awaiting admin approval, or Rejected, isn't
    # a real incoming session). Was `total_sessions - completed`, which lumped
    # in-progress and not-yet-approved sessions into "Pending" too.
    pending = sum(
        1
        for c in conferences
        if title_status(c.status) == "Approved" and title_status(c.conferenceStatus) not in ("Ongoing", "Live", "Completed")
    )
    executed_percentage = round((completed / total_sessions) * 100) if total_sessions else 0
    pending_percentage = round((pending / total_sessions) * 100) if total_sessions else 0

    # Always all-time, regardless of `start`/`end` - the Recent Sessions card
    # wants "what did I most recently complete", not "what completed within
    # whatever range is currently filtered".
    recent_completed_conferences = conference_repository.list_recent_completed_for_trainer(db, admin.username, 2)
    recent_completed_uids = _real_trainee_uids_by_conference(
        db, [c.conferenceUid for c in recent_completed_conferences]
    )
    recent_venue_name_by_uid = _venue_names_for(db, recent_completed_conferences)
    recent_updated_by_name_by_username = _updated_by_names_for(db, recent_completed_conferences)
    recent_completed = [
        _to_agenda_item(
            conference,
            len(recent_completed_uids.get(conference.conferenceUid, set())),
            recent_venue_name_by_uid,
            recent_updated_by_name_by_username,
        )
        for conference in recent_completed_conferences
    ]

    return TrainerAgendaResponse(
        trainings=result,
        totalTrainees=len(all_trainee_uids),
        totalSessions=total_sessions,
        completed=completed,
        pending=pending,
        executedPercentage=executed_percentage,
        pendingPercentage=pending_percentage,
        recentCompleted=recent_completed,
    )


def list_pending_trainings(db: Session) -> list[PendingSessionItem]:
    """Every trainer's not-yet-reviewed sessions, across all trainers -
    powers the admin dashboard's Pending Approvals list."""
    conferences = conference_repository.list_pending(db)
    return [
        PendingSessionItem(
            conferenceUid=c.conferenceUid,
            title=c.suiteTitle or c.trainingType or "Training Session",
            trainerName=c.trainerName,
            conferenceDate=c.conferenceDate,
            conferenceTime=c.conferenceTime,
            status=title_status(c.status),
        )
        for c in conferences
    ]


def _find_any_conference(db: Session, conference_uid: str) -> Conference:
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")
    return conference


def approve_training(db: Session, admin: Admin, conference_uid: str) -> TrainingOut:
    conference = _find_any_conference(db, conference_uid)
    conference.status = "Approved"
    conference.updatedBy = admin.username
    conference_repository.save(db, conference)
    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def reject_training(db: Session, admin: Admin, conference_uid: str) -> TrainingOut:
    conference = _find_any_conference(db, conference_uid)
    conference.status = "Rejected"
    conference.updatedBy = admin.username
    conference_repository.save(db, conference)
    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def _audience_class(attendance) -> str:
    """ASSIGNED (admin pre-seeded roster) / FRESH (registered via the QR flow) /
    UNASSIGNED (existing trainee who logged in and joined). Written to
    `attendance.sessionMeta` at join time (session_service.join_session);
    legacy rows with no meta fall back to UNASSIGNED."""
    if attendance is None:
        return "UNASSIGNED"
    if attendance.sessionMeta:
        try:
            value = (json.loads(attendance.sessionMeta) or {}).get("audience")
            if value in ("ASSIGNED", "FRESH", "UNASSIGNED"):
                return value
        except (ValueError, TypeError):
            pass
    return "UNASSIGNED"


def _build_dashboard(db: Session, conference: Conference) -> SessionDashboardOut:
    auto_advance_if_due(db, conference)
    conference_uid = conference.conferenceUid

    attendance_rows = attendance_repository.list_for_conference(db, conference_uid)
    # Participants = trainees who joined via QR/link ("Joined") or have a real
    # attendance event ("Present"/"Absent"). The pre-seeded roster "Pending"
    # rows are deliberately excluded - the master list is who actually turned
    # up / signed in, not the whole assigned roster.
    participating_uids = {a.traineeUid for a in attendance_rows if a.status != "Pending"}

    result_rows: list = []
    if conference.postAssessmentUid:
        result_rows = assessment_repository.list_results_for_conference_suite(
            db, conference_uid, conference.postAssessmentUid
        )
    # Keep only the latest attempt per trainee (rows are already ordered by
    # attemptNumber desc, so the first one seen per trainee wins).
    latest_result_by_trainee: dict[str, object] = {}
    for result in result_rows:
        latest_result_by_trainee.setdefault(result.traineeUid, result)

    participant_uids = participating_uids | set(latest_result_by_trainee.keys())
    trainees_by_uid = {t.traineeUid: t for t in trainee_repository.get_by_uids(db, participant_uids)}

    attendance_by_trainee = {a.traineeUid: a for a in attendance_rows}
    audience_by_uid = {uid: _audience_class(attendance_by_trainee.get(uid)) for uid in participant_uids}

    def _row_status(uid: str) -> str:
        att = attendance_by_trainee.get(uid)
        if att is None:
            return "Attempted"
        if att.status == "Present":
            return "Present"
        if att.status == "Absent":
            return "Absent"
        return "Pending"  # "Joined" - on the list, not checked in yet

    def _proctoring(uid: str) -> tuple[bool, int, list[str]]:
        """(isLocked, strikes, log lines) from the trainee's attendance row -
        `isTheftLocked` / `theftAttemptsLeft` / `theftRemarks` (see
        session_service.report_proctoring_lock)."""
        att = attendance_by_trainee.get(uid)
        if att is None:
            return False, 0, []
        logs = [ln for ln in (att.theftRemarks or "").splitlines() if ln.strip()]
        attempts_left = att.theftAttemptsLeft if att.theftAttemptsLeft is not None else 3
        strikes = max(0, min(3, 3 - attempts_left))
        return bool(att.isTheftLocked), strikes, logs

    proctoring_by_uid = {uid: _proctoring(uid) for uid in participant_uids}

    trainee_rows = [
        TraineeRow(
            traineeUid=uid,
            name=trainees_by_uid[uid].name if uid in trainees_by_uid else "Unknown Trainee",
            employeeId=trainees_by_uid[uid].employee_id if uid in trainees_by_uid else None,
            phone=trainees_by_uid[uid].phone if uid in trainees_by_uid else None,
            profilePhoto=trainees_by_uid[uid].profilePhoto if uid in trainees_by_uid else None,
            audienceType=("ASSIGNED" if audience_by_uid.get(uid) == "ASSIGNED" else "NOT ALLOCATED"),
            status=_row_status(uid),
            markedOn=attendance_by_trainee[uid].markedOn if uid in attendance_by_trainee else None,
            checkOutTime=(
                attendance_by_trainee[uid].checkOutTime.strftime("%Y-%m-%d %H:%M:%S")
                if uid in attendance_by_trainee and attendance_by_trainee[uid].checkOutTime
                else None
            ),
            score=(
                f"{float(latest_result_by_trainee[uid].percentage):g}%"
                if uid in latest_result_by_trainee
                else None
            ),
            isLocked=proctoring_by_uid[uid][0],
            proctoringStrikes=proctoring_by_uid[uid][1],
            proctoringLogs=proctoring_by_uid[uid][2],
        )
        for uid in participant_uids
    ]

    # Audience breakdown - all derived from the participant rows above so the
    # card and the Participant Master List can never disagree.
    present_count = sum(1 for r in trainee_rows if r.status == "Present")
    absent_count = sum(1 for r in trainee_rows if r.status == "Absent")
    not_marked_count = sum(1 for r in trainee_rows if r.status not in ("Present", "Absent"))
    assigned_count = sum(1 for a in audience_by_uid.values() if a == "ASSIGNED")
    unassigned_count = sum(1 for a in audience_by_uid.values() if a == "UNASSIGNED")
    fresh_count = sum(1 for a in audience_by_uid.values() if a == "FRESH")

    pass_count = sum(
        1 for r in latest_result_by_trainee.values() if float(r.percentage) >= PASS_THRESHOLD_PERCENT
    )
    fail_count = len(latest_result_by_trainee) - pass_count

    top_performers = sorted(
        latest_result_by_trainee.values(), key=lambda r: float(r.percentage), reverse=True
    )[:5]

    runtime_seconds = None
    if conference.actualStartedAt:
        end_point = conference.actualEndedAt or datetime.now()
        runtime_seconds = int((end_point - conference.actualStartedAt).total_seconds())

    return SessionDashboardOut(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or "Training Session",
        trainingType=conference.trainingType,
        conferenceDate=conference.conferenceDate,
        conferenceTime=conference.conferenceTime,
        trainerName=conference.trainerName,
        location=", ".join(filter(None, [conference.district, conference.state])) or None,
        conferenceStatus=title_status(conference.conferenceStatus),
        approvalStatus=title_status(conference.status),
        activeModuleId=conference.activeModuleId,
        activeModuleQuestionCount=_active_module_question_count(db, conference),
        actualStartedAt=to_utc_iso(conference.actualStartedAt),
        actualEndedAt=to_utc_iso(conference.actualEndedAt),
        runtimeSeconds=runtime_seconds,
        audience=AudienceBreakdown(
            total=len(participant_uids),
            present=present_count,
            absent=absent_count,
            notMarked=not_marked_count,
            assigned=assigned_count,
            unassigned=unassigned_count,
            fresh=fresh_count,
        ),
        assessment=AssessmentSummary(
            **{"pass": pass_count}, fail=fail_count, totalAttempts=len(latest_result_by_trainee)
        ),
        topPerformers=[
            TopPerformer(
                traineeUid=r.traineeUid,
                name=trainees_by_uid[r.traineeUid].name if r.traineeUid in trainees_by_uid else "Unknown Trainee",
                score=float(r.totalScore),
                maxScore=float(r.maxScore),
                percentage=float(r.percentage),
            )
            for r in top_performers
        ],
        trainees=trainee_rows,
        executionFlow=_execution_flow(db, conference),
        auditLog=_audit_log(db, conference),
        sessionHeroes=_session_heroes(db, conference),
        liveStudio=(
            live_quiz_service.build_live_studio(db, conference)
            if conference.activeModuleId == "LIVE_QUIZ"
            else None
        ),
    )


def get_session_dashboard(db: Session, admin: Admin, conference_uid: str) -> SessionDashboardOut:
    conference = _get_owned_conference(db, admin, conference_uid)
    return _build_dashboard(db, conference)


def _report_duration_label(conference: Conference) -> Optional[str]:
    """"09:30 - 11:00" spanning the earliest module start to the latest
    module end in the session flow, falling back to the conference start
    time alone when there's no per-module config."""
    try:
        config = json.loads(conference.sessionConfig) if conference.sessionConfig else {}
    except ValueError:
        config = {}
    times: list[str] = []
    for section in config.values():
        if isinstance(section, dict):
            for field in ("checkInOpens", "startTime", "checkOutCloses", "endTime"):
                value = section.get(field)
                if value:
                    times.append(value)

    def _key(value: str) -> datetime:
        try:
            return datetime.strptime(value, "%I:%M %p")
        except ValueError:
            return datetime.max

    times = sorted({t for t in times if _key(t) is not datetime.max}, key=_key)
    if len(times) >= 2:
        return f"{times[0]} - {times[-1]}"
    return conference.conferenceTime


def get_session_report(db: Session, admin: Admin, conference_uid: str) -> SessionReportOut:
    conference = _get_owned_conference(db, admin, conference_uid)
    # The report is a post-session artifact - only available once the trainer
    # has ended the session (mirrors the disabled "Report" button on the
    # Session Dashboard).
    if title_status(conference.conferenceStatus) != "Completed":
        raise bad_request("The session report is available once the session has ended")

    attendance_by_trainee = {
        a.traineeUid: a for a in attendance_repository.list_for_conference(db, conference_uid)
    }

    def _participants(suite_uid: Optional[str]) -> list[SessionReportParticipant]:
        if not suite_uid:
            return []
        # `list_results_for_conference_suite` returns only Submitted results,
        # newest attempt first - so the first row seen per trainee is their
        # latest completed attempt at this module.
        latest_by_trainee: dict[str, object] = {}
        for result in assessment_repository.list_results_for_conference_suite(db, conference_uid, suite_uid):
            latest_by_trainee.setdefault(result.traineeUid, result)

        trainees_by_uid = {
            t.traineeUid: t for t in trainee_repository.get_by_uids(db, set(latest_by_trainee))
        }

        rows: list[SessionReportParticipant] = []
        for uid, result in latest_by_trainee.items():
            trainee = trainees_by_uid.get(uid)
            attendance = attendance_by_trainee.get(uid)
            check_in = None
            if attendance and attendance.markedOn:
                check_in = attendance.markedOn.split(" ")[-1][:5]
            rows.append(
                SessionReportParticipant(
                    userId=(trainee.employee_id if trainee and trainee.employee_id else uid),
                    name=(trainee.name if trainee else "Unknown Trainee"),
                    role="Participant",
                    checkIn=check_in,
                    checkOut=(
                        attendance.checkOutTime.strftime("%H:%M")
                        if attendance and attendance.checkOutTime
                        else None
                    ),
                    score=f"{float(result.percentage):g}%",
                )
            )
        rows.sort(key=lambda r: r.name.lower())
        return rows

    venue_name = _venue_names_for(db, [conference]).get(conference.venueUid)

    return SessionReportOut(
        summary=SessionReportSummary(
            conferenceId=conference.conferenceUid,
            sessionName=conference.suiteTitle or conference.trainingType or "Training Session",
            date=conference.conferenceDate,
            state=conference.state,
            schedule=", ".join(filter(None, [conference.conferenceDate, conference.conferenceTime])) or None,
            duration=_report_duration_label(conference),
            venueLink=venue_name or ", ".join(filter(None, [conference.district, conference.state])) or None,
        ),
        standardTest=_participants(conference.postAssessmentUid),
        liveQuiz=_participants(live_quiz_suite_uid(conference)),
    )


def _resolve_start_geofence(
    db: Session,
    admin: Admin,
    conference: Conference,
    latitude: float | None,
    longitude: float | None,
    venue_latitude: float | None,
    venue_longitude: float | None,
) -> None:
    """Geofence gate for starting a session.

    - If the trainer supplied `venue_latitude`/`venue_longitude` they've chosen
      to correct the venue location from the "you're not at the venue" prompt:
      persist it onto the venue row and this conference, and skip the check.
    - Else, if the session is geofenced (venue has coordinates + geoFencing on)
      and the trainer's position is outside the radius, raise a 409 the app
      recognises to show that prompt. A session that isn't geofenced starts
      with no location check.
    """
    if venue_latitude is not None and venue_longitude is not None:
        if conference.venueUid:
            venue = catalog_repository.get_venue_by_uid(db, conference.venueUid)
            if venue:
                venue.latitude = venue_latitude
                venue.longitude = venue_longitude
                venue.updatedBy = admin.username
                venue.updationOn = datetime.now()
        conference.geoLatitude = venue_latitude
        conference.geoLongitude = venue_longitude
        return

    if not geofence_enabled(conference):
        return

    # Geofenced session: the trainer's location is mandatory - without it we
    # can't confirm they're at the venue, and skipping the check would be a
    # bypass. The app surfaces this as "turn on location".
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "LOCATION_REQUIRED",
                "message": "Turn on location to start this session - it confirms you're at the venue.",
            },
        )

    within, distance = within_geofence(conference, latitude, longitude)
    if within:
        return

    radius = conference.geoRadius or 100
    raise HTTPException(
        status_code=http_status.HTTP_409_CONFLICT,
        detail={
            "code": "OUTSIDE_VENUE",
            "message": (
                f"You're about {distance:.0f} m from the venue (allowed: {radius} m). "
                "Start the session from the venue, or update the venue location."
            ),
            "distanceMeters": round(distance),
            "radius": radius,
        },
    )


async def start_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    photo: UploadFile,
    background_tasks: BackgroundTasks,
    latitude: float | None = None,
    longitude: float | None = None,
    venue_latitude: float | None = None,
    venue_longitude: float | None = None,
) -> TrainingOut:
    conference = _get_owned_conference(db, admin, conference_uid)
    if conference.conferenceEndsOn is not None:
        raise conflict("This session has already ended")
    if title_status(conference.status) != "Approved":
        raise forbidden("This session hasn't been approved by an admin yet")
    # A session can only be started on (or after) its scheduled date - not
    # ahead of time. `conferenceDate` is stored as "YYYY-MM-DD", so a plain
    # string compare against today's ISO date is correct.
    if conference.conferenceDate and conference.conferenceDate > date.today().isoformat():
        raise bad_request("This session can only be started on its scheduled date")

    _resolve_start_geofence(
        db, admin, conference, latitude, longitude, venue_latitude, venue_longitude
    )

    # The trainer must capture a check-in photo to start the session - same
    # identity-verification idea as the trainee's secure attendance check-in.
    contents = await photo.read()
    extension = validate_image_upload(photo.content_type, contents, size_error_detail="Photo must be 5MB or smaller")
    photo_dir = media_subdir("trainer_checkin_photos")
    filename = f"{conference.conferenceUid}.{extension}"
    (photo_dir / filename).write_bytes(contents)
    conference.startConferenceImage = f"trainer_checkin_photos/{filename}"

    conference.conferenceStatus = "Ongoing"
    if conference.actualStartedAt is None:
        conference.actualStartedAt = datetime.now()

    # Starting the session no longer auto-activates a module - the trainer
    # runs the flow forward one manual Start at a time (start_module), so
    # `activeModuleId` stays None until they tap Start on the first module.
    conference_repository.save(db, conference)
    _nudge_session_room(background_tasks, conference_uid)

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def start_module(
    db: Session, admin: Admin, conference_uid: str, module_key: str, background_tasks: BackgroundTasks
) -> TrainingOut:
    """Manually opens one module. The trainer runs the flow forward one
    Start at a time: a module can only be started once the session is live,
    nothing else is running, this module hasn't run yet, and every module
    ahead of it is finished. Powers the per-row Start button on the
    Session Dashboard's Execution Flow."""
    conference = _get_owned_conference(db, admin, conference_uid)
    if conference.conferenceStatus != "Ongoing":
        raise conflict("Session is not currently running")
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

    conference.activeModuleId = module_key
    if module_key == "LIVE_QUIZ":
        conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    log_module_action(db, conference.conferenceUid, module_key, "STARTED", admin.username)
    conference_repository.save(db, conference)
    _nudge_session_room(background_tasks, conference_uid)

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def restart_module(
    db: Session, admin: Admin, conference_uid: str, module_key: str, background_tasks: BackgroundTasks
) -> TrainingOut:
    """Re-opens a module that already ran. Only allowed while no other module
    is currently live (the trainer must end the running one first). Powers
    the per-row Restart button on the Session Dashboard's Execution Flow."""
    conference = _get_owned_conference(db, admin, conference_uid)
    if conference.conferenceStatus != "Ongoing":
        raise conflict("Session is not currently running")
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

    conference.activeModuleId = module_key
    if module_key == "LIVE_QUIZ":
        conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    log_module_action(db, conference.conferenceUid, module_key, "STARTED", admin.username)
    conference_repository.save(db, conference)
    _nudge_session_room(background_tasks, conference_uid)

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def stop_active_module(
    db: Session, admin: Admin, conference_uid: str, background_tasks: BackgroundTasks
) -> TrainingOut:
    """Force-ends whatever module is currently live, without opening the
    next one - the trainer starts that manually. Never ends the session
    itself (only end_training / the red "End Session" button does that).
    Powers the blue Active Module card's End button."""
    conference = _get_owned_conference(db, admin, conference_uid)
    if conference.conferenceStatus != "Ongoing":
        raise conflict("Session is not currently running")
    if not conference.activeModuleId:
        raise conflict("No module is currently running")

    current = conference.activeModuleId
    if current == "LIVE_QUIZ":
        live_quiz_service.finish_quiz(db, conference)
    log_module_action(db, conference.conferenceUid, current, "STOPPED", admin.username)
    conference.activeModuleId = None
    conference_repository.save(db, conference)
    _nudge_session_room(background_tasks, conference_uid)

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def advance_module(
    db: Session, admin: Admin, conference_uid: str, background_tasks: BackgroundTasks
) -> TrainingOut:
    """Hands the session off from its current live module to the next one
    in the configured flow (e.g. Attendance -> Survey), closing out the
    current module's Execution Flow entry and opening the next. Powers the
    trainer's "Next Module" control on the Session Dashboard."""
    conference = _get_owned_conference(db, admin, conference_uid)
    if conference.conferenceStatus != "Ongoing":
        raise conflict("Session is not currently running")

    modules = configured_modules(conference)
    current = conference.activeModuleId
    if current:
        log_module_action(db, conference.conferenceUid, current, "STOPPED", admin.username)

    next_module = None
    if current in modules:
        next_index = modules.index(current) + 1
        if next_index < len(modules):
            next_module = modules[next_index]

    # Score the Live Quiz the moment the flow leaves it (finish_quiz is
    # idempotent, so end_training re-calling it is harmless).
    if current == "LIVE_QUIZ":
        live_quiz_service.finish_quiz(db, conference)

    conference.activeModuleId = next_module
    if next_module == "LIVE_QUIZ":
        conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    if next_module:
        log_module_action(db, conference.conferenceUid, next_module, "STARTED", admin.username)

    conference_repository.save(db, conference)
    _nudge_session_room(background_tasks, conference_uid)

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


async def end_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    photo: UploadFile,
    attendance_sheet: UploadFile,
) -> TrainingOut:
    conference = _get_owned_conference(db, admin, conference_uid)
    if conference.conferenceEndsOn is not None:
        raise conflict("This session has already ended")

    # Security Check-Out: the trainer captures a face photo and attaches the
    # signed attendance sheet - both required to close the session. Validated
    # before any state change so a bad upload leaves the session running.
    photo_bytes = await photo.read()
    photo_ext = validate_image_upload(
        photo.content_type, photo_bytes, size_error_detail="Photo must be 5MB or smaller"
    )
    sheet_bytes = await attendance_sheet.read()
    sheet_ext = validate_document_upload(
        attendance_sheet.content_type,
        sheet_bytes,
        size_error_detail="Attendance sheet must be 5MB or smaller",
    )

    photo_dir = media_subdir("trainer_checkout_photos")
    (photo_dir / f"{conference.conferenceUid}.{photo_ext}").write_bytes(photo_bytes)
    conference.conferenceImage = f"trainer_checkout_photos/{conference.conferenceUid}.{photo_ext}"

    sheet_dir = media_subdir("attendance_sheets")
    (sheet_dir / f"{conference.conferenceUid}.{sheet_ext}").write_bytes(sheet_bytes)
    conference.attendanceSheet = f"attendance_sheets/{conference.conferenceUid}.{sheet_ext}"

    if conference.activeModuleId:
        if conference.activeModuleId == "LIVE_QUIZ":
            live_quiz_service.finish_quiz(db, conference)
        log_module_action(db, conference.conferenceUid, conference.activeModuleId, "STOPPED", admin.username)
        conference.activeModuleId = None

    conference.conferenceEndsOn = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conference.conferenceStatus = "Completed"
    conference.actualEndedAt = datetime.now()
    conference_repository.save(db, conference)
    _nudge_session_room(background_tasks, conference_uid)

    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )


def _append_remark_line(existing: str | None, line: str) -> str:
    """This schema has no activity-log table - entity `remarks` longtext
    fields are used as running text logs (see `attendance.theftRemarks`
    COMMENT 'Log of tab switches'). Prepend a timestamped line so the newest
    entry is first."""
    entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {line}"
    return f"{entry}\n{existing}" if existing else entry


def _nudge_session_room(background_tasks: BackgroundTasks, conference_uid: str) -> None:
    """Tell everyone on the conference's `/ws/live` room (the trainees) to
    refetch `/sessions/current`. Fired after any trainer action that changes
    what a trainee sees - starting/stopping a module, marking attendance,
    starting/ending the session - so their screen updates in real time
    instead of waiting for the 10s poll. The payload is a thin nudge; the
    real state travels over REST."""
    background_tasks.add_task(ws_manager.send_to_room, conference_uid, {"type": "session"})


def mark_attendance(
    db: Session,
    admin: Admin,
    conference_uid: str,
    trainee_uid: str,
    payload: AttendanceMarkRequest,
    background_tasks: BackgroundTasks,
) -> SessionDashboardOut:
    """Manual Present/Absent from the Trainee Master List - only allowed
    while the session is running. Records who/when/why: sets `status` +
    `updatedBy`, appends a timestamped line to `attendance.remarks`, and
    upserts the `attendance_logs` snapshot for the ATTENDANCE module."""
    conference = _get_owned_conference(db, admin, conference_uid)
    if title_status(conference.conferenceStatus) != "Ongoing":
        raise conflict("Attendance can only be changed while the session is running")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{admin.username} -> {payload.status.upper()}: {payload.reason.strip()}"

    record = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee_uid)
    if record:
        record.status = payload.status
        record.markedOn = now_str
        record.updatedBy = admin.username
        record.remarks = _append_remark_line(record.remarks, log_line)
        attendance_repository.save(db)
    else:
        attendance_repository.create(
            db,
            Attendance(
                conferenceUid=conference_uid,
                trainerUid=conference.trainerEmployeeId,
                traineeUid=trainee_uid,
                markedOn=now_str,
                status=payload.status,
                updatedBy=admin.username,
                remarks=_append_remark_line(None, log_line),
            ),
        )

    attendance_repository.upsert_attendance_log(
        db, conference_uid, trainee_uid, "ATTENDANCE", payload.status
    )
    attendance_repository.save(db)

    _nudge_session_room(background_tasks, conference_uid)
    return _build_dashboard(db, conference)


def unlock_proctoring(
    db: Session,
    admin: Admin,
    conference_uid: str,
    trainee_uid: str,
    payload: ProctoringUnlockRequest,
    background_tasks: BackgroundTasks,
) -> SessionDashboardOut:
    """Clears a trainee's on-device proctoring lockout from the Participant
    Master List - records who/when/why on `attendance.theftRemarks` +
    `remarks` and resets `isTheftLocked` / `theftAttemptsLeft`. The trainee's
    post-test screen sees the flip via `/sessions/current` and lets them back
    in (session_service.get_current_session)."""
    conference = _get_owned_conference(db, admin, conference_uid)
    record = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee_uid)
    if record is None or not record.isTheftLocked:
        raise conflict("This trainee isn't locked")

    reason = payload.reason.strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record.isTheftLocked = 0
    record.theftAttemptsLeft = 3
    record.theftRemarks = f"[{now_str}] {admin.username} -> UNLOCK: {reason}\n{record.theftRemarks or ''}".rstrip()
    record.remarks = _append_remark_line(record.remarks, f"{admin.username} -> PROCTORING UNLOCK: {reason}")
    record.updatedBy = admin.username
    attendance_repository.save(db)

    _nudge_session_room(background_tasks, conference_uid)
    return _build_dashboard(db, conference)


def reset_attendance(
    db: Session, admin: Admin, conference_uid: str, trainee_uid: str, background_tasks: BackgroundTasks
) -> SessionDashboardOut:
    """Clears a trainee's attendance record entirely - the "..." control
    on the Trainee Master List."""
    conference = _get_owned_conference(db, admin, conference_uid)
    attendance_repository.delete_for_conference_and_trainee(db, conference_uid, trainee_uid)
    _nudge_session_room(background_tasks, conference_uid)
    return _build_dashboard(db, conference)


def list_attendance(db: Session, admin: Admin) -> list[AttendanceListItemOut]:
    """Powers the trainer's Attendance List / Pending Attendance / Confirmed
    Attendance screens (all three fetch this same list and split it
    client-side by `marked`). Scoped to this trainer's own conferences,
    same as list_trainer_trainings - this lives in the trainer's own More
    menu, not a cross-trainer admin view."""
    conferences = conference_repository.list_all_for_trainer(db, admin.username)
    conference_by_uid = {c.conferenceUid: c for c in conferences}
    conference_uids = list(conference_by_uid.keys())
    if not conference_uids:
        return []

    attendance_rows = attendance_repository.list_for_conferences(db, conference_uids)

    trainee_uids = {a.traineeUid for a in attendance_rows}
    trainees_by_uid = {t.traineeUid: t for t in trainee_repository.get_by_uids(db, trainee_uids)}

    # Per-participant tallies across every training this trainer owns - the
    # roster is seeded (status "Pending") when a training is scheduled, so a
    # trainee on an upcoming session counts here before it's held.
    trainings_total: Counter[str] = Counter(a.traineeUid for a in attendance_rows)
    trainings_present: Counter[str] = Counter(
        a.traineeUid for a in attendance_rows if a.status == "Present"
    )
    trainings_pending: Counter[str] = Counter(
        a.traineeUid for a in attendance_rows if a.status in ("Pending", "Joined")
    )

    result_rows = assessment_repository.list_results_for_conferences(db, conference_uids)
    # Keep only the latest attempt per (conference, trainee), matching a
    # conference's own post-test suite - the same "latest attempt wins"
    # rule _build_dashboard uses for the single-session dashboard.
    latest_result: dict[tuple[str, str], object] = {}
    for r in result_rows:
        conference = conference_by_uid.get(r.conferenceUid)
        if not conference or r.assessmentSuiteUid != conference.postAssessmentUid:
            continue
        key = (r.conferenceUid, r.traineeUid)
        latest_result.setdefault(key, r)

    items: list[AttendanceListItemOut] = []
    for a in attendance_rows:
        conference = conference_by_uid.get(a.conferenceUid)
        trainee = trainees_by_uid.get(a.traineeUid)
        result = latest_result.get((a.conferenceUid, a.traineeUid))

        post_test_score = None
        post_test_summary = None
        if result:
            total = float(result.maxScore)
            correct = float(result.totalScore)
            post_test_score = f"{correct:g} / {total:g} ({float(result.percentage):g}%)"
            post_test_summary = f"Total: {total:g}, Correct: {correct:g}, Wrong: {total - correct:g}"

        items.append(
            AttendanceListItemOut(
                attendanceId=a.attendanceUid or str(a.id),
                region=conference.region if conference else None,
                product=conference.trainingType if conference else None,
                session=conference.sessionType if conference else None,
                audienceType=conference.audience if conference else None,
                conferenceDate=conference.conferenceDate if conference else None,
                trainerName=conference.trainerName if conference else None,
                trainerHoId=conference.trainerEmployeeId if conference else None,
                participantHoId=trainee.employee_id if trainee else None,
                participantName=trainee.name if trainee else "Unknown Trainee",
                phone=str(a.phone) if a.phone else (str(trainee.phone) if trainee else None),
                state=conference.state if conference else None,
                location=", ".join(filter(None, [conference.district, conference.state])) if conference else None,
                reportingManagerOfPromoter=trainee.supervisorName if trainee else None,
                attendanceStatus=a.status,
                checkIn=a.markedOn,
                checkOut=a.checkOutTime.strftime("%Y-%m-%d %H:%M:%S") if a.checkOutTime else None,
                postTestScore=post_test_score,
                postTestScoreSummary=post_test_summary,
                sessionTypeMethod=conference.sessionType if conference else None,
                conferenceId=a.conferenceUid,
                lastUpdates=a.timestamp.strftime("%Y-%m-%d %H:%M:%S") if a.timestamp else None,
                marked=a.status == "Present",
                trainerTrainingsTotal=trainings_total[a.traineeUid],
                trainerTrainingsPresent=trainings_present[a.traineeUid],
                trainerTrainingsPending=trainings_pending[a.traineeUid],
            )
        )

    return items
