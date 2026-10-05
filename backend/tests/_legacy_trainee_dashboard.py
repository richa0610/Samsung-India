"""The trainee dashboard's ranking pool and training rows as they were before Phase 5 (loaded every
submitted result into Python; one results query per training row) - kept only as the reference
the SQL/cached versions are proven equal to (tests/test_phase5_aggregates.py). Never imported by
the app."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories import assessment_repository, attendance_repository, conference_repository
from app.schemas.session import DashboardTrainingRow
from app.services.module_flow import live_quiz_suite_uid
from app.services.trainee_dashboard_service import (
    _fmt_score,
    _num,
    _parse_date,
    _test_and_quiz_suites,
    _trainee_status_for,
)
from app.utils.status import title_status
from tests import _legacy_queries as legacy_queries


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
    results = legacy_queries.list_all_submitted_results(db)
    conf_uids = {r.conferenceUid for r in results}
    confs = {
        c.conferenceUid: c
        for c in conference_repository.list_by_uids(db, conf_uids)
        if title_status(c.conferenceStatus) != "Cancelled"
    }
    accepted = {uid: _test_and_quiz_suites(c) for uid, c in confs.items()}
    present_pairs = set(legacy_queries.list_present_pairs(db, list(conf_uids)))

    pool_uids = legacy_queries.list_attended_trainee_uids(db)
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
