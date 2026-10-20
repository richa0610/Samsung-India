import json
from dataclasses import dataclass
from datetime import datetime

from fastapi import BackgroundTasks
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import (
    DEFAULT_SESSION_TITLE,
    MODULE_NAMES,
    PASS_THRESHOLD_PERCENT,
)
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
    ProctoringStrikeOut,
    ProctoringStrikeRequest,
    SessionHistoryItem,
    SessionJoinInfo,
    SessionModule,
)
from app.utils.conference_format import (
    COMPLETED,
    RUNNING,
    active_module,
    is_completed,
    is_running,
    location_label,
    log_action,
    log_module,
    log_time,
    read_session_config,
    session_status,
)
from app.services.account_ids import same_trainer
from app.services.module_flow import auto_advance_if_due, configured_modules, live_quiz_suite_uid, scored_suite_uids
from app.services.proctoring_settings_service import get_proctoring_settings
from app.services import proctoring_strikes, trainee_access
from app.utils import join_code
from app.utils.date_utils import duration, ist_now, parse_module_start, to_venue_time, utc_now
from app.utils.status import title_status


def _conference_start(conference: Conference) -> datetime | None:
    return parse_module_start(conference.conferenceDate, conference.conferenceTime)


def _session_is_over(conference: Conference) -> bool:
    """True once a session should stop counting as active for a trainee.

    A session that has been started stays active until the trainer explicitly
    ends it - it is never timed out by the date, so a session running past
    midnight isn't cut off. It is over only when:

      1. The trainer ended it (Completed) or an admin cancelled it.
      2. It was never started and its scheduled date is already before today
         (IST), i.e. it was missed.

    `conferenceEndsOn` is the training's planned last day (the other system fills it when the
    training is created - user, 2026-10-17), so it never means "ended" here."""
    status = session_status(conference.conferenceStatus)
    if status in (COMPLETED, "Cancelled"):
        return True
    if status == RUNNING:
        return False
    scheduled_day = (conference.conferenceDate or "").strip()
    return bool(scheduled_day) and scheduled_day < ist_now().date().isoformat()


def _select_current_conference(
    db: Session, trainee: Trainee | None = None, requested_conference_uid: str | None = None
) -> tuple[Conference | None, bool, datetime | None]:
    """Picks which conference is "current" for the trainee app - only ever one the trainee is on
    (user, 2026-10-13). A trainee who signs in without a QR and has no training of their own gets
    none, and the home screen shows "No Session" - never another trainer's live training or an
    unrelated / old one (which used to be shown, and the home screen then joined them to it).

    Priority:
      0. The requested conference - the QR / share link - if the trainee is on it.
      1. The trainee's own session: running now, else today's (waiting for its start, or ended -
         shown completed so they see their final results).
    """
    # Each step runs only if every step before it found nothing.
    return (
        _requested_conference(db, trainee, requested_conference_uid)
        or _own_conference(db, trainee)
        or (None, False, None)
    )


_Selection = tuple[Conference | None, bool, datetime | None]


def _is_running(conference: Conference) -> bool:
    return is_running(conference) and not _session_is_over(conference)


def _requested_conference(db: Session, trainee: Trainee | None, requested_conference_uid: str | None) -> _Selection | None:
    """0. The explicitly requested conference - honoured only for a session this trainee is on; any
    other ID falls through to the normal selection instead of exposing that session's modules."""
    if not requested_conference_uid:
        return None
    req_conf = db.query(Conference).filter(Conference.conferenceUid == requested_conference_uid).first()
    if req_conf and (trainee is None or trainee_access.has_taken_part(db, trainee, requested_conference_uid)):
        return req_conf, _is_running(req_conf), _conference_start(req_conf)
    return None


def _own_conference(db: Session, trainee: Trainee | None) -> _Selection | None:
    """1. The trainee's own session - one they joined (by QR) or were marked at, never a roster row
    an admin pre-assigned that they haven't activated ("Pending") nor a cancelled training: the
    newest running one, else the newest of today's (waiting for its start, or ended today - shown
    completed so they see their final results). Every such row counts, not only the latest one, so
    an older training they were Present at never hides today's."""
    if not trainee:
        return None
    rows = (
        db.query(Attendance, Conference)
        .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
        .filter(
            Attendance.traineeUid == trainee.traineeUid,
            func.coalesce(Attendance.status, "") != "Pending",
            func.lower(func.coalesce(Conference.conferenceStatus, "")) != "cancelled",
        )
        .order_by(Attendance.id.desc())
        .all()
    )
    running = next((conference for _, conference in rows if _is_running(conference)), None)
    if running is not None:
        return running, True, _conference_start(running)
    today = next((conference for attendance, conference in rows if _attended_today(conference, attendance)), None)
    if today is not None:
        return today, False, _conference_start(today)
    return None


