from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_trainee
from app.dependencies.database import get_db, get_tenant_id_from_request
from app.models.trainee import Trainee
from app.schemas.session import (
    CurrentSession,
    LiveAnswerRequest,
    LiveAnswerResult,
    LiveQuizResultsOut,
    LiveQuizSubmitOut,
    LiveQuizSummaryOut,
    LiveQuizView,
    LiveRevealOut,
    LiveTimeoutRequest,
    ProctoringLockOut,
    ProctoringLockRequest,
    SessionHistoryItem,
    SessionJoinInfo,
    TraineeDashboardOut,
    TraineeMetricCard,
    TrainingHistoryPage,
    TrainingDetailOut,
)
from app.services import live_quiz_service, session_service, trainee_dashboard_service, training_detail_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/join/{code}", response_model=SessionJoinInfo)
def get_session_join_info(
    code: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_tenant_id_from_request)
):
    return session_service.get_join_info(db, code, tenant_id)


@router.post("/join/{code}", response_model=SessionJoinInfo)
def join_session(
    code: str,
    viaRegistration: bool = False,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return session_service.join_session(db, trainee, code, tenant_id, via_registration=viaRegistration)


@router.get("/current", response_model=CurrentSession)
def get_current_session(
    request: Request,
    conference_uid: str | None = None,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    tenant_id = get_tenant_id_from_request(request)
    return session_service.get_current_session(db, trainee, tenant_id, conference_uid=conference_uid)


@router.post("/proctoring-lock", response_model=ProctoringLockOut)
def report_proctoring_lock(
    payload: ProctoringLockRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    tenant_id = get_tenant_id_from_request(request)
    return session_service.report_proctoring_lock(db, trainee, payload, background_tasks, tenant_id)


@router.get("/live-quiz", response_model=LiveQuizView)
def get_live_quiz(
    conferenceUid: str,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.get_live_quiz_view(db, trainee, conferenceUid)


@router.post("/live-quiz/answer", response_model=LiveAnswerResult)
def submit_live_quiz_answer(
    payload: LiveAnswerRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.submit_live_answer(db, trainee, payload, background_tasks, get_tenant_id_from_request(request))


@router.post("/live-quiz/timeout", response_model=LiveAnswerResult)
def report_live_quiz_timeout(
    payload: LiveTimeoutRequest,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.report_live_timeout(db, trainee, payload.conferenceUid, payload.questionId)


@router.get("/live-quiz/summary", response_model=LiveQuizSummaryOut)
def get_live_quiz_summary(
    conferenceUid: str,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.get_live_quiz_summary(db, trainee, conferenceUid)


@router.get("/live-quiz/reveal", response_model=LiveRevealOut)
def reveal_live_quiz_question(
    conferenceUid: str,
    questionId: int,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.reveal_live_question(db, trainee, conferenceUid, questionId)


@router.post("/live-quiz/submit", response_model=LiveQuizSubmitOut)
def submit_live_quiz(
    conferenceUid: str,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.submit_live_quiz(db, trainee, conferenceUid)


@router.get("/live-quiz/results", response_model=LiveQuizResultsOut)
def get_live_quiz_results(
    conferenceUid: str,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return live_quiz_service.get_live_quiz_results(db, trainee, conferenceUid)


@router.get("/history", response_model=list[SessionHistoryItem])
def get_session_history(
    limit: int = Query(10, ge=1, le=500),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return session_service.get_session_history(db, trainee, limit)


@router.get("/trainings", response_model=TrainingHistoryPage)
def get_training_history(
    page: int = Query(1, ge=1, le=10000),
    limit: int = Query(20, ge=1, le=100),
    start: Optional[str] = Query(None, max_length=32),
    end: Optional[str] = Query(None, max_length=32),
    status: Optional[str] = Query(None, max_length=20),
    # A Dashboard metric card tapped: only the trainings that card counted.
    card: Optional[TraineeMetricCard] = Query(None),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    """The trainee's own Training History, a page at a time (the screen loads more as it scrolls)."""
    return trainee_dashboard_service.list_training_history(
        db, trainee, page, limit, start or None, end or None, status or None, card
    )


@router.get("/dashboard", response_model=TraineeDashboardOut)
def get_trainee_dashboard(
    # The app asks for 5 (Home) or 500 (Training History); bounded so one request can't ask for more.
    limit: int = Query(10, ge=1, le=500),
    start: Optional[str] = Query(None, max_length=32),
    end: Optional[str] = Query(None, max_length=32),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return trainee_dashboard_service.build_trainee_dashboard(db, trainee, limit, start, end)


@router.get("/{conference_uid}/detail", response_model=TrainingDetailOut)
def get_training_detail(
    conference_uid: str,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    return training_detail_service.get_training_detail(db, trainee, conference_uid)
