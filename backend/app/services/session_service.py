import json
from datetime import datetime

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import DEMO_TRAINER_EMPLOYEE_ID, PASS_THRESHOLD_PERCENT
from app.core.exceptions import bad_request, not_found
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.models.trainee import Trainee
from app.repositories import (
    activity_log_repository,
    assessment_repository,
    attendance_repository,
    conference_repository,
    trainee_repository,
)
from app.routers.ws import manager as ws_manager
from app.schemas.session import (
    CurrentSession,
    ProctoringLockOut,
    ProctoringLockRequest,
    SessionHistoryItem,
    SessionJoinInfo,
    SessionModule,
)
from app.services.module_flow import auto_advance_if_due, configured_modules
from app.services.proctoring_settings_service import get_proctoring_settings
from app.utils.date_utils import duration, parse_module_start
from app.utils.helpers import attendance_is_assigned
from app.utils.status import title_status

_LIVE_STATUSES = ("Ongoing", "Live")

MODULE_NAMES = {
    "ATTENDANCE": "Attendance",
    "STANDARD_TEST": "Standard Test",
    "LIVE_QUIZ": "Live Quiz",
    "SURVEY": "Survey",
}


def _parse_session_config(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def _conference_start(conference: Conference) -> datetime | None:
    return parse_module_start(conference.conferenceDate, conference.conferenceTime)


def _session_is_over(conference: Conference) -> bool:
    """True once a session should stop counting as active for a trainee.
    Checked in order:

      1. The trainer explicitly ended it (`conferenceStatus == "Completed"`).
      2. Staleness guard: If the session was dated before today, it's over even
         if the trainer walked away without hitting End Session.
      3. It's actively running right now (`Ongoing`/`Live`).
      4. Otherwise, not live and not completed -> over if before today."""
    if title_status(conference.conferenceStatus) == "Completed":
        return True
    now_date_str = datetime.now().strftime("%Y-%m-%d")
    reference_day = (
        conference.conferenceEndsOn
        or (conference.actualStartedAt.strftime("%Y-%m-%d") if conference.actualStartedAt else None)
        or conference.conferenceDate
        or ""
    ).strip()
    if reference_day and reference_day < now_date_str:
        return True
    if title_status(conference.conferenceStatus) in _LIVE_STATUSES:
        return False
    return False


def _select_current_conference(
    db: Session, trainee: Trainee | None = None, requested_conference_uid: str | None = None
) -> tuple[Conference | None, bool, datetime | None]:
    """Picks which conference is "current" for the trainee app.

    Priority:
      0. An explicitly requested conference UID (if valid).
      1. A session the trainee actively attended or joined today (if completed,
         we show it as completed so they see their final results).
      2. A live (`Ongoing`/`Live`) conference - the trainee's own trainer
         first, then the demo trainer, then any live one.
      3. Otherwise an Approved scheduled conference.
      4. Otherwise the newest conference on record.
    """
    if requested_conference_uid:
        req_conf = db.query(Conference).filter(Conference.conferenceUid == requested_conference_uid).first()
        if req_conf:
            return req_conf, req_conf.conferenceStatus in _LIVE_STATUSES and not _session_is_over(req_conf), _conference_start(req_conf)

    # 1. Did the trainee actively participate in a session today?
    if trainee:
        latest_attendance = (
            db.query(Attendance)
            .filter(
                Attendance.traineeUid == trainee.traineeUid,
                (Attendance.status == "Present") | Attendance.markedOn.isnot(None),
            )
            .order_by(Attendance.id.desc())
            .first()
        )
        if not latest_attendance:
            latest_attendance = (
                db.query(Attendance)
                .filter(Attendance.traineeUid == trainee.traineeUid)
                .order_by(Attendance.id.desc())
                .first()
            )
        if latest_attendance and latest_attendance.conferenceUid:
            attended_conf = (
                db.query(Conference)
                .filter(Conference.conferenceUid == latest_attendance.conferenceUid)
                .first()
            )
            if attended_conf:
                # If this conference is still live right now, it is unconditionally their active session
                if attended_conf.conferenceStatus in _LIVE_STATUSES and not _session_is_over(attended_conf):
                    return attended_conf, True, _conference_start(attended_conf)
                # If this conference was attended today, show it so the trainee sees its final state (Completed)
                now_str = datetime.now().strftime("%Y-%m-%d")
                attended_today = (
                    attended_conf.conferenceDate == now_str
                    or (attended_conf.actualEndedAt and attended_conf.actualEndedAt.strftime("%Y-%m-%d") == now_str)
                    or (latest_attendance.markedOn and str(latest_attendance.markedOn).startswith(now_str))
                )
                if attended_today:
                    # Only override if there is an active LIVE session for this trainee right now
                    has_live_now = False
                    if trainee.trainerEmployeeId:
                        newer_live = (
                            db.query(Conference)
                            .filter(
                                Conference.trainerEmployeeId == trainee.trainerEmployeeId,
                                Conference.conferenceStatus.in_(_LIVE_STATUSES),
                            )
                            .all()
                        )
                        for live_c in newer_live:
                            if not _session_is_over(live_c):
                                has_live_now = True
                                break
                    if not has_live_now:
                        return attended_conf, False, _conference_start(attended_conf)

    ongoing_query = db.query(Conference).filter(
        Conference.conferenceStatus.in_(_LIVE_STATUSES)
    )

    if trainee and trainee.trainerEmployeeId:
        trainer_ongoing = [
            c
            for c in ongoing_query.filter(
                Conference.trainerEmployeeId == trainee.trainerEmployeeId
            ).all()
            if not _session_is_over(c)
        ]
        if trainer_ongoing:
            conf = max(trainer_ongoing, key=lambda c: c.id)
            return conf, True, _conference_start(conf)

    all_ongoing = [c for c in ongoing_query.all() if not _session_is_over(c)]
    if all_ongoing:
        demo_ongoing = [c for c in all_ongoing if c.trainerEmployeeId == DEMO_TRAINER_EMPLOYEE_ID]
        conf = max(demo_ongoing or all_ongoing, key=lambda c: c.id)
        return conf, True, _conference_start(conf)

    conferences = db.query(Conference).filter(Conference.status == "Approved").all()
    if not conferences:
        conferences = db.query(Conference).all()
    if not conferences:
        return None, False, None

    if trainee and trainee.trainerEmployeeId:
        trainer_confs = [c for c in conferences if c.trainerEmployeeId == trainee.trainerEmployeeId]
        if trainer_confs:
            conferences = trainer_confs

    now = datetime.now()
    timed: list[tuple[datetime, Conference]] = []
    undated: list[Conference] = []
    for conference in conferences:
        start_at = _conference_start(conference)
        if start_at is None:
            undated.append(conference)
        else:
            timed.append((start_at, conference))

    if timed:
        upcoming = [item for item in timed if item[0] > now]
        start_at, conference = (
            min(upcoming, key=lambda item: item[0])
            if upcoming
            else max(timed, key=lambda item: item[0])
        )
        return conference, conference.conferenceStatus in _LIVE_STATUSES, start_at

    if undated:
        conf = max(undated, key=lambda c: c.id)
        return conf, conf.conferenceStatus in _LIVE_STATUSES, None

    return None, False, None


def _join_info(conference: Conference) -> SessionJoinInfo:
    start_at = _conference_start(conference)
    return SessionJoinInfo(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or "Training Session",
        sessionType=conference.sessionType,
        date=conference.conferenceDate,
        location=", ".join(filter(None, [conference.district, conference.state])) or None,
        trainerName=conference.trainerName,
        started=conference.conferenceStatus in _LIVE_STATUSES,
        startsAt=start_at.strftime("%d %b %Y, %I:%M %p") if start_at else None,
    )


def _conference_for_code(db: Session, code: str) -> Conference:
    conference = conference_repository.get_by_uid(db, code)
    if not conference:
        raise not_found("That training session code isn't valid")
    approved = title_status(conference.status) == "Approved"
    if not approved and conference.conferenceStatus not in (*_LIVE_STATUSES, "Completed"):
        raise bad_request("This training isn't open to join yet")
    if _session_is_over(conference):
        raise bad_request("This training session has already ended")
    return conference


def get_join_info(db: Session, code: str) -> SessionJoinInfo:
    """Public preview of the training behind a scanned QR code."""
    return _join_info(_conference_for_code(db, code))


def _set_attendance_audience(attendance: Attendance, audience: str) -> None:
    """Records how this participant reached the session (ASSIGNED / UNASSIGNED
    / FRESH) in the unused `sessionMeta` JSON column so the trainer dashboard's
    Audience Breakdown can classify them without a schema change."""
    meta = {}
    if attendance.sessionMeta:
        try:
            meta = json.loads(attendance.sessionMeta) or {}
        except (ValueError, TypeError):
            meta = {}
    meta["audience"] = audience
    attendance.sessionMeta = json.dumps(meta)


def join_session(
    db: Session, trainee: Trainee, code: str, via_registration: bool = False
) -> SessionJoinInfo:
    """Binds the (already-authenticated) trainee to the scanned training so
    `GET /sessions/current` resolves to it, and auto-approves a trainee who
    reached the app through a trainer-shared QR.

    `via_registration` is set only by the scan-QR-then-register flow - it's
    what tells a brand-new trainee (FRESH) apart from an existing one who just
    logged in and joined (UNASSIGNED)."""
    conference = _conference_for_code(db, code)
    trainee.trainerEmployeeId = conference.trainerEmployeeId
    if title_status(trainee.status) != "Approved":
        trainee.status = "Approved"
    trainee_repository.save(db, trainee)

    # Register the trainee as a participant of this specific conference so
    # they show on the trainer's live Participant Master List right away.
    # Status "Joined" distinguishes a QR/link participant from the pre-seeded
    # roster "Pending" rows (which the dashboard deliberately hides); check-in
    # later promotes it to "Present".
    existing = attendance_repository.get_for_conference_and_trainee(
        db, conference.conferenceUid, trainee.traineeUid
    )
    if existing is None:
        attendance = Attendance(
            conferenceUid=conference.conferenceUid,
            trainerUid=conference.trainerEmployeeId,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            status="Joined",
        )
        _set_attendance_audience(attendance, "FRESH" if via_registration else "UNASSIGNED")
        attendance_repository.create(db, attendance)
    elif existing.status == "Pending":
        # Admin pre-seeded this trainee onto the roster on the website - the
        # QR join is what activates the row (and puts them on the master list).
        existing.status = "Joined"
        _set_attendance_audience(existing, "ASSIGNED")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] system -> JOINED: activated from assigned roster"
        existing.remarks = f"{line}\n{existing.remarks}" if existing.remarks else line
        attendance_repository.save(db)
    return _join_info(conference)


