"""Builds the trainee-facing Dashboard screen (`GET /sessions/dashboard`).

Everything here is derived from real rows - attendance, assessment_results and
conferences. Nothing is faked: a trainee with no history gets zeros and an
empty training table, not sample data.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.trainee import Trainee
from app.repositories import (
    assessment_repository,
    attendance_repository,
    conference_repository,
    trainee_repository,
)
from app.schemas.session import (
    DashboardMetrics,
    DashboardPerformance,
    DashboardRanking,
    DashboardTrainingRow,
    TraineeDashboardOut,
)
from app.services import session_service
from app.services.module_flow import live_quiz_suite_uid
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
    """This trainee's own outcome for one conference - shared by the
    dashboard metrics and the Training Details table so the two can never
    disagree with each other."""
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


def _rank_in(pool: list[tuple[str, float]], trainee_uid: str) -> tuple[int | None, int, float | None]:
    """`pool` is (uid, percent), sorted best-first. Competition ranking - every
    trainee with a strictly higher percent is ahead; ties share a rank.
    Returns (rank, total, percentile) or (None, total, None) if not in pool."""
    total = len(pool)
    my_percent = next((percent for uid, percent in pool if uid == trainee_uid), None)
    if my_percent is None:
        return None, total, None
    rank = 1 + sum(1 for _uid, percent in pool if percent > my_percent)
    return rank, total, round(rank / total * 100, 1) if total else None


def _ranking_pool(db: Session) -> list[tuple[str, float]]:
    """(traineeUid, percent) for every trainee marked Present in at least one
    training, sorted best-first. `percent` is their aggregate over Standard
    Test + Live Quiz results **for sessions they were Present at**; a trainee
    who attended but has no such marks sits at 0%. A trainee who has a result
    but was never Present anywhere is not ranked."""
    results = assessment_repository.list_all_submitted_results(db)
    conf_uids = {r.conferenceUid for r in results}
    confs = {c.conferenceUid: c for c in conference_repository.list_by_uids(db, conf_uids)}
    accepted = {uid: _test_and_quiz_suites(c) for uid, c in confs.items()}
    present_pairs = set(attendance_repository.list_present_pairs(db, list(conf_uids)))

    pool_uids = attendance_repository.list_attended_trainee_uids(db)
    totals: dict[str, list[float]] = {uid: [0.0, 0.0] for uid in pool_uids}
    for row in results:
        if (
            row.traineeUid in totals
            and (row.conferenceUid, row.traineeUid) in present_pairs
            and row.assessmentSuiteUid in accepted.get(row.conferenceUid, set())
        ):
            totals[row.traineeUid][0] += _num(row.totalScore)
            totals[row.traineeUid][1] += _num(row.maxScore)

    pool = [(uid, (score / maximum * 100) if maximum > 0 else 0.0) for uid, (score, maximum) in totals.items()]
    pool.sort(key=lambda item: item[1], reverse=True)
    return pool


def build_trainee_dashboard(db: Session, trainee: Trainee, limit: int) -> TraineeDashboardOut:
    conference, started, _start_at = session_service._select_current_conference(db, trainee=trainee)

    attendance_rows = attendance_repository.list_for_trainee(db, trainee.traineeUid)
    result_rows = assessment_repository.list_results_for_trainee(db, trainee.traineeUid)

    attendance_by_conf = {row.conferenceUid: row for row in attendance_rows}
    results_by_conf: dict[str, list] = {}
    for row in result_rows:
        results_by_conf.setdefault(row.conferenceUid, []).append(row)

    conf_uids = set(attendance_by_conf) | set(results_by_conf)
    conferences_by_uid = {c.conferenceUid: c for c in conference_repository.list_by_uids(db, conf_uids)}

    # --- metrics ---------------------------------------------------------
    present = sum(1 for row in attendance_rows if row.status == "Present")
    # Assigned/Scheduled = only INCOMING trainings: a roster row still
    # awaiting the trainee to even join ("Pending") whose session hasn't
    # started or ended yet. A "Joined" row means they already showed up, and
    # a "Pending" row whose session is over/live isn't incoming any more -
    # it's "Missed" or "Ongoing" in the table below instead.
    scheduled = sum(
        1
        for uid, att in attendance_by_conf.items()
        if att.status == "Pending" and uid in conferences_by_uid and _trainee_status_for(conferences_by_uid[uid], att) == "Scheduled"
    )
    # Absent = assigned to this trainee but never actually attended - either
    # the trainer explicitly marked them Absent, or the session has since
    # ended while they were only Joined/Pending and never checked in. Mirrors
    # the Training Details table's "Absent"/"Missed" row status exactly, so
    # this number always matches what the table shows.
    absent = sum(
        1
        for uid, att in attendance_by_conf.items()
        if uid in conferences_by_uid and _trainee_status_for(conferences_by_uid[uid], att) in ("Absent", "Missed")
    )
    total_trainings = len(conf_uids)
    metrics = DashboardMetrics(
        totalTrainings=total_trainings, present=present, absent=absent, scheduled=scheduled
    )

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
    cutoff = datetime.now() - timedelta(days=_PERIOD_DAYS)
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
    global_pool = _ranking_pool(db)
    state_uids = trainee_repository.list_uids_in_state(db, trainee.state) if trainee.state else set()
    state_pool = [item for item in global_pool if item[0] in state_uids]

    g_rank, g_total, g_pct = _rank_in(global_pool, trainee.traineeUid)
    s_rank, s_total, s_pct = _rank_in(state_pool, trainee.traineeUid)
    ranking = DashboardRanking(
        globalRank=g_rank,
        globalTotal=g_total,
        globalPercentile=g_pct,
        stateRank=s_rank,
        stateTotal=s_total,
        statePercentile=s_pct,
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
    # Newest first for display.
    ordered = sorted(
        conferences_by_uid.values(),
        key=lambda c: (_parse_date(c.conferenceDate) or datetime.min, c.id),
        reverse=True,
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

        rank_label = None
        if post and conf.postAssessmentUid:
            ranked = sorted(
                assessment_repository.list_results_for_conference_suite(
                    db, conf.conferenceUid, conf.postAssessmentUid
                ),
                key=lambda r: float(r.percentage),
                reverse=True,
            )
            for index, result in enumerate(ranked):
                if result.traineeUid == trainee.traineeUid:
                    rank_label = str(index + 1)
                    break

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

    return rows[:limit]
