"""Read views of one session for whoever runs it: the Session Dashboard, the join code, the full
performer ranking and the post-session report."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import (
    DEFAULT_SESSION_TITLE,
    MAX_PROCTORING_UNLOCKS,
    PASS_THRESHOLD_PERCENT,
    UNKNOWN_TRAINEE_NAME,
)
from app.core.exceptions import bad_request
from app.models.admin import Admin
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import assessment_repository, attendance_repository, trainee_repository
from app.schemas.training import (
    AssessmentSummary,
    AudienceBreakdown,
    JoinCodeOut,
    SessionDashboardOut,
    SessionReportOut,
    SessionReportParticipant,
    SessionReportSummary,
    TopPerformer,
    TraineeRow,
)
from app.services import live_quiz_service, proctoring_strikes
from app.services.module_flow import auto_advance_if_due, live_quiz_suite_uid
from app.services.participant_stage import ParticipantStage, participant_stages
from app.services.training import timeline
from app.services.training.common import owned_conference
from app.services.training.listing import venue_names_for
from app.utils import join_code
from app.utils.conference_format import active_module, is_completed, location_label, read_session_config, session_status
from app.utils.date_utils import VENUE_TIME_FORMAT, ist_to_iso, to_venue_time
from app.utils.helpers import audience_class  # noqa: F401 - also imported from here (admin_service)
from app.utils.status import title_status


def latest_post_test_results(db: Session, conference: Conference) -> dict[str, object]:
    """Latest Post Test attempt per trainee, keyed by traineeUid. Shared by the dashboard build
    below, list_all_performers's non-Live-Quiz branch and attendance_actions.mark_attendance."""
    if not conference.postAssessmentUid:
        return {}
    return _latest_results(db, conference.conferenceUid, conference.postAssessmentUid)


def _latest_results(db: Session, conference_uid: str, suite_uid: str) -> dict[str, object]:
    """Latest submitted attempt per trainee at one assessment suite, keyed by traineeUid.
    `list_results_for_conference_suite` returns only Submitted results, newest attempt first - so
    the first row seen per trainee is their latest completed attempt."""
    latest: dict[str, object] = {}
    for result in assessment_repository.list_results_for_conference_suite(db, conference_uid, suite_uid):
        latest.setdefault(result.traineeUid, result)
    return latest


def _passed(result) -> bool:
    """A Post Test result at or above the pass mark - the one rule behind the dashboard's pass /
    fail counts and each participant's green / red score."""
    return float(result.percentage) >= PASS_THRESHOLD_PERCENT


def _top_performer(result, trainees_by_uid: dict) -> TopPerformer:
    trainee = trainees_by_uid.get(result.traineeUid)
    return TopPerformer(
        traineeUid=result.traineeUid,
        name=trainee.name if trainee else UNKNOWN_TRAINEE_NAME,
        score=float(result.totalScore),
        maxScore=float(result.maxScore),
        percentage=float(result.percentage),
    )


def build_dashboard(db: Session, conference: Conference) -> SessionDashboardOut:
    auto_advance_if_due(db, conference)
    conference_uid = conference.conferenceUid

    attendance_rows = attendance_repository.list_for_conference(db, conference_uid)
    # Participants = trainees who joined via QR/link ("Joined") or have a real
    # attendance event ("Present"/"Absent"). The pre-seeded roster "Pending"
    # rows are deliberately excluded - the master list is who actually turned
    # up / signed in, not the whole assigned roster.
    participating_uids = {a.traineeUid for a in attendance_rows if a.status != "Pending"}

    latest_result_by_trainee = latest_post_test_results(db, conference)

    participant_uids = participating_uids | set(latest_result_by_trainee.keys())
    trainees_by_uid = {t.traineeUid: t for t in trainee_repository.get_by_uids(db, participant_uids)}

    attendance_by_trainee = {a.traineeUid: a for a in attendance_rows}
    stage_by_uid = participant_stages(db, conference, attendance_by_trainee, participant_uids)

    trainee_rows = [
        _trainee_row(
            uid,
            trainees_by_uid.get(uid),
            attendance_by_trainee.get(uid),
            latest_result_by_trainee.get(uid),
            stage_by_uid[uid],
        )
        for uid in participant_uids
    ]

    pass_count = sum(1 for r in latest_result_by_trainee.values() if _passed(r))
    fail_count = len(latest_result_by_trainee) - pass_count

    # While Live Quiz is running, Top Performers tracks it instead of Post
    # Test - live_quiz_ranked_results is already ordered (score DESC, then
    # response time ASC), the same board the trainees' own Rank tab polls,
    # so this updates as trainees hit Final Submit rather than waiting for
    # the whole quiz to end. Doesn't touch latest_result_by_trainee, which
    # stays Post-Test-based for the Trainee Master List / pass-fail counts
    # above - only what Top Performers itself ranks changes here.
    top_performers = (
        live_quiz_service.live_quiz_ranked_results(db, conference)[:5]
        if active_module(conference) == "LIVE_QUIZ"
        else sorted(latest_result_by_trainee.values(), key=lambda r: float(r.percentage), reverse=True)[:5]
    )

    runtime_seconds = timeline.module_active_seconds(db, conference)

    return SessionDashboardOut(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
        trainingType=conference.trainingType,
        conferenceDate=conference.conferenceDate,
        conferenceTime=to_venue_time(conference.conferenceTime),
        trainerName=conference.trainerName,
        location=location_label(conference),
        conferenceStatus=session_status(conference.conferenceStatus),
        approvalStatus=title_status(conference.status),
        activeModuleId=active_module(conference),
        activeModuleQuestionCount=timeline.active_module_question_count(db, conference),
        # Stored in India time, like the other system's (user, 2026-10-17).
        actualStartedAt=ist_to_iso(conference.actualStartedAt),
        actualEndedAt=ist_to_iso(conference.actualEndedAt),
        runtimeSeconds=runtime_seconds,
        audience=_audience_breakdown(trainee_rows),
        assessment=AssessmentSummary(
            **{"pass": pass_count}, fail=fail_count, totalAttempts=len(latest_result_by_trainee)
        ),
        topPerformers=[_top_performer(r, trainees_by_uid) for r in top_performers],
        trainees=trainee_rows,
        executionFlow=timeline.execution_flow(db, conference),
        auditLog=timeline.audit_log(db, conference),
        sessionHeroes=timeline.session_heroes(db, conference),
        liveStudio=(
            live_quiz_service.build_live_studio(db, conference)
            if active_module(conference) == "LIVE_QUIZ"
            else None
        ),
    )


