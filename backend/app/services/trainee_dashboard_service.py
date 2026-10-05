"""Builds the trainee-facing Dashboard screen (`GET /sessions/dashboard`).

Everything here is derived from real rows - attendance, assessment_results and
conferences. Nothing is faked: a trainee with no history gets zeros and an
empty training table, not sample data.
"""

import math
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.trainee import Trainee
from app.repositories import (
    assessment_repository,
    attendance_repository,
    conference_repository,
    dashboard_repository,
)
from app.schemas.session import (
    DashboardMetrics,
    DashboardPerformance,
    DashboardRanking,
    DashboardTrainingRow,
    TraineeDashboardOut,
    TraineeMetricCard,
    TrainingHistoryPage,
)
from app.services import session_service
from app.services.module_flow import live_quiz_suite_uid
from app.utils.date_utils import ist_now, utc_now
from app.utils.status import title_status

_PERIOD_DAYS = 30


def _num(value) -> float:
    return float(value) if value is not None else 0.0


def _fmt_score(total, maximum) -> str | None:
    if maximum is None or float(maximum) <= 0:
        return None
    return f"{float(total):g}/{float(maximum):g}"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _avg_percent(rows: list) -> float | None:
    total = sum(_num(r.totalScore) for r in rows)
    maximum = sum(_num(r.maxScore) for r in rows)
    return (total / maximum) * 100 if maximum > 0 else None


def _test_and_quiz_suites(conference) -> set[str]:
    """The suites whose results count as marks: the conference's Standard Test
    (postAssessmentUid) and its Live Quiz. Survey / pre-test never count."""
    suites: set[str] = set()
    if conference.postAssessmentUid:
        suites.add(conference.postAssessmentUid)
    quiz = live_quiz_suite_uid(conference)
    if quiz:
        suites.add(quiz)
    return suites


def _trainee_status_for(conference, attendance) -> str:
    """This trainee's own outcome for one conference - the status on each
    Training Details row, and what Training History's status filter matches,
    so the two can never disagree. (The Dashboard's metric cards group
    trainings differently - see _metric_card_for.)"""
    over = session_service._session_is_over(conference)
    conf_live = title_status(conference.conferenceStatus) in ("Ongoing", "Live")
    if attendance and attendance.status == "Present":
        return "Completed" if over else ("Ongoing" if conf_live else "Scheduled")
    if attendance and attendance.status == "Absent":
        return "Absent"
    if over:
        return "Missed"
    if conf_live:
        return "Ongoing"
    return "Scheduled"


def _session_ended(conference) -> bool:
    """The trainer ended the session (Completed, or an end time is recorded)."""
    return title_status(conference.conferenceStatus) == "Completed" or conference.conferenceEndsOn is not None


def _never_started(conference) -> bool:
    """The trainer never started this session and its scheduled date (IST) has
    already passed - it just didn't happen, so it isn't the trainee's absence."""
    if title_status(conference.conferenceStatus) in ("Ongoing", "Live", "Completed", "Cancelled"):
        return False
    scheduled_day = (conference.conferenceDate or "").strip()
    return bool(scheduled_day) and scheduled_day < ist_now().date().isoformat()


def _metric_card_for(conference, attendance) -> TraineeMetricCard:
    """The one Dashboard metric card this training counts toward - shared by the cards' numbers and
    the Training History a tapped card opens, so the list always holds what the card counted. Every
    training lands in exactly one, so the cards add up to Total Trainings. In priority order:
      present    - marked Present at the session
      absent     - the trainer ended it and they were never marked Present
      ongoing    - it started, hasn't been ended, and they aren't Present
      notStarted - its date has passed but the trainer never started it
      scheduled  - still upcoming (assigned / joined, not begun)"""
    if attendance is not None and attendance.status == "Present":
        return "present"
    if _session_ended(conference):
        return "absent"
    if title_status(conference.conferenceStatus) in ("Ongoing", "Live"):
        return "ongoing"
    if _never_started(conference):
        return "notStarted"
    return "scheduled"


