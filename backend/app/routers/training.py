from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import forbidden
from app.dependencies.auth import get_current_admin, require_admin_role
from app.dependencies.database import get_common_db, get_db, get_tenant_id_from_request
from app.dependencies.filters import ConferenceFilters, get_conference_filters
from app.dependencies.paging import PageRequest, page_request
from app.models.admin import Admin
from app.schemas.trainee_admin import TraineeAdminIn, TraineeAdminOut, TraineePageResponse
from app.schemas.training import (
    AssessmentSuiteCreate,
    AssessmentSuiteDetail,
    AssessmentSuiteOut,
    AttendanceListItemOut,
    AttendanceMarkRequest,
    AttendanceResetRequest,
    LiveBroadcastRequest,
    ProctoringUnlockRequest,
    QuestionCreate,
    SessionDashboardOut,
    SessionReportOut,
    TopPerformer,
    TrainerSummaryOut,
    TrainingPageResponse,
    AttendancePageResponse,
    TrainingAdminUpdate,
    TrainingCreate,
    TrainingDetailOut,
    TrainingFacetsOut,
    TrainingOut,
    TrainingStatusActionRequest,
)
from app.services import (
    assessment_builder_service,
    live_quiz_service,
    trainee_admin_service,
    training_service,
)

router = APIRouter(prefix="/admin", tags=["training"])