def _attended_today(conference: Conference, attendance: Attendance) -> bool:
    now_str = ist_now().strftime("%Y-%m-%d")
    return bool(
        conference.conferenceDate == now_str
        or (conference.actualEndedAt and conference.actualEndedAt.strftime("%Y-%m-%d") == now_str)
        or (attendance.markedOn and str(attendance.markedOn).startswith(now_str))
    )


def _join_info(conference: Conference) -> SessionJoinInfo:
    start_at = _conference_start(conference)
    return SessionJoinInfo(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
        sessionType=conference.sessionType,
        date=conference.conferenceDate,
        location=location_label(conference),
        trainerName=conference.trainerName,
        started=is_running(conference),
        startsAt=start_at.strftime("%d %b %Y, %I:%M %p") if start_at else None,
    )


def _conference_for_code(db: Session, code: str, tenant_id: str) -> Conference:
    """The training behind a scanned join code. The code's signature is checked first
    (app/utils/join_code.py, bound to this tenant): a guessed or edited code, or one from another
    tenant, is "not valid" exactly like an unknown training - no lookup, nothing revealed."""
    conference_uid = join_code.verify(tenant_id, code)
    conference = conference_repository.get_by_uid(db, conference_uid) if conference_uid else None
    if not conference:
        raise not_found("That training session code isn't valid")
    approved = title_status(conference.status) == "Approved"
    if not approved and session_status(conference.conferenceStatus) not in (RUNNING, COMPLETED):
        raise bad_request("This training isn't open to join yet")
    if _session_is_over(conference):
        raise bad_request("This training session has already ended")
    return conference