class _OwnTrainings:
    """The trainee's own trainings - every one with an attendance row or a result - with their
    attendance and results. Cancelled ones (and, with a date range, ones outside it) are dropped
    from every number and row, as if the trainee was never part of them. Three statements, the
    trainee's own rows only."""

    def __init__(self, db: Session, trainee: Trainee, start: str | None, end: str | None):
        attendance_rows = attendance_repository.list_for_trainee(db, trainee.traineeUid)
        result_rows = assessment_repository.list_results_for_trainee(db, trainee.traineeUid)
        all_uids = {row.conferenceUid for row in attendance_rows} | {row.conferenceUid for row in result_rows}
        conferences = {c.conferenceUid: c for c in conference_repository.list_by_uids(db, all_uids)}
        dropped = {uid for uid, c in conferences.items() if title_status(c.conferenceStatus) == "Cancelled"}
        if start or end:
            dropped |= {
                uid
                for uid, c in conferences.items()
                if (start and (c.conferenceDate or "") < start) or (end and (c.conferenceDate or "") > end)
            }
        self.attendance_rows = [row for row in attendance_rows if row.conferenceUid not in dropped]
        self.result_rows = [row for row in result_rows if row.conferenceUid not in dropped]
        self.attendance_by_conf = {row.conferenceUid: row for row in self.attendance_rows}
        self.results_by_conf: dict[str, list] = {}
        for row in self.result_rows:
            self.results_by_conf.setdefault(row.conferenceUid, []).append(row)
        self.conf_uids = all_uids - dropped
        self.conferences_by_uid = {uid: c for uid, c in conferences.items() if uid not in dropped}

    def newest_first(self) -> list:
        return sorted(
            self.conferences_by_uid.values(),
            key=lambda c: (_parse_date(c.conferenceDate) or datetime.min, c.id),
            reverse=True,
        )


def list_training_history(
    db: Session,
    trainee: Trainee,
    page: int,
    limit: int,
    start: str | None = None,
    end: str | None = None,
    status: str | None = None,
    card: Optional[TraineeMetricCard] = None,
) -> TrainingHistoryPage:
    """One page of the trainee's Training History, newest first - the screen's infinite scroll.
    The date range and the filters apply before paging, so `total` is what matches them; `status`
    is the trainee's own outcome shown on each row (_trainee_status_for) and `card` the Dashboard
    metric card a training counted toward (_metric_card_for - a tapped card lists exactly what it
    counted). Both depend on the session's timing, so they are applied here rather than in SQL -
    over the trainee's own trainings only. Only the page's rows are built (scores and session rank:
    one statement for the page), and the tenant-wide ranking the Dashboard shows is not computed."""
    own = _OwnTrainings(db, trainee, start, end)
    ordered = own.newest_first()
    if status:
        ordered = [c for c in ordered if _trainee_status_for(c, own.attendance_by_conf.get(c.conferenceUid)) == status]
    if card:
        ordered = [c for c in ordered if _metric_card_for(c, own.attendance_by_conf.get(c.conferenceUid)) == card]
    total = len(ordered)
    offset = (page - 1) * limit
    rows = _training_rows(db, trainee, ordered[offset:offset + limit], own.attendance_by_conf, own.results_by_conf)
    return TrainingHistoryPage(
        items=rows, total=total, page=page, pageSize=limit, totalPages=math.ceil(total / limit) if total else 0
    )


