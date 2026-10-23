from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import FINISHED_RESULT_STATUSES, RESULT_RETEST, RESULT_STARTED
from app.models.conference import Conference
from app.models.quiz import Assessment, AssessmentResult, AssessmentSuite, Question


def commit(db: Session) -> None:
    db.commit()


def finished(status_column=AssessmentResult.status):
    """SQL condition: a finished result - "Completed", or "Submitted" from before 2026-10-16
    (core/constants.FINISHED_RESULT_STATUSES). `status_column` for an aliased results table."""
    return status_column.in_(FINISHED_RESULT_STATUSES)


# --- AssessmentSuite -------------------------------------------------------

def list_approved_suites(db: Session) -> list[AssessmentSuite]:
    return (
        db.query(AssessmentSuite)
        .filter(AssessmentSuite.status == "Approved")
        .order_by(AssessmentSuite.assessment_type, AssessmentSuite.courseName)
        .all()
    )


def get_suite_by_uid(db: Session, suite_uid: str) -> Optional[AssessmentSuite]:
    return db.query(AssessmentSuite).filter(AssessmentSuite.assessmentSuiteUid == suite_uid).first()


def create_suite(db: Session, suite: AssessmentSuite) -> AssessmentSuite:
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return suite


def save_suite(db: Session) -> None:
    db.commit()


# --- Question ----------------------------------------------------------------

def list_questions_for_suite(db: Session, suite_uid: str) -> list[Question]:
    return db.query(Question).filter(Question.assessmentSuiteUid == suite_uid).order_by(Question.sort_order).all()


def count_questions_for_suite(db: Session, suite_uid: str) -> int:
    return db.query(Question).filter(Question.assessmentSuiteUid == suite_uid).count()


def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()


def add_question(db: Session, question: Question) -> None:
    db.add(question)


def delete_question(db: Session, question_id: int, suite_uid: str) -> None:
    db.query(Question).filter(Question.id == question_id, Question.assessmentSuiteUid == suite_uid).delete()


# --- Assessment (submitted answers) ------------------------------------------

def add_answer(db: Session, answer: Assessment) -> None:
    db.add(answer)


# --- Assessment: Live Quiz per-question answers ------------------------------

def get_answer(db: Session, conference_uid: str, trainee_uid: str, question_id: int) -> Optional[Assessment]:
    return (
        db.query(Assessment)
        .filter(
            Assessment.conferenceUid == conference_uid,
            Assessment.traineeUid == trainee_uid,
            Assessment.questionId == str(question_id),
        )
        .first()
    )


def upsert_answer(
    db: Session,
    *,
    conference_uid: str,
    trainee_uid: str,
    suite_uid: str,
    question_id: int,
    selected_option: Optional[str],
    response_ms: Optional[int] = None,
) -> None:
    """One row per (conference, trainee, question) - an existing row is updated
    in place, never stacked. Whether a row may be replaced at all is the
    caller's rule: the Live Quiz never replaces a recorded answer
    (live_quiz_service.submit_live_answer).
    `response_ms` (Live Quiz) is the time from question broadcast to this
    answer; stored as a bare integer in `remarks` (the schema's per-row notes
    field - no dedicated column) and summed at scoring time for the tie-break."""
    existing = get_answer(db, conference_uid, trainee_uid, question_id)
    if existing:
        existing.selectedOption = selected_option
        if response_ms is not None:
            existing.remarks = str(response_ms)
    else:
        db.add(
            Assessment(
                assessmentSuiteUid=suite_uid,
                conferenceUid=conference_uid,
                traineeUid=trainee_uid,
                questionId=str(question_id),
                selectedOption=selected_option,
                remarks=str(response_ms) if response_ms is not None else None,
            )
        )
    db.commit()


def list_answers_for_conference_suite(db: Session, conference_uid: str, suite_uid: str) -> list[Assessment]:
    return (
        db.query(Assessment)
        .filter(Assessment.conferenceUid == conference_uid, Assessment.assessmentSuiteUid == suite_uid)
        .all()
    )


def list_answers_for_trainee_suite(
    db: Session, conference_uid: str, trainee_uid: str, suite_uid: str
) -> list[Assessment]:
    """One trainee's answers for one conference+suite - the Training Detail
    screen's per-question review (their pick vs. the correct answer)."""
    return (
        db.query(Assessment)
        .filter(
            Assessment.conferenceUid == conference_uid,
            Assessment.traineeUid == trainee_uid,
            Assessment.assessmentSuiteUid == suite_uid,
        )
        .all()
    )


def responders_by_question(db: Session, conference_uid: str, suite_uid: str) -> dict[str, int]:
    """questionId -> number of distinct trainees who have answered it, for the
    trainer's Live Studio per-row response counts."""
    rows = (
        db.query(Assessment.questionId, func.count(func.distinct(Assessment.traineeUid)))
        .filter(Assessment.conferenceUid == conference_uid, Assessment.assessmentSuiteUid == suite_uid)
        .group_by(Assessment.questionId)
        .all()
    )
    return dict(rows)


# --- AssessmentResult ----------------------------------------------------------

