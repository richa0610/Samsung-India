import json

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, not_found
from app.models.quiz import Assessment, AssessmentResult
from app.models.trainee import Trainee
from app.repositories import assessment_repository
from app.schemas.assessment import AssessmentQuestionsOut, QuestionOut, SubmitRequest, SubmitResult
from app.services import trainee_access
from app.services.activity_log_service import log_activity
from app.services.module_flow import mark_checkout_if_last_module
from app.utils.date_utils import utc_now


def score_answers(questions: list, answers_by_qid: dict[int, str | None]) -> tuple[int, int, float, int]:
   
    points_by_id = {q.id: (q.points or 0) for q in questions}
    correct_by_id = {q.id: q.correct_answer for q in questions}
    max_score = sum(points_by_id.values())

    total_score = 0
    correct_count = 0
    for question_id, selected in answers_by_qid.items():
        if selected is not None and selected == correct_by_id.get(question_id):
            total_score += points_by_id.get(question_id, 0)
            correct_count += 1

    percentage = round((total_score / max_score) * 100, 2) if max_score else 0.0
    return total_score, max_score, percentage, correct_count


def get_questions(db: Session, trainee: Trainee, suite_uid: str, conference_uid: str) -> AssessmentQuestionsOut:
    """The questions of a test the trainee is taking right now (trainee_access.open_assessment:
    Present, the suite is that session's Standard Test or Survey, and that module is open) - never
    another session's test, and never before it opens. Correct answers are never included."""
    trainee_access.open_assessment(db, trainee, conference_uid, suite_uid)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    if not questions:
        raise not_found("No questions found for this assessment")

    suite = assessment_repository.get_suite_by_uid(db, suite_uid)

    return AssessmentQuestionsOut(
        title=(suite.examTitle or suite.courseName) if suite else None,
        testTime=suite.testTime if suite else None,
        questions=[
            QuestionOut(
                id=q.id,
                question=q.question or "",
                question_type=q.question_type,
                sort_order=q.sort_order or 0,
                options=json.loads(q.options) if q.options else [],
            )
            for q in questions
        ],
    )


def _validated_answers(questions: list, payload: SubmitRequest) -> dict[int, str | None]:
    """Answers keyed by question: each question of this suite at most once. An answer for a
    question outside the suite, or two answers for one question (which used to count its points
    twice), is refused rather than scored."""
    suite_question_ids = {q.id for q in questions}
    answers: dict[int, str | None] = {}
    for answer in payload.answers:
        if answer.questionId not in suite_question_ids:
            raise bad_request("An answer refers to a question that isn't part of this assessment")
        if answer.questionId in answers:
            raise bad_request("Each question can only be answered once")
        answers[answer.questionId] = answer.selectedOption
    return answers


def _result_out(questions: list, result: AssessmentResult, answers_by_qid: dict[int, str | None]) -> SubmitResult:
    _, _, _, correct_count = score_answers(questions, answers_by_qid)
    return SubmitResult(
        totalScore=float(result.totalScore),
        maxScore=float(result.maxScore),
        percentage=float(result.percentage),
        correctCount=correct_count,
        totalQuestions=len(answers_by_qid),
    )


def submit_assessment(db: Session, trainee: Trainee, suite_uid: str, payload: SubmitRequest) -> SubmitResult:
    """Scores and stores a trainee's submission for the test open in their session.

    One submission per trainee, session and test - the session screen never offers a completed
    module again (session_service's isLive). A repeat (a double tap, or a retry after a lost
    response) returns the stored result instead of saving a second attempt; the trainee's
    attendance row is locked for the transaction, so concurrent repeats run one after another."""
    conference, module_key = trainee_access.open_assessment(db, trainee, payload.conferenceUid, suite_uid, lock=True)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    if not questions:
        raise not_found("No questions found for this assessment")

    existing = assessment_repository.get_latest_result(db, conference.conferenceUid, trainee.traineeUid, suite_uid)
    if existing is not None:
        stored = assessment_repository.list_answers_for_trainee_suite(db, conference.conferenceUid, trainee.traineeUid, suite_uid)
        assessment_repository.commit(db)  # releases the row lock
        return _result_out(questions, existing, {int(a.questionId): a.selectedOption for a in stored})

    answers_by_qid = _validated_answers(questions, payload)
    now = utc_now()
    for question_id, selected in answers_by_qid.items():
        assessment_repository.add_answer(
            db,
            Assessment(
                assessmentSuiteUid=suite_uid,
                conferenceUid=conference.conferenceUid,
                traineeUid=trainee.traineeUid,
                questionId=str(question_id),
                selectedOption=selected,
            ),
        )

    total_score, max_score, percentage, correct_count = score_answers(questions, answers_by_qid)
    result = AssessmentResult(
        conferenceUid=conference.conferenceUid,
        traineeUid=trainee.traineeUid,
        assessmentSuiteUid=suite_uid,
        attemptNumber=assessment_repository.next_attempt_number(db, trainee.traineeUid, suite_uid),
        totalScore=total_score,
        maxScore=max_score,
        percentage=percentage,
        startedAt=now,
        submittedAt=now,
        status="Submitted",
    )
    assessment_repository.add_result(db, result)
    # The session's last module done -> the trainee is checked out (same rule as the Attendance
    # and Live Quiz modules; module_flow.mark_checkout_if_last_module).
    mark_checkout_if_last_module(db, conference, trainee.traineeUid, module_key)
    assessment_repository.commit(db)

    log_activity(
        db,
        action="SUBMIT_ASSESSMENT",
        username=str(trainee.phone),
        role="trainee",
        remarks=f"Submitted {suite_uid} for {conference.conferenceUid}: {total_score}/{max_score} ({percentage}%)",
    )
    return SubmitResult(
        totalScore=total_score,
        maxScore=max_score,
        percentage=percentage,
        correctCount=correct_count,
        totalQuestions=len(answers_by_qid),
    )