def _trainee_row(
    uid: str,
    trainee: Optional[Trainee],
    attendance: Optional[Attendance],
    result,
    stage: ParticipantStage,
) -> TraineeRow:
    """One row of the dashboard's Participant Master List."""
    is_locked, strikes, logs = _proctoring(attendance)
    return TraineeRow(
        traineeUid=uid,
        name=trainee.name if trainee else UNKNOWN_TRAINEE_NAME,
        employeeId=trainee.employee_id if trainee else None,
        phone=trainee.phone if trainee else None,
        profilePhoto=trainee.profilePhoto if trainee else None,
        audienceType=audience_class(attendance),
        status=_row_status(attendance),
        markedOn=attendance.markedOn if attendance else None,
        checkOutTime=(
            attendance.checkOutTime.strftime("%Y-%m-%d %H:%M:%S") if attendance and attendance.checkOutTime else None
        ),
        score=f"{float(result.percentage):g}%" if result else None,
        scorePassed=_passed(result) if result else None,
        isLocked=is_locked,
        proctoringStrikes=strikes,
        proctoringLogs=logs,
        proctoringUnlocks=proctoring_strikes.unlocks_used(attendance),
        proctoringMaxUnlocks=MAX_PROCTORING_UNLOCKS,
        stage=stage.stage,
        stageModules=stage.modules,
    )


def _row_status(attendance: Optional[Attendance]) -> str:
    if attendance is None:
        return "Attempted"
    if attendance.status in ("Present", "Absent"):
        return attendance.status
    return "Pending"  # "Joined" - on the list, not checked in yet


def _proctoring(attendance: Optional[Attendance]) -> tuple[bool, int, list[str]]:
    """(isLocked, strikes, log lines) from the trainee's attendance row -
    `isTheftLocked` / `theftAttemptsLeft` / `theftRemarks`, as
    services/proctoring_strikes.py keeps them (the countdown: -1 per strike,
    0 at a lockout, +3 per unlock). Strikes shown = how far the countdown is
    below 3, so a fresh unlock shows 0 again. The `3` is this display's own
    fallback for a row with no countdown yet - build_dashboard has no
    tenant_id available (it's reused by many callers that don't have a
    request to resolve one from), so TraineeRow.proctoringMaxStrikes stays
    this static default rather than the tenant's configured max; it's
    informational only - the app decides when a trainee is locked out."""
    if attendance is None:
        return False, 0, []
    logs = [ln for ln in (attendance.theftRemarks or "").splitlines() if ln.strip()]
    attempts_left = attendance.theftAttemptsLeft if attendance.theftAttemptsLeft is not None else 3
    strikes = max(0, min(3, 3 - attempts_left))
    return bool(attendance.isTheftLocked), strikes, logs


def _audience_breakdown(trainee_rows: list[TraineeRow]) -> AudienceBreakdown:
    """All derived from the participant rows so the card and the Participant Master List can never
    disagree."""
    statuses = [r.status for r in trainee_rows]
    audiences = [r.audienceType for r in trainee_rows]
    return AudienceBreakdown(
        total=len(trainee_rows),
        present=statuses.count("Present"),
        absent=statuses.count("Absent"),
        notMarked=len(statuses) - statuses.count("Present") - statuses.count("Absent"),
        assigned=audiences.count("ASSIGNED"),
        unassigned=audiences.count("UNASSIGNED"),
        fresh=audiences.count("FRESH"),
    )


