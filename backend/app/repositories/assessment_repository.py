from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.quiz import Assessment, AssessmentResult, AssessmentSuite, Question


def commit(db: Session) -> None:
    db.commit()


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
    """One row per (conference, trainee, question) - a trainee changing their
    pick before the timer locks overwrites the same row rather than stacking.
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


def responders_by_question(db: Session, conference_uid: str, suite_uid: str) -> dict[str, int]:
    """questionId -> number of distinct trainees who have answered it, for the
    trainer's Live Studio per-row response counts."""
    rows = (
        db.query(Assessment.questionId, func.count(func.distinct(Assessment.traineeUid)))
        .filter(Assessment.conferenceUid == conference_uid, Assessment.assessmentSuiteUid == suite_uid)
        .group_by(Assessment.questionId)
        .all()
    )
    return {question_id: count for question_id, count in rows}


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


def get_latest_result(
    db: Session, conference_uid: str, trainee_uid: str, suite_uid: str
) -> Optional[AssessmentResult]:
    return (
        db.query(AssessmentResult)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.traineeUid == trainee_uid,
            AssessmentResult.assessmentSuiteUid == suite_uid,
            AssessmentResult.status == "Submitted",
        )
        .order_by(AssessmentResult.attemptNumber.desc())
        .first()
    )


def list_results_for_conference_suite(db: Session, conference_uid: str, suite_uid: str) -> list[AssessmentResult]:
    return (
        db.query(AssessmentResult)
        .filter(
            AssessmentResult.conferenceUid == conference_uid,
            AssessmentResult.assessmentSuiteUid == suite_uid,
            AssessmentResult.status == "Submitted",
        )
        .order_by(AssessmentResult.attemptNumber.desc())
        .all()
    )


def list_results_for_conferences(db: Session, conference_uids: list[str]) -> list[AssessmentResult]:
    if not conference_uids:
        return []
    return (
        db.query(AssessmentResult)
        .filter(AssessmentResult.conferenceUid.in_(conference_uids), AssessmentResult.status == "Submitted")
        .order_by(AssessmentResult.attemptNumber.desc())
        .all()
    )


def list_submitted_pairs(db: Session, conference_uids: list[str]) -> list[tuple[str, str]]:
    """(conferenceUid, traineeUid) pairs for Submitted results - used to
    compute real headcounts alongside attendance_repository.list_present_pairs."""
    if not conference_uids:
        return []
    rows = (
        db.query(AssessmentResult.conferenceUid, AssessmentResult.traineeUid)
        .filter(AssessmentResult.conferenceUid.in_(conference_uids), AssessmentResult.status == "Submitted")
        .all()
    )
    return [(row.conferenceUid, row.traineeUid) for row in rows]


def list_results_for_trainee(db: Session, trainee_uid: str) -> list[AssessmentResult]:
    return (
        db.query(AssessmentResult)
        .filter(AssessmentResult.traineeUid == trainee_uid)
        .order_by(AssessmentResult.submittedAt.desc())
        .all()
    )


def list_all_submitted_results(db: Session) -> list[AssessmentResult]:
    """Every Submitted result row, all trainees - the dashboard groups these by
    trainee and keeps only the Standard Test + Live Quiz suites for ranking."""
    return db.query(AssessmentResult).filter(AssessmentResult.status == "Submitted").all()
