import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.constants import RESULT_COMPLETED, RESULT_STARTED
from app.core.exceptions import bad_request, not_found
from app.core.request_context import caller_device
from app.models.quiz import Assessment, AssessmentResult
from app.models.trainee import Trainee
from app.repositories import assessment_repository
from app.schemas.assessment import AssessmentQuestionsOut, QuestionOut, SubmitRequest, SubmitResult
from app.services import answer_numbers, trainee_access
from app.services.activity_log_service import log_activity
from app.services.module_flow import mark_checkout_if_last_module
from app.utils import question_format
from app.utils.date_utils import utc_now


def score_answers(questions: list, answers_by_qid: dict[int, str | None]) -> tuple[int, int, float, int]:
    """(total, max, percentage, correct count) for answers as saved - option numbers, see
    answer_numbers - keyed by question."""
    questions_by_id = {q.id: q for q in questions}
    max_score = sum(q.points or 0 for q in questions)

    total_score = 0
    correct_count = 0
    for question_id, selected in answers_by_qid.items():
        question = questions_by_id.get(question_id)
        if question is not None and answer_numbers.is_correct(question, selected):
            total_score += question.points or 0
            correct_count += 1

    percentage = round((total_score / max_score) * 100, 2) if max_score else 0.0
    return total_score, max_score, percentage, correct_count


def answers_snapshot(
    questions: list,
    answers_by_qid: dict[int, str | None],
    *,
    scored: bool,
    response_ms_by_qid: dict[int, int] | None = None,
) -> str:
    """A result's `answersSnapshot`, in the other system's shape (user, 2026-10-16): every question of
    the set by its id - {"143": {"answer": "2", "is_correct": true, "points": 1}, ...} - with the answer
    as saved ("" when unanswered), whether it is right and the points it earned. A Survey is never
    scored: false and 0 (user). A Live Quiz entry also carries its answer time, "responseMs", which the
    leaderboard's tie-break adds up."""
    snapshot = {}
    for question in questions:
        answer = answers_by_qid.get(question.id)
        correct = scored and answer_numbers.is_correct(question, answer)
        entry = {"answer": answer or "", "is_correct": correct, "points": (question.points or 0) if correct else 0}
        if response_ms_by_qid and question.id in response_ms_by_qid:
            entry["responseMs"] = response_ms_by_qid[question.id]
        snapshot[str(question.id)] = entry
    return json.dumps(snapshot)


def _marks(questions: list, answers_by_qid: dict[int, str | None], module_key: str) -> tuple[int, int, float, int]:
    """(total, max, percentage, correct count) for a submission. A Survey has no right answers: it
    is submitted, never scored (module_flow.scored_suite_uids), so all four are 0."""
    if module_key == "SURVEY":
        return 0, 0, 0.0, 0
    return score_answers(questions, answers_by_qid)


def _seconds_between(started_at, ended_at) -> int:
    """How long the test took; 0 when its start wasn't recorded."""
    return max(0, int((ended_at - started_at).total_seconds())) if started_at else 0


def get_questions(db: Session, trainee: Trainee, suite_uid: str, conference_uid: str) -> AssessmentQuestionsOut:
    """The questions of a test the trainee is taking right now (trainee_access.open_assessment:
    Present, the suite is that session's Standard Test or Survey, and that module is open) - never
    another session's test, and never before it opens. Correct answers are never included.
    Opening them is when the trainee starts the test (see record_start)."""
    conference, _ = trainee_access.open_assessment(db, trainee, conference_uid, suite_uid, lock=True)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    if not questions:
        raise not_found("No questions found for this assessment")

    suite = assessment_repository.get_suite_by_uid(db, suite_uid)

    questions_out = AssessmentQuestionsOut(
        title=(suite.examTitle or suite.courseName) if suite else None,
        testTime=suite.testTime if suite else None,
        questions=[
            QuestionOut(
                id=q.id,
                question=q.question or "",
                question_type=q.question_type,
                sort_order=q.sort_order or 0,
                options=question_format.options(q),
            )
            for q in questions
        ],
    )
    # Built first: the commit expires the loaded questions. It also releases the attendance-row lock
    # open_assessment took, so two opens at once can't both add a start.
    record_start(db, conference.conferenceUid, trainee.traineeUid, suite_uid, utc_now())
    assessment_repository.commit(db)
    return questions_out


