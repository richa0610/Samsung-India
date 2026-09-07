import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_trainee
from app.dependencies.database import get_db
from app.models.trainee import Trainee
from app.schemas.assessment import (
    AssessmentQuestionsOut,
    LeaderboardResponse,
    LeaderboardUserOut,
    QuestionOut,
    SubmitRequest,
    SubmitResult,
)
from app.models.quiz import Assessment, AssessmentResult, AssessmentSuite, Question
from app.repositories import assessment_repository, attendance_repository
from app.services import assessment_service

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/{suite_uid}/questions", response_model=AssessmentQuestionsOut)
def get_questions(
    suite_uid: str,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return assessment_service.get_questions(db, suite_uid)


@router.post("/{suite_uid}/submit", response_model=SubmitResult)
def submit_assessment(
    suite_uid: str,
    payload: SubmitRequest,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    attendance = attendance_repository.get_for_conference_and_trainee(
        db, payload.conferenceUid, trainee.traineeUid
    )
    if not attendance or attendance.status != "Present":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be marked present by the trainer to submit this assessment.",
        )

    questions = db.query(Question).filter(Question.assessmentSuiteUid == suite_uid).all()
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions found for this assessment",
        )

    points_by_id = {q.id: (q.points or 0) for q in questions}
    correct_by_id = {q.id: q.correct_answer for q in questions}
    max_score = sum(points_by_id.values())

    total_score = 0
    correct_count = 0
    now = datetime.now()

    for answer in payload.answers:
        is_correct = (
            answer.selectedOption is not None
            and answer.selectedOption == correct_by_id.get(answer.questionId)
        )
        if is_correct:
            total_score += points_by_id.get(answer.questionId, 0)
            correct_count += 1

        db.add(
            Assessment(
                assessmentSuiteUid=suite_uid,
                conferenceUid=payload.conferenceUid,
                traineeUid=trainee.traineeUid,
                questionId=str(answer.questionId),
                selectedOption=answer.selectedOption,
            )
        )

    percentage = round((total_score / max_score) * 100, 2) if max_score else 0.0

    try:
        db.add(
            AssessmentResult(
                conferenceUid=payload.conferenceUid,
                traineeUid=trainee.traineeUid,
                assessmentSuiteUid=suite_uid,
                attemptNumber=assessment_repository.next_attempt_number(
                    db, trainee.traineeUid, suite_uid
                ),
                totalScore=total_score,
                maxScore=max_score,
                percentage=percentage,
                startedAt=now,
                submittedAt=now,
                status="Submitted",
            )
        )
        db.commit()
    except Exception as exc:  # TEMP diagnostic - surface the real reason
        db.rollback()
        logging.getLogger("assessment").exception("submit_assessment failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Save failed: {type(exc).__name__}: {str(exc)[:200]}",
        )

    return SubmitResult(
        totalScore=total_score,
        maxScore=max_score,
        percentage=percentage,
        correctCount=correct_count,
        totalQuestions=len(payload.answers),
    )


@router.get("/{suite_uid}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    suite_uid: str,
    conference_uid: Optional[str] = Query(None),
    zone: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    suite = (
        db.query(AssessmentSuite)
        .filter(AssessmentSuite.assessmentSuiteUid == suite_uid)
        .first()
    )
    title = (suite.examTitle or suite.courseName or "Quiz Assessment") if suite else "Quiz Assessment"
    total_questions = suite.noOfQuestion if suite and suite.noOfQuestion else 0
    if not total_questions:
        total_questions = (
            db.query(Question)
            .filter(Question.assessmentSuiteUid == suite_uid)
            .count()
        )

    # Query all results for this suite joined with Trainee
    query = (
        db.query(AssessmentResult, Trainee)
        .join(Trainee, AssessmentResult.traineeUid == Trainee.traineeUid)
        .filter(AssessmentResult.assessmentSuiteUid == suite_uid)
    )

    if conference_uid:
        query = query.filter(AssessmentResult.conferenceUid == conference_uid)
    if zone and zone.lower() != "all":
        query = query.filter(func.lower(Trainee.zone) == zone.lower())
    if state and state.lower() != "all":
        query = query.filter(func.lower(Trainee.state) == state.lower())
    if district and district.lower() != "all":
        query = query.filter(func.lower(Trainee.district) == district.lower())

    results = (
        query.order_by(
            AssessmentResult.totalScore.desc(),
            AssessmentResult.percentage.desc(),
            AssessmentResult.durationSeconds.asc(),
            AssessmentResult.submittedAt.asc(),
        )
        .all()
    )

    leaderboard_users: List[LeaderboardUserOut] = []
    user_rank = None
    user_score = None
    user_accuracy = None
    user_time_taken = None
    user_correct = None
    user_incorrect = None

    seen_trainees = set()
    current_rank = 1

    for res, t in results:
        if t.traineeUid in seen_trainees:
            continue
        seen_trainees.add(t.traineeUid)

        score_val = float(res.totalScore or 0)
        max_val = float(res.maxScore or total_questions or 1)
        pct_val = float(res.percentage or (round((score_val / max_val) * 100, 1) if max_val else 0))

        dur_secs = res.durationSeconds or 0
        if dur_secs >= 60:
            m = dur_secs // 60
            s = dur_secs % 60
            time_str = f"{m}m {s}s" if s else f"{m}m"
        else:
            time_str = f"{dur_secs}s" if dur_secs > 0 else "--"

        is_you = (t.traineeUid == trainee.traineeUid)
        if is_you:
            user_rank = current_rank
            user_score = score_val
            user_accuracy = pct_val
            user_time_taken = time_str
            user_correct = int(score_val)
            user_incorrect = max(0, total_questions - int(score_val))

        leaderboard_users.append(
            LeaderboardUserOut(
                rank=current_rank,
                traineeUid=t.traineeUid,
                name=t.name or "Trainee",
                score=f"{int(score_val)}/{int(max_val)}",
                accuracy=f"{int(pct_val)}%",
                percentage=pct_val,
                timeTaken=time_str,
                isYou=is_you,
            )
        )
        current_rank += 1

    # Fallback to current trainee's own latest submission if not found in filtered list
    if user_rank is None:
        last_attempt = (
            db.query(AssessmentResult)
            .filter(
                AssessmentResult.assessmentSuiteUid == suite_uid,
                AssessmentResult.traineeUid == trainee.traineeUid,
            )
            .order_by(AssessmentResult.id.desc())
            .first()
        )
        if last_attempt:
            score_val = float(last_attempt.totalScore or 0)
            max_val = float(last_attempt.maxScore or total_questions or 1)
            pct_val = float(last_attempt.percentage or (round((score_val / max_val) * 100, 1) if max_val else 0))
            user_score = score_val
            user_accuracy = pct_val
            user_correct = int(score_val)
            user_incorrect = max(0, total_questions - int(score_val))

    return LeaderboardResponse(
        title=title,
        totalQuestions=total_questions,
        userRank=user_rank,
        userScore=user_score,
        userAccuracy=user_accuracy,
        timeTakenFormatted=user_time_taken,
        correctCount=user_correct,
        incorrectCount=user_incorrect,
        leaderboard=leaderboard_users,
    )