def get_join_info(db: Session, code: str, tenant_id: str) -> SessionJoinInfo:
    """Public preview of the training behind a scanned QR code (a valid signed code only)."""
    return _join_info(_conference_for_code(db, code, tenant_id))


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
    db: Session, trainee: Trainee, code: str, tenant_id: str, via_registration: bool = False
) -> SessionJoinInfo:
    """Binds the (already-authenticated) trainee to the scanned training so
    `GET /sessions/current` resolves to it, and auto-approves a trainee who
    reached the app through a trainer-shared QR.

    `via_registration` is set only by the scan-QR-then-register flow - it's
    what tells a brand-new trainee (FRESH) apart from an existing one who just
    logged in and joined (UNASSIGNED)."""
    conference = _conference_for_code(db, code, tenant_id)
    # Serialize roster changes for this session (see conference_repository.lock_for_roster_change).
    conference_repository.lock_for_roster_change(db, conference.conferenceUid)
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
        stamp = utc_now().strftime("%Y-%m-%d %H:%M:%S")
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
    the trainer can unlock them (training.attendance_actions.unlock_proctoring). No schema
    change: uses the pre-existing `isTheftLocked` / `theftAttemptsLeft` /
    `theftRemarks` columns (SCHEMA.md documents them for exactly this).

    Only on a session the trainee is already on - a lock is reported from inside that session's
    assessment. It never creates a roster row (that would let a lock report join any session,
    around the QR join's own gate)."""
    # Locked like a strike report (record_proctoring_strike), so the two never miscount each other.
    conference, attendance = trainee_access.rostered_conference(db, trainee, payload.conferenceUid, lock=True)
    proctoring_strikes.record_lockout(attendance, payload.violationType, payload.strikeNumber, payload.strikeId)
    attendance_repository.save(db)

    background_tasks.add_task(
        ws_manager.send_to_room, tenant_id, conference.conferenceUid, {"type": "session"}
    )
    return ProctoringLockOut(locked=True)


def record_proctoring_strike(
    db: Session,
    trainee: Trainee,
    payload: ProctoringStrikeRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str,
) -> ProctoringStrikeOut:
    """One proctoring strike during the trainee's test: its reason counted, and the trainee locked
    out on the server once their strikes since the last unlock reach the company's warning limit
    (proctoring_strikes.record_strike). Only a trainee marked Present on that training - the one
    taking its test; their attendance row is held so concurrent strikes count one after another.
    A strike sent twice counts once."""
    # Read before the row is held: the warning limit lives in the Common DB.
    _, warning_limit = get_proctoring_settings(tenant_id)
    conference, attendance = trainee_access.present_conference(db, trainee, payload.conferenceUid, lock=True)
    outcome = proctoring_strikes.record_strike(attendance, payload.violationType, payload.strikeId, warning_limit)
    attendance_repository.save(db)
    if outcome.counted:
        background_tasks.add_task(
            ws_manager.send_to_room, tenant_id, conference.conferenceUid, {"type": "session"}
        )
    return ProctoringStrikeOut(counted=outcome.counted, attemptsLeft=attendance.theftAttemptsLeft, locked=outcome.locked)


_CHECK_IN_FIRST = "Complete your check-in to unlock this."


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

    location = location_label(conference)
    is_over = _session_is_over(conference)
    config = read_session_config(conference.sessionConfig)
    timeline = _ModuleTimeline.load(db, conference, is_over)
    attendance = _session_attendance(db, conference, trainee)

    # Admission: the trainee self-admits once the Attendance module is live, then runs Secure
    # Check-In (location + face photo); the row keeps status "Present" and gains `checkInPhoto`,
    # which is how we tell "admitted, not yet checked in" from "checked in". "Absent" is a hard
    # eject (the app blocks the whole screen). The other modules stay locked until the trainee has
    # actually checked in.
    trainee_checked_in = attendance.status == "Present" and attendance.checkInPhoto is not None
    # The Attendance card is done only once the trainee has completed their
    # own check-in (or the trainer marked them Absent).
    attendance_completed = trainee_checked_in or attendance.status == "Absent"
    attendance_cfg = config.get("attendance", {})

    # Built keyed, then emitted in `configured_modules` order (which is sorted
    # by each module's planned start time).
    module_by_key = {"ATTENDANCE": _attendance_module(conference, attendance_cfg, attendance, timeline, attendance_completed)}
    for key, suite_uid, config_key in _assessment_modules(conference, config):
        if suite_uid:
            module_by_key[key] = _assessment_module(
                db, conference, trainee, key, suite_uid, config.get(config_key, {}), timeline, trainee_checked_in
            )

    # Emit in the flow's time-sorted order; anything built but not in that
    # list (shouldn't happen) trails at the end in build order.
    modules = [module_by_key[k] for k in timeline.module_order if k in module_by_key]
    modules += [m for k, m in module_by_key.items() if k not in timeline.module_order]

    return CurrentSession(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or DEFAULT_SESSION_TITLE,
        sessionType=conference.sessionType,
        date=conference.conferenceDate,
        location=location,
        trainerName=conference.trainerName,
        confirmationStatus=_confirmation_status(is_over, attendance_completed),
        started=False if is_over else started,
        sessionClosed=is_over,
        startsAt=_starts_at_label(start_at, started, is_over),
        admitted=trainee_checked_in,
        attendanceStatus=attendance.status,
        # On-device proctoring lockout (post-test). The trainer clears it from
        # the Participant Master List; the trainee's screen sees the flip here
        # and lets them back into the test.
        proctoringLocked=bool(attendance.isTheftLocked),
        liveProctoringEnabled=live_proctoring_enabled,
        proctoringMaxWarnings=proctoring_max_warnings,
        attendanceGeoFencing=bool(attendance_cfg.get("geoFencing")),
        modules=modules,
    )


def _starts_at_label(start_at: datetime | None, started: bool, is_over: bool) -> str | None:
    """When a session that hasn't started yet begins, e.g. "10 Oct 2026, 09:00 AM"."""
    if start_at and not started and not is_over:
        return start_at.strftime("%d %b %Y, %I:%M %p")
    return None


def _confirmation_status(is_over: bool, attendance_completed: bool) -> str:
    if is_over:
        return "Completed"
    return "Confirmed" if attendance_completed else "Not Confirmed"


def _session_attendance(db: Session, conference: Conference, trainee: Trainee) -> Attendance:
    """The trainee's attendance row on this session - created as "Joined", tagged with how they
    reached it, the first time they open it."""
    attendance = attendance_repository.get_for_conference_and_trainee(db, conference.conferenceUid, trainee.traineeUid)
    if attendance is not None:
        return attendance
    attendance = Attendance(
        conferenceUid=conference.conferenceUid,
        trainerUid=conference.trainerEmployeeId,
        traineeUid=trainee.traineeUid,
        phone=trainee.phone,
        status="Joined",
    )
    audience = "ASSIGNED" if same_trainer(db, None, trainee.trainerEmployeeId, conference.trainerEmployeeId) else "UNASSIGNED"
    _set_attendance_audience(attendance, audience)
    return attendance_repository.create(db, attendance)


@dataclass
class _ModuleTimeline:
    """One session's modules as the trainer actually ran them (their Start/End actions): how long
    each ran, and whether a trainee who didn't complete one has missed it."""

    conference: Conference
    is_over: bool
    module_order: list[str]
    active_index: int | None
    runs: dict[str, list[ConferenceActivityLog]]

    @classmethod
    def load(cls, db: Session, conference: Conference, is_over: bool) -> "_ModuleTimeline":
        # A module counts as "missed" once the flow has moved past it (or its own
        # window / the whole session has closed) without the trainee completing
        # it - as opposed to just not-yet-live, which still shows "please wait".
        module_order = configured_modules(conference)
        running = active_module(conference)
        active_index = module_order.index(running) if running in module_order else None
        # Per-module run history from the trainer's Start/End actions. A module
        # the trainer has already Started and Ended - `ran_seconds` set - is over:
        # a trainee who never completed it (didn't check in / joined after it
        # ended) has missed it, and we can show how long it actually ran.
        runs: dict[str, list[ConferenceActivityLog]] = {}
        for log in activity_log_repository.list_for_conference(db, conference.conferenceUid):
            runs.setdefault(log_module(log), []).append(log)
        return cls(conference, is_over, module_order, active_index, runs)

    def ran_seconds(self, key: str) -> int | None:
        entries = self.runs.get(key, [])
        starts = [e for e in entries if log_action(e) == "STARTED"]
        stops = [e for e in entries if log_action(e) == "STOPPED"]
        if not stops or not starts:
            return None
        start = starts[min(len(stops), len(starts)) - 1]
        return max(0, int((log_time(stops[-1]) - log_time(start)).total_seconds()))

    def ran_label(self, key: str) -> str | None:
        """How long the module actually ran, e.g. "45m 3s" - for the
        duration pill / the "Ran : ..." badge on a finished module."""
        secs = self.ran_seconds(key)
        return None if secs is None else _run_length(secs)

    def ran_badge(self, key: str) -> str | None:
        label = self.ran_label(key)
        return f"Ran : {label}" if label else None

    def is_missed(self, key: str, completed: bool, live: bool) -> bool:
        """Module flow is fully manual now - the trainer Starts/Ends each
        module by hand, so the scheduled clock times in `sessionConfig`
        are only a plan and must NOT make a module "missed". A module is
        missed only when (1) the trainer Started then Ended it and the trainee
        never completed it (didn't check in / joined after), (2) the session
        itself has ended, or (3) the trainer has manually advanced the flow
        past it."""
        if completed or live:
            return False
        return self.ran_seconds(key) is not None or self._session_ended() or self._advanced_past(key)

    def _session_ended(self) -> bool:
        return self.is_over or is_completed(self.conference)

    def _advanced_past(self, key: str) -> bool:
        return key in self.module_order and self.active_index is not None and self.module_order.index(key) < self.active_index


def _run_length(secs: int) -> str:
    hours, rem = divmod(secs, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _attendance_module(
    conference: Conference, attendance_cfg: dict, attendance: Attendance, timeline: _ModuleTimeline, completed: bool
) -> SessionModule:
    # Every trainee self-admits once the Attendance module is live - no
    # per-trainee admission gate (assigned/unassigned/fresh doesn't matter
    # here; routers/attendance.py accepts a self check-in from any of them
    # the same way, only a trainer's already-final Present/Absent decision
    # blocks it) - so this card is never locked waiting for the trainer.
    live = active_module(conference) == "ATTENDANCE" and not completed
    # Sessions imported without a Session Flow config have no per-module
    # times - fall back to the conference's own start time so the trainee
    # sees a real value instead of a hardcoded placeholder.
    opens = attendance_cfg.get("checkInOpens") or to_venue_time(conference.conferenceTime)
    closes = attendance_cfg.get("checkOutCloses")
    return SessionModule(
        key="ATTENDANCE",
        name=MODULE_NAMES["ATTENDANCE"],
        time=opens,
        endTime=closes,
        duration=duration(opens, closes) or timeline.ran_label("ATTENDANCE"),
        ranDuration=timeline.ran_badge("ATTENDANCE"),
        isLive=live,
        isCompleted=completed,
        isMissed=timeline.is_missed("ATTENDANCE", completed, live),
        # The client's `isLocked` path is the security-violation card, a
        # different thing from admission.
        isLocked=False,
        lockReason=None,
        completedAt=attendance.markedOn.split(" ")[-1][:5] if attendance.markedOn else None,
    )


def _assessment_modules(conference: Conference, config: dict) -> tuple[tuple[str, str | None, str], ...]:
    """(module key, its question set, its sessionConfig key) for the Test, Live Quiz and Survey cards."""
    return (
        ("STANDARD_TEST", conference.postAssessmentUid, "standardTest"),
        # Unlike Standard Test/Survey, Live Quiz has no dedicated Conference
        # column yet - its assessmentSuiteUid only ever lives in
        # sessionConfig. For now it's answered the same way a Standard Test
        # is (fetch questions, submit answers) - the trainer picking a
        # question live for trainees to answer is a future iteration.
        ("LIVE_QUIZ", live_quiz_suite_uid(conference), "liveQuiz"),
        ("SURVEY", conference.surveyUid, "survey"),
    )


def _assessment_module(
    db: Session,
    conference: Conference,
    trainee: Trainee,
    key: str,
    suite_uid: str,
    module_cfg: dict,
    timeline: _ModuleTimeline,
    checked_in: bool,
) -> SessionModule:
    """A Test / Live Quiz / Survey card - locked until the trainee has checked in."""
    start_time_str = module_cfg.get("startTime") or to_venue_time(conference.conferenceTime)
    end_time_str = module_cfg.get("endTime")
    result = assessment_repository.get_latest_result(db, conference.conferenceUid, trainee.traineeUid, suite_uid)
    completed = result is not None
    live = not timeline.is_over and not completed and active_module(conference) == key
    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    question_count = module_cfg.get("questionCount") or (suite.noOfQuestion if suite else None)
    return SessionModule(
        key=key,
        name=MODULE_NAMES[key],
        time=start_time_str,
        endTime=end_time_str,
        duration=duration(start_time_str, end_time_str) or timeline.ran_label(key),
        ranDuration=timeline.ran_badge(key),
        isLive=live,
        isCompleted=completed,
        isMissed=timeline.is_missed(key, completed, live),
        isLocked=not checked_in,
        lockReason=None if checked_in else _CHECK_IN_FIRST,
        completedAt=result.submittedAt.strftime("%H:%M") if result and result.submittedAt else None,
        # A Survey is only submitted, never scored (module_flow.scored_suite_uids).
        score=f"{float(result.totalScore):g}/{float(result.maxScore):g}" if result and key != "SURVEY" else None,
        assessmentSuiteUid=suite_uid,
        suiteName=(suite.examTitle or suite.courseName) if suite else None,
        questionCount=question_count or None,
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
    results_by_conference: dict[str, list] = {}
    for result in result_rows:
        results_by_conference.setdefault(result.conferenceUid, []).append(result)

    items: list[SessionHistoryItem] = []
    for conference in conferences:
        attendance = attendance_by_conference.get(conference.conferenceUid)
        # The newest mark there (rows come submittedAt desc) - a Standard Test or Live Quiz, never a
        # Survey, whose 0% would read as a failed session.
        scored = scored_suite_uids(conference)
        result = next(
            (r for r in results_by_conference.get(conference.conferenceUid, []) if r.assessmentSuiteUid in scored), None
        )
        items.append(
            SessionHistoryItem(
                conferenceUid=conference.conferenceUid,
                title=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
                date=conference.conferenceDate,
                trainerName=conference.trainerName,
                attendanceStatus=attendance.status if attendance else None,
                score=f"{float(result.percentage):g}%" if result else None,
                passed=(float(result.percentage) >= PASS_THRESHOLD_PERCENT) if result else None,
            )
        )
    return items


def session_is_over(conference: Conference) -> bool:
    """Public name for `_session_is_over` - the rule trainee_access applies to open modules."""
    return _session_is_over(conference)


def session_is_running(conference: Conference) -> bool:
    """Started and not over - the same rule the session screen uses (conference_format.is_running:
    "Started", or "Ongoing" / "Live" from before, in any letter case)."""
    return _is_running(conference)