def report_proctoring_lock(
    db: Session,
    trainee: Trainee,
    payload: ProctoringLockRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str,
) -> ProctoringLockOut:
    """The trainee's post-test proctoring struck out - persist the lock onto
    their attendance row so the trainer's Participant Master List shows it and
    the trainer can unlock them (training_service.unlock_proctoring). No schema
    change: uses the pre-existing `isTheftLocked` / `theftAttemptsLeft` /
    `theftRemarks` columns (SCHEMA.md documents them for exactly this)."""
    conference = conference_repository.get_by_uid(db, payload.conferenceUid)
    if not conference:
        raise not_found("Training not found")

    attendance = attendance_repository.get_for_conference_and_trainee(
        db, conference.conferenceUid, trainee.traineeUid
    )
    if attendance is None:
        attendance = Attendance(
            conferenceUid=conference.conferenceUid,
            trainerUid=conference.trainerEmployeeId,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            status="Joined",
        )
        attendance_repository.create(db, attendance)

    _, proctoring_max_warnings = get_proctoring_settings(tenant_id)
    attendance.isTheftLocked = 1
    attendance.theftAttemptsLeft = max(0, proctoring_max_warnings - payload.strikeNumber)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] LOCKED strike #{payload.strikeNumber}: {payload.violationType}"
    attendance.theftRemarks = f"{line}\n{attendance.theftRemarks}" if attendance.theftRemarks else line
    attendance_repository.save(db)

    background_tasks.add_task(
        ws_manager.send_to_room, conference.conferenceUid, {"type": "session"}
    )
    return ProctoringLockOut(locked=True)