def record_start(db: Session, conference_uid: str, trainee_uid: str, suite_uid: str, started_at: datetime) -> None:
    """When the trainee began this test or quiz, remembered once - as a "Started" result row (the
    table's own Started -> Completed lifecycle) that their scoring then completes
    (result_to_complete), so the result carries when it really began. Standard Test / Survey: when
    they first opened the questions. Live Quiz: when the first question they answered (or timed out
    on) went live. A later call keeps the first time; one after the result is submitted records
    nothing. Not committed - the caller commits, holding the trainee's attendance-row lock until then
    so two calls at once can't both add a row."""
    already = assessment_repository.get_latest_result(
        db, conference_uid, trainee_uid, suite_uid
    ) or assessment_repository.get_started_result(db, conference_uid, trainee_uid, suite_uid)
    if already is None:
        assessment_repository.add_result(
            db,
            AssessmentResult(
                conferenceUid=conference_uid,
                traineeUid=trainee_uid,
                assessmentSuiteUid=suite_uid,
                attemptNumber=assessment_repository.next_attempt_number(db, trainee_uid, suite_uid),
                startedAt=started_at,
                status=RESULT_STARTED,
                **caller_device(),
            ),
        )


def result_to_complete(db: Session, conference_uid: str, trainee_uid: str, suite_uid: str) -> AssessmentResult:
    """The row a submission fills in: the trainee's "Started" row here (record_start) - or, when no
    start was recorded (begun before starts were), a new row whose start is unknown, added to the
    session. The caller sets its scores and marks it Completed."""
    result = assessment_repository.get_started_result(db, conference_uid, trainee_uid, suite_uid)
    if result is None:
        result = AssessmentResult(
            conferenceUid=conference_uid,
            traineeUid=trainee_uid,
            assessmentSuiteUid=suite_uid,
            attemptNumber=assessment_repository.next_attempt_number(db, trainee_uid, suite_uid),
        )
        assessment_repository.add_result(db, result)
    return result


def _answers_to_save(questions: list, payload: SubmitRequest, module_key: str) -> dict[int, str | None]:
    """Answers keyed by question, as they are saved: each question of this suite at most once. An
    answer for a question outside the suite, or two answers for one question (which used to count
    its points twice), is refused rather than scored. A test answer is saved as its option number
    (answer_numbers); a Survey answer keeps the option the app sent."""
    questions_by_id = {q.id: q for q in questions}
    answers: dict[int, str | None] = {}
    for answer in payload.answers:
        question = questions_by_id.get(answer.questionId)
        if question is None:
            raise bad_request("An answer refers to a question that isn't part of this assessment")
        if answer.questionId in answers:
            raise bad_request("Each question can only be answered once")
        answers[answer.questionId] = (
            answer_numbers.number_for(question, answer.selectedOption)
        )
    return answers


def _result_out(
    questions: list, result: AssessmentResult, answers_by_qid: dict[int, str | None], module_key: str
) -> SubmitResult:
    _, _, _, correct_count = _marks(questions, answers_by_qid, module_key)
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
        return _result_out(questions, existing, {int(a.questionId): a.selectedOption for a in stored}, module_key)

    answers_by_qid = _answers_to_save(questions, payload, module_key)
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

    total_score, max_score, percentage, correct_count = _marks(questions, answers_by_qid, module_key)
    result = result_to_complete(db, conference.conferenceUid, trainee.traineeUid, suite_uid)
    result.totalScore, result.maxScore, result.percentage = total_score, max_score, percentage
    result.submittedAt = now
    result.durationSeconds = _seconds_between(result.startedAt, now)
    result.answersSnapshot = answers_snapshot(questions, answers_by_qid, scored=module_key != "SURVEY")
    result.status = RESULT_COMPLETED
    # The device that submitted it (the one that opened it may have been another).
    for column, value in caller_device().items():
        setattr(result, column, value)
    # The session's last module done -> the trainee is checked out (same rule as the Attendance
    # and Live Quiz modules; module_flow.mark_checkout_if_last_module).
    mark_checkout_if_last_module(db, conference, trainee.traineeUid, module_key)
    assessment_repository.commit(db)

    log_activity(
        db,
        action="SUBMIT_ASSESSMENT",
        username=str(trainee.phone),
        role="trainee",
        remarks=f"Submitted {suite_uid} for {conference.conferenceUid}"
        + ("" if module_key == "SURVEY" else f": {total_score}/{max_score} ({percentage}%)"),
    )
    return SubmitResult(
        totalScore=total_score,
        maxScore=max_score,
        percentage=percentage,
        correctCount=correct_count,
        totalQuestions=len(answers_by_qid),
    )
