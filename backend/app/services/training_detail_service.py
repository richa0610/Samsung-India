"""Builds the trainee-facing Training Detail screen (`GET
/sessions/{conferenceUid}/detail`) - one past training's full module
breakdown, with a question-by-question review for every assessment-type
module the trainee attempted. Tap-through target from the Training History
screen's table rows.
"""

import json

from sqlalchemy.orm import Session

from app.core.constants import MODULE_LABELS
from app.core.exceptions import not_found
from app.models.conference import Conference
from app.models.quiz import Question
from app.models.trainee import Trainee
from app.repositories import assessment_repository, attendance_repository, conference_repository
from app.schemas.assessment import QuestionOption
from app.schemas.session import TrainingDetailOut, TrainingModuleDetail, TrainingQuestionAttempt
from app.services import session_service
from app.services.module_flow import configured_modules, live_quiz_suite_uid
from app.services.trainee_dashboard_service import _fmt_score, _trainee_status_for


def _suite_for_module(conference: Conference, module_key: str) -> str | None:
    if module_key == "STANDARD_TEST":
        return conference.postAssessmentUid
    if module_key == "LIVE_QUIZ":
        return live_quiz_suite_uid(conference)
    if module_key == "SURVEY":
        return conference.surveyUid
    return None


def _question_options(question: Question) -> list[QuestionOption]:
    try:
        raw = json.loads(question.options) if question.options else []
    except ValueError:
        raw = []
    return [QuestionOption(id=str(o.get("id")), text=o.get("text", "")) for o in raw if isinstance(o, dict)]


def _attendance_module(attendance, overall_status: str) -> TrainingModuleDetail:
    # `overall_status` (Missed/Absent/Ongoing/Scheduled/Completed) already
    # reflects this trainee's attendance outcome for the whole training - the
    # only refinement needed here is "Present" -> "Completed" specifically
    # for this module's own card.
    status = "Completed" if attendance and attendance.status == "Present" else overall_status
    return TrainingModuleDetail(
        key="ATTENDANCE",
        name=MODULE_LABELS["ATTENDANCE"],
        status=status,
        completedAt=attendance.markedOn if attendance else None,
    )


def _assessment_module(
    db: Session, conference_uid: str, trainee_uid: str, module_key: str, suite_uid: str | None, session_over: bool
) -> TrainingModuleDetail:
    if not suite_uid:
        return TrainingModuleDetail(key=module_key, name=MODULE_LABELS[module_key], status="Missed")

    result = assessment_repository.get_latest_result(db, conference_uid, trainee_uid, suite_uid)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    answers_by_qid = {
        a.questionId: a
        for a in assessment_repository.list_answers_for_trainee_suite(db, conference_uid, trainee_uid, suite_uid)
    }

    attempts: list[TrainingQuestionAttempt] = []
    for q in questions:
        answer = answers_by_qid.get(str(q.id))
        selected_id = answer.selectedOption if answer else None
        options = _question_options(q)
        options_by_id = {o.id: o.text for o in options}
        correct_id = q.correct_answer
        # Surveys have no right answer - correct_answer is unset, so both
        # correctOptionId/Text stay None and isCorrect is never true.
        attempts.append(
            TrainingQuestionAttempt(
                id=q.id,
                question=q.question or "",
                options=options,
                selectedOptionId=selected_id,
                selectedOptionText=options_by_id.get(selected_id) if selected_id else None,
                correctOptionId=correct_id,
                correctOptionText=options_by_id.get(correct_id) if correct_id else None,
                isCorrect=bool(selected_id) and bool(correct_id) and selected_id == correct_id,
                answered=answer is not None,
                points=float(q.points or 0),
            )
        )

    if result:
        status = "Completed"
    elif session_over:
        status = "Missed"
    else:
        status = "Scheduled"

    return TrainingModuleDetail(
        key=module_key,
        name=MODULE_LABELS[module_key],
        status=status,
        score=_fmt_score(result.totalScore, result.maxScore) if result else None,
        completedAt=result.submittedAt.strftime("%Y-%m-%d %H:%M:%S") if result and result.submittedAt else None,
        questions=attempts,
    )


def get_training_detail(db: Session, trainee: Trainee, conference_uid: str) -> TrainingDetailOut:
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")

    attendance = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee.traineeUid)
    overall_status = _trainee_status_for(conference, attendance)
    session_over = session_service._session_is_over(conference)

    modules: list[TrainingModuleDetail] = []
    for module_key in configured_modules(conference):
        if module_key == "ATTENDANCE":
            modules.append(_attendance_module(attendance, overall_status))
        else:
            suite_uid = _suite_for_module(conference, module_key)
            modules.append(
                _assessment_module(db, conference_uid, trainee.traineeUid, module_key, suite_uid, session_over)
            )

    location = ", ".join(filter(None, [conference.district, conference.state])) or None

    return TrainingDetailOut(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or "Training Session",
        date=conference.conferenceDate,
        location=location,
        trainerName=conference.trainerName,
        status=overall_status,
        modules=modules,
    )