def get_current_session(
    db: Session,
    trainee: Trainee,
    tenant_id: str,
    conference_uid: str | None = None,
) -> CurrentSession:
    """The trainee home screen's data payload. Resolves which session is
    active for this trainee, its modules in flow order, their live/completed
    status, and the trainee's attendance/admission gate.
    """
    conference, started, start_at = _select_current_conference(db, trainee=trainee, requested_conference_uid=conference_uid)
    if not conference:
        raise not_found("No active training session found")

    auto_advance_if_due(db, conference)

    live_proctoring_enabled, proctoring_max_warnings = get_proctoring_settings(tenant_id)

    location = ", ".join(filter(None, [conference.district, conference.state])) or None
    is_over = _session_is_over(conference)

    config = _parse_session_config(conference.sessionConfig)
    # Built keyed, then emitted in `configured_modules` order (which is sorted
    # by each module's planned start time).
    module_by_key: dict[str, SessionModule] = {}

    # A module counts as "missed" once the flow has moved past it (or its own
    # window / the whole session has closed) without the trainee completing
    # it - as opposed to just not-yet-live, which still shows "please wait".
    module_order = configured_modules(conference)
    active_index = module_order.index(conference.activeModuleId) if conference.activeModuleId in module_order else None

    # Per-module run history from the trainer's Start/End actions. A module
    # the trainer has already Started and Ended - `ran_seconds` set - is over:
    # a trainee who never completed it (didn't check in / joined after it
    # ended) has missed it, and we can show how long it actually ran.
    logs = activity_log_repository.list_for_conference(db, conference.conferenceUid)
    module_runs: dict[str, list[ConferenceActivityLog]] = {}
    for log in logs:
        module_runs.setdefault(log.moduleId, []).append(log)

    def _ran_seconds(key: str) -> int | None:
        entries = module_runs.get(key, [])
        starts = [e for e in entries if e.action == "STARTED"]
        stops = [e for e in entries if e.action == "STOPPED"]
        if not stops or not starts:
            return None
        start = starts[min(len(stops), len(starts)) - 1]
        return max(0, int((stops[-1].timestamp - start.timestamp).total_seconds()))

    def is_missed(key: str, completed: bool, live: bool) -> bool:
        if completed or live:
            return False
        # Module flow is fully manual now - the trainer Starts/Ends each
        # module by hand, so the scheduled clock times in `sessionConfig`
        # are only a plan and must NOT make a module "missed". A module is
        # missed only when it actually ran without the trainee completing
        # it, or the whole session is over.
        #
        # 1. The trainer Started then Ended this module and the trainee
        #    never completed it (didn't check in / joined after).
        if _ran_seconds(key) is not None:
            return True
        # 2. The session itself has ended.
        if is_over or conference.conferenceStatus == "Completed":
            return True
        now_date_str = datetime.now().strftime("%Y-%m-%d")
        if conference.conferenceEndsOn and str(conference.conferenceEndsOn) < now_date_str:
            return True
        # 3. The trainer has manually advanced the flow past this module.
        if key in module_order and active_index is not None and module_order.index(key) < active_index:
            return True
        return False

    def _ran_label(key: str) -> str | None:
        """How long the module actually ran, e.g. "45m 3s" - for the
        duration pill / the "Ran : ..." badge on a finished module."""
        secs = _ran_seconds(key)
        if secs is None:
            return None
        hours, rem = divmod(secs, 3600)
        minutes, seconds = divmod(rem, 60)
        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _ran_badge(key: str) -> str | None:
        label = _ran_label(key)
        return f"Ran : {label}" if label else None

    attendance = attendance_repository.get_for_conference_and_trainee(
        db, conference.conferenceUid, trainee.traineeUid
    )
    if attendance is None:
        attendance = Attendance(
            conferenceUid=conference.conferenceUid,
            trainerUid=conference.trainerEmployeeId,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            status="Joined",
        )
        audience = "ASSIGNED" if trainee.trainerEmployeeId == conference.trainerEmployeeId else "UNASSIGNED"
        _set_attendance_audience(attendance, audience)
        attendance_repository.create(db, attendance)

    attendance_status = attendance.status if attendance else None
    # Admission is trainer-gated. The trainer marking this trainee "Present"
    # on the Participant Master List is what unlocks the Attendance card -
    # until then it stays locked ("waiting for the trainer"). Once admitted,
    # the trainee runs Secure Check-In (location + face photo); the row keeps
    # status "Present" and gains `checkInPhoto`, which is how we tell
    # "admitted, not yet checked in" from "checked in". "Absent" is a hard
    # eject (the app blocks the whole screen). The other modules stay locked
    # until the trainee has actually checked in.
    trainer_admitted = attendance_status == "Present"
    trainee_checked_in = trainer_admitted and attendance.checkInPhoto is not None
    is_absent = attendance_status == "Absent"
    checked_in = trainee_checked_in
    attendance_is_active_module = conference.activeModuleId == "ATTENDANCE"
    # Every trainee self-admits once the Attendance module is live - no
    # per-trainee admission gate (assigned/unassigned/fresh doesn't matter
    # here; routers/attendance.py accepts a self check-in from any of them
    # the same way, only a trainer's already-final Present/Absent decision
    # blocks it). Kept as its own variable (rather than inlining `True`)
    # since attendance_live/_lock_reason below both read it.
    attendance_admitted = True

    def _lock_reason(module_key: str) -> str | None:
        if module_key == "ATTENDANCE":
            if not attendance_is_active_module or attendance_admitted or is_absent:
                return None
            return "Waiting for the trainer to mark you present."
        return None if trainee_checked_in else "Complete your check-in to unlock this."

    # The Attendance card is done only once the trainee has completed their
    # own check-in (or the trainer marked them Absent).
    attendance_completed = trainee_checked_in or is_absent
    attendance_live = attendance_is_active_module and attendance_admitted and not attendance_completed

    attendance_cfg = config.get("attendance", {})
    # Sessions imported without a Session Flow config have no per-module
    # times - fall back to the conference's own start time so the trainee
    # sees a real value instead of a hardcoded placeholder.
    attendance_open = attendance_cfg.get("checkInOpens") or conference.conferenceTime
    attendance_close = attendance_cfg.get("checkOutCloses")
    module_by_key["ATTENDANCE"] = SessionModule(
        key="ATTENDANCE",
        name=MODULE_NAMES["ATTENDANCE"],
        time=attendance_open,
        endTime=attendance_close,
        duration=duration(attendance_open, attendance_close) or _ran_label("ATTENDANCE"),
        ranDuration=_ran_badge("ATTENDANCE"),
        isLive=attendance_live,
        isCompleted=attendance_completed,
        isMissed=is_missed("ATTENDANCE", attendance_completed, attendance_live),
        # The admission lock is carried by `lockReason` - the client's
        # `isLocked` path is the security-violation card, a different thing.
        isLocked=False,
        lockReason=_lock_reason("ATTENDANCE"),
        completedAt=attendance.markedOn.split(" ")[-1][:5] if attendance and attendance.markedOn else None,
    )

    for key, suite_uid, config_key in (
        ("STANDARD_TEST", conference.postAssessmentUid, "standardTest"),
        # Unlike Standard Test/Survey, Live Quiz has no dedicated Conference
        # column yet - its assessmentSuiteUid only ever lives in
        # sessionConfig. For now it's answered the same way a Standard Test
        # is (fetch questions, submit answers) - the trainer picking a
        # question live for trainees to answer is a future iteration.
        ("LIVE_QUIZ", config.get("liveQuiz", {}).get("assessmentSuiteUid"), "liveQuiz"),
        ("SURVEY", conference.surveyUid, "survey"),
    ):
        if not suite_uid:
            continue

        module_cfg = config.get(config_key, {})
        start_time_str = module_cfg.get("startTime") or conference.conferenceTime
        end_time_str = module_cfg.get("endTime")
        result = assessment_repository.get_latest_result(db, conference.conferenceUid, trainee.traineeUid, suite_uid)
        completed = result is not None
        live = not is_over and not completed and conference.activeModuleId == key

        module_by_key[key] = SessionModule(
            key=key,
            name=MODULE_NAMES[key],
            time=start_time_str,
            endTime=end_time_str,
            duration=duration(start_time_str, end_time_str) or _ran_label(key),
            ranDuration=_ran_badge(key),
            isLive=live,
            isCompleted=completed,
            isMissed=is_missed(key, completed, live),
            isLocked=not checked_in,
            lockReason=_lock_reason(key),
            completedAt=result.submittedAt.strftime("%H:%M") if result and result.submittedAt else None,
            score=f"{float(result.totalScore):g}/{float(result.maxScore):g}" if result else None,
            assessmentSuiteUid=suite_uid,
        )

    # Emit in the flow's time-sorted order; anything built but not in that
    # list (shouldn't happen) trails at the end in build order.
    modules = [module_by_key[k] for k in module_order if k in module_by_key]
    modules += [m for k, m in module_by_key.items() if k not in module_order]

    return CurrentSession(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or "Training Session",
        sessionType=conference.sessionType,
        date=conference.conferenceDate,
        location=location,
        trainerName=conference.trainerName,
        confirmationStatus="Completed" if is_over else ("Confirmed" if attendance_completed else "Not Confirmed"),
        started=False if is_over else started,
        sessionClosed=is_over,
        startsAt=start_at.strftime("%d %b %Y, %I:%M %p") if start_at and not started and not is_over else None,
        admitted=checked_in,
        attendanceStatus=attendance_status,
        # On-device proctoring lockout (post-test). The trainer clears it from
        # the Participant Master List; the trainee's screen sees the flip here
        # and lets them back into the test.
        proctoringLocked=bool(attendance and attendance.isTheftLocked),
        liveProctoringEnabled=live_proctoring_enabled,
        proctoringMaxWarnings=proctoring_max_warnings,
        attendanceGeoFencing=bool(attendance_cfg.get("geoFencing")),
        modules=modules,
    )


