import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.quiz import Assessment, AssessmentResult
from app.models.trainee import Trainee
from app.repositories import assessment_repository
from app.schemas.assessment import AssessmentQuestionsOut, QuestionOut, SubmitRequest, SubmitResult


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


def get_questions(db: Session, suite_uid: str) -> AssessmentQuestionsOut:
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


def submit_assessment(db: Session, trainee: Trainee, suite_uid: str, payload: SubmitRequest) -> SubmitResult:
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    if not questions:
        raise not_found("No questions found for this assessment")

    now = datetime.now()

    for answer in payload.answers:
        assessment_repository.add_answer(
            db,
            Assessment(
                assessmentSuiteUid=suite_uid,
                conferenceUid=payload.conferenceUid,
                traineeUid=trainee.traineeUid,
                questionId=str(answer.questionId),
                selectedOption=answer.selectedOption,
            ),
        )

    total_score, max_score, percentage, correct_count = score_answers(
        questions, {a.questionId: a.selectedOption for a in payload.answers}
    )

    assessment_repository.add_result(
        db,
        AssessmentResult(
            conferenceUid=payload.conferenceUid,
            traineeUid=trainee.traineeUid,
            assessmentSuiteUid=suite_uid,
            attemptNumber=assessment_repository.next_attempt_number(db, trainee.traineeUid, suite_uid),
            totalScore=total_score,
            maxScore=max_score,
            percentage=percentage,
            startedAt=now,
            submittedAt=now,
            status="Submitted",
        ),
    )
    assessment_repository.commit(db)

    return SubmitResult(
        totalScore=total_score,
        maxScore=max_score,
        percentage=percentage,
        correctCount=correct_count,
        totalQuestions=len(payload.answers),
    )