@router.get("/assessment-suites", response_model=list[AssessmentSuiteOut])
def list_assessment_suites(
    module: Optional[Literal["standardTest", "liveQuiz", "survey"]] = Query(None),
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return assessment_builder_service.list_assessment_suites(db, module)


@router.post("/assessment-suites", response_model=AssessmentSuiteDetail)
def create_assessment_suite(
    payload: AssessmentSuiteCreate,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(require_admin_role),
):
    return assessment_builder_service.create_assessment_suite(db, payload)


@router.get("/assessment-suites/{suite_uid}", response_model=AssessmentSuiteDetail)
def get_assessment_suite(
    suite_uid: str,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(require_admin_role),
):
    return assessment_builder_service.get_assessment_suite(db, suite_uid)


@router.post("/assessment-suites/{suite_uid}/questions", response_model=AssessmentSuiteDetail)
def add_question(
    suite_uid: str,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(require_admin_role),
):
    return assessment_builder_service.add_question(db, suite_uid, payload)


@router.delete("/assessment-suites/{suite_uid}/questions/{question_id}", response_model=AssessmentSuiteDetail)
def delete_question(
    suite_uid: str,
    question_id: int,
    db: Session = Depends(get_db),
    _admin: Admin = Depends(require_admin_role),
):
    return assessment_builder_service.delete_question(db, suite_uid, question_id)


@router.post("/trainings", response_model=TrainingOut)
def create_training(
    payload: TrainingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.create_training(db, payload, background_tasks, admin, tenant_id, common_db=common_db)


@router.get("/trainings/summary", response_model=TrainerSummaryOut)
def get_trainer_summary(
    start: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    """The trainer Home dashboard (counts for today, or for start..end, plus recent sessions)."""
    return training_service.trainer_summary(db, admin, start, end, common_db=common_db, tenant_id=tenant_id)


# Declared before the "/trainings/{conference_uid}" routes below so "page" is
# never read as a training id.
@router.get("/trainings/page", response_model=TrainingPageResponse)
def list_trainings_page(
    approval: Optional[Literal["pending", "reviewed", "approved"]] = Query(None),
    q: Optional[str] = Query(None, max_length=100),
    sort: Literal[
        "timestamp", "conferenceDate", "conferenceTime", "conferenceUid", "trainerName", "zone",
        "sessionType", "trainingType", "trainingHub", "state", "district", "conferenceStatus",
        "session",
    ] = "timestamp",
    dir: Literal["asc", "desc"] = "desc",
    # The trainer Sessions screen: its Today tab (the device's date), Completed tab and location
    # filter; sort="session" is its grouped order (page numbers only).
    on_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    status: Optional[Literal["completed"]] = Query(None),
    location: Optional[str] = Query(None, max_length=200),
    paging: PageRequest = Depends(page_request(50)),
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    # Authorization comes from the caller's verified scope (resolved inside list_trainings_page):
    # an admin's admin_access grant, or an active trainer's own assignments. `filters` here is
    # only ever a further narrowing, never the authorization boundary.
    return training_service.list_trainings_page(
        db, admin, filters, approval, q, sort, dir == "desc", paging.cursor, paging.limit, paging.page,
        common_db=common_db, tenant_id=tenant_id, on_date=on_date, status=status, location=location,
    )


@router.get("/trainings/facets", response_model=TrainingFacetsOut)
def get_training_facets(
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.training_facets(db, admin, filters, common_db=common_db, tenant_id=tenant_id)


@router.post("/trainings/{conference_uid}/approve", response_model=TrainingOut)
def approve_training(
    conference_uid: str,
    payload: Optional[TrainingStatusActionRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    reason = payload.reason if payload else None
    return training_service.approve_training(
        db, admin, conference_uid, reason=reason, background_tasks=background_tasks,
        common_db=common_db, tenant_id=tenant_id,
    )


@router.post("/trainings/{conference_uid}/reject", response_model=TrainingOut)
def reject_training(
    conference_uid: str,
    payload: Optional[TrainingStatusActionRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    reason = payload.reason if payload else None
    return training_service.reject_training(
        db, admin, conference_uid, reason=reason, background_tasks=background_tasks,
        common_db=common_db, tenant_id=tenant_id,
    )


@router.get("/trainings/{conference_uid}", response_model=SessionDashboardOut)
def get_session_dashboard(
    conference_uid: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.get_session_dashboard(db, admin, conference_uid, common_db, tenant_id)


@router.get("/trainings/{conference_uid}/detail", response_model=TrainingDetailOut)
def get_training_detail(
    conference_uid: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.get_training_detail(db, admin, conference_uid, common_db, tenant_id)


@router.patch("/trainings/{conference_uid}", response_model=TrainingOut)
def update_training(
    conference_uid: str,
    payload: TrainingAdminUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.update_training(
        db, admin, conference_uid, payload, background_tasks, common_db=common_db, tenant_id=tenant_id
    )


@router.get("/trainings/{conference_uid}/performers", response_model=list[TopPerformer])
def list_all_performers(
    conference_uid: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.list_all_performers(db, admin, conference_uid, common_db, tenant_id)


@router.get("/trainings/{conference_uid}/report", response_model=SessionReportOut)
def get_session_report(
    conference_uid: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.get_session_report(db, admin, conference_uid, common_db, tenant_id)


@router.get("/trainings/{conference_uid}/schedule-check")
def check_training_schedule(
    conference_uid: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.check_schedule(db, admin, conference_uid, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/start", response_model=TrainingOut)
async def start_training(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    photo: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    venueLatitude: Optional[float] = Form(None),
    venueLongitude: Optional[float] = Form(None),
    scheduleOverrideReason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return await training_service.start_training(
        db,
        admin,
        conference_uid,
        photo,
        background_tasks,
        latitude=latitude,
        longitude=longitude,
        venue_latitude=venueLatitude,
        venue_longitude=venueLongitude,
        schedule_override_reason=scheduleOverrideReason,
        common_db=common_db,
        tenant_id=tenant_id,
    )


@router.post("/trainings/{conference_uid}/advance-module", response_model=TrainingOut)
def advance_module(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.advance_module(db, admin, conference_uid, background_tasks, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/modules/{module_key}/start", response_model=TrainingOut)
def start_module(
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.start_module(
        db, admin, conference_uid, module_key, background_tasks, common_db, tenant_id
    )


@router.post("/trainings/{conference_uid}/modules/{module_key}/restart", response_model=TrainingOut)
def restart_module(
    conference_uid: str,
    module_key: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.restart_module(
        db, admin, conference_uid, module_key, background_tasks, common_db, tenant_id
    )


@router.post("/trainings/{conference_uid}/modules/stop-active", response_model=TrainingOut)
def stop_active_module(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.stop_active_module(db, admin, conference_uid, background_tasks, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/live-quiz/broadcast", response_model=SessionDashboardOut)
def live_quiz_broadcast(
    conference_uid: str,
    payload: LiveBroadcastRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return live_quiz_service.broadcast_question(
        db, admin, conference_uid, payload.questionId, background_tasks, common_db, tenant_id
    )


@router.post("/trainings/{conference_uid}/live-quiz/stop-timer", response_model=SessionDashboardOut)
def live_quiz_stop_timer(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return live_quiz_service.stop_timer(db, admin, conference_uid, background_tasks, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/live-quiz/leaderboard", response_model=SessionDashboardOut)
def live_quiz_leaderboard(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return live_quiz_service.show_leaderboard(db, admin, conference_uid, background_tasks, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/live-quiz/lobby", response_model=SessionDashboardOut)
def live_quiz_lobby(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return live_quiz_service.show_lobby(db, admin, conference_uid, background_tasks, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/live-quiz/finish", response_model=SessionDashboardOut)
def live_quiz_finish(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return live_quiz_service.finish(db, admin, conference_uid, background_tasks, common_db, tenant_id)


@router.post("/trainings/{conference_uid}/end", response_model=TrainingOut)
async def end_training(
    conference_uid: str,
    background_tasks: BackgroundTasks,
    photo: UploadFile = File(...),
    attendanceSheet: UploadFile = File(...),
    totalPax: int = Form(...),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return await training_service.end_training(
        db, admin, conference_uid, background_tasks, photo, attendanceSheet, totalPax, common_db, tenant_id
    )


@router.post("/trainings/{conference_uid}/attendance/{trainee_uid}", response_model=SessionDashboardOut)
def mark_attendance(
    conference_uid: str,
    trainee_uid: str,
    payload: AttendanceMarkRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.mark_attendance(
        db, admin, conference_uid, trainee_uid, payload, background_tasks, common_db, tenant_id
    )


@router.post(
    "/trainings/{conference_uid}/attendance/{trainee_uid}/unlock",
    response_model=SessionDashboardOut,
)
def unlock_proctoring(
    conference_uid: str,
    trainee_uid: str,
    payload: ProctoringUnlockRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.unlock_proctoring(
        db, admin, conference_uid, trainee_uid, payload, background_tasks, common_db, tenant_id
    )


@router.delete("/trainings/{conference_uid}/attendance/{trainee_uid}", response_model=SessionDashboardOut)
def reset_attendance(
    conference_uid: str,
    trainee_uid: str,
    payload: AttendanceResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.reset_attendance(
        db, admin, conference_uid, trainee_uid, payload, background_tasks, common_db, tenant_id
    )


@router.get("/attendance/page", response_model=AttendancePageResponse)
def list_attendance_page(
    mode: Literal["all", "pending", "confirmed"] = "all",
    q: Optional[str] = Query(None, max_length=100),
    sort: Literal[
        "markedAt", "conferenceDate", "region", "product", "session", "audienceType", "trainerName",
        "trainerHoId", "participantHoId", "participantName", "phone", "state", "district",
        "reportingManagerOfPromoter", "attendanceStatus", "checkIn", "checkOut", "attendanceId", "conferenceId",
    ] = "markedAt",
    dir: Literal["asc", "desc"] = "desc",
    paging: PageRequest = Depends(page_request(10)),
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.list_attendance_page(
        db, admin, filters, mode, q, sort, dir == "desc", paging.cursor, paging.limit, paging.page,
        common_db=common_db, tenant_id=tenant_id,
    )


@router.post("/trainees", response_model=TraineeAdminOut, status_code=status.HTTP_201_CREATED)
def register_trainee_admin(
    payload: TraineeAdminIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return trainee_admin_service.register_trainee_admin(
        db, payload, background_tasks, admin, common_db=common_db, tenant_id=tenant_id
    )


@router.get("/trainees/page", response_model=TraineePageResponse)
def list_trainees_page(
    mode: Literal["all", "pending"] = "all",
    q: Optional[str] = Query(None, max_length=100),
    sort: Literal["timestamp", "traineeUid", "name", "trainerName", "supervisorName", "district", "updatedBy", "status"] = "timestamp",
    dir: Literal["asc", "desc"] = "desc",
    paging: PageRequest = Depends(page_request(10)),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return trainee_admin_service.list_trainees_page(
        db, admin, mode, q, sort, dir == "desc", paging.cursor, paging.limit, paging.page, common_db=common_db, tenant_id=tenant_id
    )