def build_trainee_dashboard(
    db: Session, trainee: Trainee, limit: int, start: str | None = None, end: str | None = None
) -> TraineeDashboardOut:
    conference, started, _start_at = session_service._select_current_conference(db, trainee=trainee)

    own = _OwnTrainings(db, trainee, start, end)
    attendance_rows, result_rows = own.attendance_rows, own.result_rows
    attendance_by_conf, results_by_conf = own.attendance_by_conf, own.results_by_conf
    conf_uids, conferences_by_uid = own.conf_uids, own.conferences_by_uid

    # --- metrics: one card per training (see _metric_card_for) -------------
    cards = Counter(
        _metric_card_for(training, attendance_by_conf.get(uid))
        for uid, training in conferences_by_uid.items()
    )
    metrics = DashboardMetrics(totalTrainings=sum(cards.values()), **cards)

    # --- performance: Standard Test + Live Quiz marks, for sessions the
    #     trainee was actually marked Present at (a result without a Present
    #     attendance row doesn't count) ---
    my_suites = {
        uid: _test_and_quiz_suites(conferences_by_uid[uid]) for uid in results_by_conf if uid in conferences_by_uid
    }
    present_conf_uids = {row.conferenceUid for row in attendance_rows if row.status == "Present"}

    def _counts_as_mark(row) -> bool:
        return (
            row.status == "Submitted"
            and row.conferenceUid in present_conf_uids
            and row.assessmentSuiteUid in my_suites.get(row.conferenceUid, set())
        )

    scored = [row for row in result_rows if _counts_as_mark(row)]
    total_score = sum(_num(row.totalScore) for row in scored)
    max_score = sum(_num(row.maxScore) for row in scored)
    cutoff = utc_now() - timedelta(days=_PERIOD_DAYS)
    recent = [row for row in scored if row.submittedAt and row.submittedAt >= cutoff]
    older = [row for row in scored if row.submittedAt and row.submittedAt < cutoff]
    recent_avg, older_avg = _avg_percent(recent), _avg_percent(older)
    period_gain = round(recent_avg - older_avg, 1) if recent_avg is not None and older_avg is not None else None
    performance = DashboardPerformance(
        percentage=round(total_score / max_score * 100, 1) if max_score > 0 else 0.0,
        totalScore=round(total_score, 2),
        maxScore=round(max_score, 2),
        periodGain=period_gain,
    )

    # --- ranking: trainees who've attended >=1 training, by their Standard
    #     Test + Live Quiz marks. A new trainee who's never attended is out. ---
    # Computed in the database on every request (dashboard_repository.trainee_rank) - never cached,
    # so a result or attendance written anywhere shows up in the next rank.
    global_position, state_position = dashboard_repository.trainee_rank(db, trainee.traineeUid, trainee.state)
    ranking = DashboardRanking(
        globalRank=global_position.rank,
        globalTotal=global_position.total,
        globalPercentile=global_position.percentile,
        stateRank=state_position.rank,
        stateTotal=state_position.total,
        statePercentile=state_position.percentile,
        stateName=trainee.state,
    )

    # --- training rows -------------------------------------------------
    trainings = _build_training_rows(db, trainee, attendance_by_conf, results_by_conf, conferences_by_uid, limit)

    return TraineeDashboardOut(
        conferenceUid=conference.conferenceUid if conference else None,
        hasActiveSession=bool(conference and started),
        metrics=metrics,
        performance=performance,
        ranking=ranking,
        trainings=trainings,
    )


def _build_training_rows(
    db, trainee, attendance_by_conf, results_by_conf, conferences_by_uid, limit
) -> list[DashboardTrainingRow]:
    # Newest first for display; only the rows returned are built.
    ordered = sorted(
        conferences_by_uid.values(),
        key=lambda c: (_parse_date(c.conferenceDate) or datetime.min, c.id),
        reverse=True,
    )[:limit]
    return _training_rows(db, trainee, ordered, attendance_by_conf, results_by_conf)


def _training_rows(db, trainee, ordered, attendance_by_conf, results_by_conf) -> list[DashboardTrainingRow]:
    """The table rows for exactly these trainings, in this order."""
    # The trainee's rank in each row's Standard Test, for all rows in ONE statement (not one per
    # row): each trainee counts once by their latest attempt, equal scores share a rank.
    session_rank = dashboard_repository.session_ranks(
        db, trainee.traineeUid, {conf.conferenceUid: conf.postAssessmentUid for conf in ordered if conf.postAssessmentUid}
    )

    rows: list[DashboardTrainingRow] = []
    for conf in ordered:
        conf_results = results_by_conf.get(conf.conferenceUid, [])
        by_suite = {r.assessmentSuiteUid: r for r in conf_results}

        post = by_suite.get(conf.postAssessmentUid) if conf.postAssessmentUid else None
        quiz_suite = live_quiz_suite_uid(conf)
        quiz = by_suite.get(quiz_suite) if quiz_suite else None

        # The trainee's own outcome for this training, not the raw conference
        # lifecycle: a session that ran and ended while the trainee only
        # "Joined" (never checked in) is "Missed" for them, not "Completed".
        status = _trainee_status_for(conf, attendance_by_conf.get(conf.conferenceUid))

        position = session_rank.get(conf.conferenceUid) if post else None
        rank_label = str(position) if position is not None else None

        started_at = _parse_date(conf.conferenceDate)
        rows.append(
            DashboardTrainingRow(
                conferenceUid=conf.conferenceUid,
                title=conf.suiteTitle or conf.trainingType or "Training Session",
                date=started_at.strftime("%d %b %Y") if started_at else conf.conferenceDate,
                rawDate=conf.conferenceDate,
                day=started_at.strftime("(%a)") if started_at else None,
                status=status,
                postTestScore=_fmt_score(post.totalScore, post.maxScore) if post else None,
                quizScore=_fmt_score(quiz.totalScore, quiz.maxScore) if quiz else None,
                rank=rank_label,
                rankScope="Session" if rank_label else None,
            )
        )

    return rows