def next_attempt_number(db: Session, trainee_uid: str, suite_uid: str) -> int:
    """The next `attemptNumber` for this trainee + suite. Uses MAX, not COUNT,
    so it stays correct even after older attempt rows have been deleted (dev
    cleanup, a reset script, etc.) - COUNT + 1 would then collide with the
    `unique_attempt` UNIQUE(traineeUid, assessmentSuiteUid, attemptNumber)
    constraint and make the submit fail with a bare IntegrityError (500)."""
    highest = (
        db.query(func.max(AssessmentResult.attemptNumber))
        .filter(
            AssessmentResult.traineeUid == trainee_uid,
            AssessmentResult.assessmentSuiteUid == suite_uid,
        )
        .scalar()
    )
    return int(highest or 0) + 1


def add_result(db: Session, result: AssessmentResult) -> None:
    db.add(result)


def has_submitted_result(db: Session, conference_uid: str, trainee_uid: str) -> bool:
    return (
        db.query(AssessmentResult.id)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.traineeUid == trainee_uid,
            finished(),
        )
        .first()
        is not None
    )


def get_latest_result(
    db: Session, conference_uid: str, trainee_uid: str, suite_uid: str
) -> Optional[AssessmentResult]:
    return (
        db.query(AssessmentResult)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.traineeUid == trainee_uid,
            AssessmentResult.assessmentSuiteUid == suite_uid,
            finished(),
        )
        .order_by(AssessmentResult.attemptNumber.desc())
        .first()
    )


def _latest_with_status(
    db: Session, conference_uid: str, trainee_uid: str, suite_uid: str, status: str
) -> Optional[AssessmentResult]:
    return (
        db.query(AssessmentResult)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.traineeUid == trainee_uid,
            AssessmentResult.assessmentSuiteUid == suite_uid,
            AssessmentResult.status == status,
        )
        .order_by(AssessmentResult.attemptNumber.desc())
        .first()
    )


def get_started_result(
    db: Session, conference_uid: str, trainee_uid: str, suite_uid: str
) -> Optional[AssessmentResult]:
    """The trainee's unfinished attempt at this test here: the row written (status "Started", with
    startedAt) when they first opened its questions, which their submit then completes."""
    return _latest_with_status(db, conference_uid, trainee_uid, suite_uid, RESULT_STARTED)


def get_retest_result(
    db: Session, conference_uid: str, trainee_uid: str, suite_uid: str
) -> Optional[AssessmentResult]:
    """The trainee's retest of this test of a session they missed (core/constants.RESULT_RETEST)."""
    return _latest_with_status(db, conference_uid, trainee_uid, suite_uid, RESULT_RETEST)


def submitted_trainees_by_suite(db: Session, conference_uid: str, suite_uids: list[str]) -> dict[str, set[str]]:
    """{suite: trainees with a Submitted result for it in this training} - one query, however many
    suites. A suite nobody submitted is left out."""
    if not suite_uids:
        return {}
    rows = (
        db.query(AssessmentResult.assessmentSuiteUid, AssessmentResult.traineeUid)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.assessmentSuiteUid.in_(suite_uids),
            finished(),
        )
        .distinct()
        .all()
    )
    submitted: dict[str, set[str]] = {}
    for suite_uid, trainee_uid in rows:
        submitted.setdefault(suite_uid, set()).add(trainee_uid)
    return submitted


def list_results_for_conference_suite(db: Session, conference_uid: str, suite_uid: str) -> list[AssessmentResult]:
    return (
        db.query(AssessmentResult)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.assessmentSuiteUid == suite_uid,
            finished(),
        )
        .order_by(AssessmentResult.attemptNumber.desc())
        .all()
    )


def list_results_for_conferences(db: Session, conference_uids: list[str]) -> list[AssessmentResult]:
    if not conference_uids:
        return []
    return (
        db.query(AssessmentResult)
        .filter(AssessmentResult.conferenceUid.in_(conference_uids), finished())
        .order_by(AssessmentResult.attemptNumber.desc())
        .all()
    )


def list_results_for_trainee(db: Session, trainee_uid: str) -> list[AssessmentResult]:
    """The trainee's finished results (a test opened but not yet submitted is "Started" - not a result)."""
    return (
        db.query(AssessmentResult)
        .filter(AssessmentResult.traineeUid == trainee_uid, finished())
        .order_by(AssessmentResult.submittedAt.desc())
        .all()
    )


def latest_post_test_results_for_pairs(db: Session, pairs: set[tuple[str, str]]) -> dict[tuple[str, str], object]:
    """{(conferenceUid, traineeUid): the latest Submitted attempt of that
    conference's OWN post-test suite} for just the given pairs (one page of the
    attendance list). Same rule as the Python list: highest attempt number wins,
    and a result for any other suite - or for a conference with no post-test
    suite - is ignored."""
    if not pairs:
        return {}
    rows = db.execute(
        select(
            AssessmentResult.conferenceUid,
            AssessmentResult.traineeUid,
            AssessmentResult.totalScore,
            AssessmentResult.maxScore,
            AssessmentResult.percentage,
        )
        .join(
            Conference,
            and_(
                Conference.conferenceUid == AssessmentResult.conferenceUid,
                AssessmentResult.assessmentSuiteUid == Conference.postAssessmentUid,
            ),
        )
        .where(
            finished(),
            or_(*[and_(AssessmentResult.conferenceUid == c, AssessmentResult.traineeUid == t) for c, t in pairs]),
        )
        .order_by(AssessmentResult.attemptNumber.desc())
    ).all()
    latest: dict[tuple[str, str], object] = {}
    for row in rows:
        latest.setdefault((row.conferenceUid, row.traineeUid), row)
    return latest
