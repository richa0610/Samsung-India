import json

from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.quiz import AssessmentSuite, Question
from app.repositories import assessment_repository
from app.schemas.training import (
    AssessmentSuiteCreate,
    AssessmentSuiteDetail,
    AssessmentSuiteOut,
    QuestionCreate,
    QuestionOptionIn,
    QuestionOut,
)


def list_assessment_suites(db: Session) -> list[AssessmentSuiteOut]:
    """Powers the Category / Select Question Set pickers in the trainer's
    session-flow builder. `assessment_type` doubles as the category
    grouping (e.g. "Quiz", "Survey", "Post Test")."""
    suites = assessment_repository.list_approved_suites(db)
    return [
        AssessmentSuiteOut(
            assessmentSuiteUid=suite.assessmentSuiteUid,
            category=suite.assessment_type or "Uncategorised",
            name=suite.examTitle or suite.courseName or "Untitled",
            noOfQuestion=suite.noOfQuestion or 0,
        )
        for suite in suites
    ]


def _question_to_out(q: Question) -> QuestionOut:
    settings = json.loads(q.settings) if q.settings else {}
    return QuestionOut(
        id=q.id,
        question=q.question or "",
        questionType=q.question_type,
        options=[QuestionOptionIn(**o) for o in (json.loads(q.options) if q.options else [])],
        correctAnswer=q.correct_answer,
        points=q.points or 0,
        timerSeconds=settings.get("timerSeconds"),
        explanation=settings.get("explanation"),
        sortOrder=q.sort_order or 0,
    )


def _suite_to_detail(db: Session, suite: AssessmentSuite) -> AssessmentSuiteDetail:
    settings = json.loads(suite.settings) if suite.settings else {}
    questions = assessment_repository.list_questions_for_suite(db, suite.assessmentSuiteUid)
    return AssessmentSuiteDetail(
        assessmentSuiteUid=suite.assessmentSuiteUid,
        title=suite.examTitle or suite.courseName or "Untitled Assessment",
        description=suite.description,
        category=suite.assessment_type or "",
        testTime=suite.testTime,
        type=settings.get("type", "Quiz"),
        noOfQuestion=len(questions),
        questions=[_question_to_out(q) for q in questions],
    )


def create_assessment_suite(db: Session, payload: AssessmentSuiteCreate) -> AssessmentSuiteDetail:
    suite = AssessmentSuite(
        courseName=payload.title,
        examTitle=payload.title,
        description=payload.description,
        assessment_type=payload.category,
        settings=json.dumps({"type": payload.type}),
        testTime=payload.testTime,
        noOfQuestion=0,
        status="Approved",
    )
    suite = assessment_repository.create_suite(db, suite)
    return _suite_to_detail(db, suite)


def get_assessment_suite(db: Session, suite_uid: str) -> AssessmentSuiteDetail:
    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    if not suite:
        raise not_found("Assessment suite not found")
    return _suite_to_detail(db, suite)


def add_question(db: Session, suite_uid: str, payload: QuestionCreate) -> AssessmentSuiteDetail:
    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    if not suite:
        raise not_found("Assessment suite not found")

    next_order = assessment_repository.count_questions_for_suite(db, suite_uid) + 1

    assessment_repository.add_question(
        db,
        Question(
            assessmentSuiteUid=suite_uid,
            question=payload.question,
            question_type=payload.questionType,
            sort_order=next_order,
            options=json.dumps([o.model_dump() for o in payload.options]) if payload.options else None,
            correct_answer=payload.correctAnswer,
            points=payload.points,
            settings=json.dumps({"timerSeconds": payload.timerSeconds, "explanation": payload.explanation}),
            status="Approved",
        ),
    )
    suite.noOfQuestion = next_order
    assessment_repository.save_suite(db)
    return _suite_to_detail(db, suite)


def delete_question(db: Session, suite_uid: str, question_id: int) -> AssessmentSuiteDetail:
    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    if not suite:
        raise not_found("Assessment suite not found")

    assessment_repository.delete_question(db, question_id, suite_uid)
    suite.noOfQuestion = assessment_repository.count_questions_for_suite(db, suite_uid)
    assessment_repository.save_suite(db)
    return _suite_to_detail(db, suite)