def get_session_dashboard(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> SessionDashboardOut:
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    return build_dashboard(db, conference)


def get_join_code(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> JoinCodeOut:
    """The signed join code for this training's QR code / share link - only for whoever may run the
    session (the same check as its dashboard). Bound to this tenant."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    return JoinCodeOut(
        conferenceUid=conference.conferenceUid,
        joinCode=join_code.make(tenant_id, conference.conferenceUid),
        tenantId=tenant_id,
    )


def list_all_performers(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> list[TopPerformer]:
    """Every trainee ranked on whichever assessment the dashboard's Top
    Performers card is currently tracking - Live Quiz while it's the
    active module, Post Test otherwise (see build_dashboard's own
    top_performers). Powers the card's "View All" page; unlike the card
    itself, this isn't capped to 5.

    Read access is the same access grant as operating the session (`owned_conference`):
    the assigned trainer, or an admin-table account whose admin_access grant covers this
    conference. Reading no longer needs less authorization than running it."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)

    if active_module(conference) == "LIVE_QUIZ":
        ranked = live_quiz_service.live_quiz_ranked_results(db, conference)
    else:
        ranked = sorted(
            latest_post_test_results(db, conference).values(), key=lambda r: float(r.percentage), reverse=True
        )

    trainees_by_uid = {t.traineeUid: t for t in trainee_repository.get_by_uids(db, {r.traineeUid for r in ranked})}
    return [_top_performer(r, trainees_by_uid) for r in ranked]


def _report_duration_label(conference: Conference) -> Optional[str]:
    """"09:30 - 11:00" spanning the earliest module start to the latest
    module end in the session flow, falling back to the conference start
    time alone when there's no per-module config."""
    config = read_session_config(conference.sessionConfig)
    times: list[str] = []
    for section in config.values():
        if isinstance(section, dict):
            for field in ("checkInOpens", "startTime", "checkOutCloses", "endTime"):
                value = section.get(field)
                if value:
                    times.append(value)

    def _key(value: str) -> datetime:
        try:
            return datetime.strptime(value, VENUE_TIME_FORMAT)
        except ValueError:
            return datetime.max

    times = sorted({t for t in times if _key(t) is not datetime.max}, key=_key)
    if len(times) >= 2:
        return f"{times[0]} - {times[-1]}"
    return to_venue_time(conference.conferenceTime)


def get_session_report(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> SessionReportOut:
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    # The report is a post-session artifact - only available once the trainer
    # has ended the session (mirrors the disabled "Report" button on the
    # Session Dashboard).
    if not is_completed(conference):
        raise bad_request("The session report is available once the session has ended")

    attendance_by_trainee = {
        a.traineeUid: a for a in attendance_repository.list_for_conference(db, conference_uid)
    }
    venue_name = venue_names_for(db, [conference]).get(conference.venueUid)

    return SessionReportOut(
        summary=SessionReportSummary(
            conferenceId=conference.conferenceUid,
            sessionName=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
            date=conference.conferenceDate,
            state=conference.state,
            schedule=", ".join(filter(None, [conference.conferenceDate, to_venue_time(conference.conferenceTime)])) or None,
            duration=_report_duration_label(conference),
            venueLink=venue_name or location_label(conference),
        ),
        standardTest=_report_participants(db, conference_uid, conference.postAssessmentUid, attendance_by_trainee),
        liveQuiz=_report_participants(db, conference_uid, live_quiz_suite_uid(conference), attendance_by_trainee),
    )


def _report_participants(
    db: Session, conference_uid: str, suite_uid: Optional[str], attendance_by_trainee: dict[str, Attendance]
) -> list[SessionReportParticipant]:
    """Everyone who completed this module's assessment, by their latest attempt, sorted by name."""
    if not suite_uid:
        return []
    latest_by_trainee = _latest_results(db, conference_uid, suite_uid)
    trainees_by_uid = {t.traineeUid: t for t in trainee_repository.get_by_uids(db, set(latest_by_trainee))}
    rows = [
        _report_participant(uid, result, trainees_by_uid.get(uid), attendance_by_trainee.get(uid))
        for uid, result in latest_by_trainee.items()
    ]
    return sorted(rows, key=lambda r: r.name.lower())


def _report_participant(
    uid: str, result, trainee: Optional[Trainee], attendance: Optional[Attendance]
) -> SessionReportParticipant:
    return SessionReportParticipant(
        userId=trainee.employee_id if trainee and trainee.employee_id else uid,
        name=trainee.name if trainee else UNKNOWN_TRAINEE_NAME,
        role="Participant",
        checkIn=attendance.markedOn.split(" ")[-1][:5] if attendance and attendance.markedOn else None,
        checkOut=attendance.checkOutTime.strftime("%H:%M") if attendance and attendance.checkOutTime else None,
        score=f"{float(result.percentage):g}%",
    )
