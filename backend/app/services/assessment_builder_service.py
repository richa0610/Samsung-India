import re
import json

from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.admin import Admin
from app.models.quiz import AssessmentSuite, Question
from app.repositories import assessment_repository
from app.services import answer_numbers
from app.services.account_ids import account_name
from app.utils import question_format
from app.schemas.training import (
    AssessmentSuiteCreate,
    AssessmentSuiteDetail,
    AssessmentSuiteOut,
    QuestionCreate,
    QuestionOptionIn,
    QuestionOut,
)


_SURVEY_WORDS = re.compile(r"survey|feedback", re.I)
_TEST_WORDS = re.compile(r"\b(test|exam)\b", re.I)


def suite_module(suite: AssessmentSuite) -> str:
    """Which session-flow module a question set belongs to. `assessment_type`
    alone can't tell: it defaults to "Quiz" for every set (a Post Test set is
    often stored as "Quiz" too), so the category AND the title are read
    together - survey/feedback -> survey; the word "test"/"exam" (Post Test,
    Standard Test) -> standardTest; everything else -> liveQuiz."""
    text = f"{suite.assessment_type or ''} {suite.examTitle or suite.courseName or ''}"
    if _SURVEY_WORDS.search(text):
        return "survey"
    if _TEST_WORDS.search(text):
        return "standardTest"
    return "liveQuiz"


def suite_category(suite) -> str:
    """The picker category a question set is listed under - its `assessment_type`."""
    return suite.assessment_type or "Uncategorised"


def list_assessment_suites(db: Session, module: str | None = None) -> list[AssessmentSuiteOut]:
    """Powers the Category / Select Question Set pickers in the trainer's
    session-flow builder. `assessment_type` doubles as the category
    grouping (e.g. "Quiz", "Survey", "Post Test")."""
    suites = assessment_repository.list_approved_suites(db)
    if module:
        suites = [suite for suite in suites if suite_module(suite) == module]
    return [
        AssessmentSuiteOut(
            assessmentSuiteUid=suite.assessmentSuiteUid,
            category=suite_category(suite),
            name=suite.examTitle or suite.courseName or "Untitled",
            noOfQuestion=suite.noOfQuestion or 0,
        )
        for suite in suites
    ]


def _question_to_out(q: Question) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        question=q.question or "",
        questionType=q.question_type,
        options=[QuestionOptionIn(**o) for o in question_format.options(q)],
        # Saved as the option's number (answer_numbers); the builder shows the option's id.
        correctAnswer=answer_numbers.correct_option_id(q),
        points=q.points or 0,
        timerSeconds=question_format.timer_seconds(q),
        explanation=question_format.explanation(q),
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


def _existing_suite(db: Session, suite_uid: str) -> AssessmentSuite:
    """The question set, or 404 when there is none with this ID."""
    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    if not suite:
        raise not_found("Assessment suite not found")
    return suite


def get_assessment_suite(db: Session, suite_uid: str) -> AssessmentSuiteDetail:
    return _suite_to_detail(db, _existing_suite(db, suite_uid))


def add_question(db: Session, suite_uid: str, payload: QuestionCreate, admin: Admin) -> AssessmentSuiteDetail:
    """Adds a question, stored the other system's way (user, 2026-10-17 - utils/question_format):
    plain-text options, the answer key as the correct option's position (["2"]), its timer in
    settings, the explanation in `descriptions`, `updatedBy` = the adding admin's name."""
    suite = _existing_suite(db, suite_uid)
    next_order = assessment_repository.count_questions_for_suite(db, suite_uid) + 1

    # The builder names the correct option by the id it gave it; the key keeps only its position.
    option_ids = [option.id for option in payload.options]
    key = option_ids.index(payload.correctAnswer) + 1 if payload.correctAnswer in option_ids else None
    question = Question(
        assessmentSuiteUid=suite_uid,
        question=payload.question,
        question_type=payload.questionType,
        sort_order=next_order,
        options=question_format.stored_options(option.text for option in payload.options),
        correct_answer=question_format.stored_key([key] if key else []),
        points=payload.points,
        settings=question_format.stored_settings(payload.timerSeconds),
        descriptions=(payload.explanation or "").strip() or None,
        updatedBy=account_name(admin),
        status="Approved",
    )
    assessment_repository.add_question(db, question)
    suite.noOfQuestion = next_order
    assessment_repository.save_suite(db)
    return _suite_to_detail(db, suite)


def delete_question(db: Session, suite_uid: str, question_id: int) -> AssessmentSuiteDetail:
    suite = _existing_suite(db, suite_uid)
    assessment_repository.delete_question(db, question_id, suite_uid)
    suite.noOfQuestion = assessment_repository.count_questions_for_suite(db, suite_uid)
    assessment_repository.save_suite(db)
    return _suite_to_detail(db, suite)