def get_session_history(db: Session, trainee: Trainee, limit: int) -> list[SessionHistoryItem]:
    """The trainee's past sessions with their attendance/result, for the
    "Recent Sessions" popup on the session detail screen."""
    attendance_rows = attendance_repository.list_for_trainee(db, trainee.traineeUid)
    result_rows = assessment_repository.list_results_for_trainee(db, trainee.traineeUid)

    conference_uids = {a.conferenceUid for a in attendance_rows} | {r.conferenceUid for r in result_rows}
    if not conference_uids:
        return []

    conferences = conference_repository.list_by_uids(db, conference_uids, limit=limit)

    attendance_by_conference = {a.conferenceUid: a for a in attendance_rows}
    # Rows are already ordered by submittedAt desc, so the first one seen
    # per conference is that trainee's most recent result there.
    latest_result_by_conference = {}
    for result in result_rows:
        latest_result_by_conference.setdefault(result.conferenceUid, result)

    items: list[SessionHistoryItem] = []
    for conference in conferences:
        attendance = attendance_by_conference.get(conference.conferenceUid)
        result = latest_result_by_conference.get(conference.conferenceUid)
        items.append(
            SessionHistoryItem(
                conferenceUid=conference.conferenceUid,
                title=conference.suiteTitle or conference.trainingType or "Training Session",
                date=conference.conferenceDate,
                trainerName=conference.trainerName,
                attendanceStatus=attendance.status if attendance else None,
                score=f"{float(result.percentage):g}%" if result else None,
                passed=(float(result.percentage) >= PASS_THRESHOLD_PERCENT) if result else None,
            )
        )
    return items
