from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import forbidden
from app.dependencies.auth import get_current_admin, require_admin_role
from app.dependencies.database import get_common_db, get_db, get_tenant_id_from_request
from app.dependencies.filters import ConferenceFilters, get_conference_filters
from app.models.admin import Admin
from app.schemas.trainee_admin import TraineeAdminIn, TraineeAdminOut
from app.schemas.training import (
    AssessmentSuiteCreate,
    AssessmentSuiteDetail,
    AssessmentSuiteOut,
    AttendanceListItemOut,
    AttendanceMarkRequest,
    LiveBroadcastRequest,
    PendingSessionItem,
    ProctoringUnlockRequest,
    QuestionCreate,
    SessionDashboardOut,
    SessionReportOut,
    TopPerformer,
    TrainerAgendaResponse,
    TrainingPageResponse,
    AttendancePageResponse,
    TrainingAdminUpdate,
    TrainingCreate,
    TrainingDetailOut,
    TrainingOut,
    TrainingStatusActionRequest,
)
from app.services import (
    assessment_builder_service,
    data_scope_service,
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
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.create_training(db, payload, background_tasks, admin, tenant_id)


@router.get("/trainings", response_model=TrainerAgendaResponse)
def list_trainer_trainings(
    all_sessions: bool = False,
    org: bool = False,
    approval: Optional[Literal["pending", "reviewed"]] = Query(None),
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if org and getattr(admin, "role", None) != "admin":
        raise forbidden("This view requires an admin account")
    scoped_filters = data_scope_service.apply_identity_scope(db, admin, filters)
    return training_service.list_trainer_trainings(
        db, admin, scoped_filters.start, scoped_filters.end, all_sessions, org, scoped_filters, approval
    )


# Declared before the "/trainings/{conference_uid}" routes below so "page" is
# never read as a training id.
@router.get("/trainings/page", response_model=TrainingPageResponse)
def list_trainings_page(
    approval: Optional[Literal["pending", "reviewed"]] = Query(None),
    q: Optional[str] = Query(None, max_length=100),
    sort: Literal[
        "timestamp", "conferenceDate", "conferenceTime", "conferenceUid", "trainerName", "zone",
        "sessionType", "trainingType", "trainingHub", "state", "district", "conferenceStatus",
    ] = "timestamp",
    dir: Literal["asc", "desc"] = "desc",
    cursor: Optional[str] = Query(None, max_length=500),
    limit: int = Query(50, ge=1, le=200),
    page: Optional[int] = Query(None, ge=1, le=100_000),
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    # Authorization comes from the admin's own admin_access grant (resolved inside
    # list_trainings_page), not from apply_identity_scope's legacy company/zone columns -
    # `filters` here is only ever a further narrowing, never the authorization boundary.
    return training_service.list_trainings_page(
        db, admin, filters, approval, q, sort, dir == "desc", cursor, limit, page,
        common_db=common_db, tenant_id=tenant_id,
    )


@router.get("/trainings/pending", response_model=list[PendingSessionItem])
def list_pending_trainings(
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
):
    scoped_filters = data_scope_service.apply_identity_scope(db, admin, filters)
    return training_service.list_pending_trainings(db, scoped_filters)


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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.reset_attendance(
        db, admin, conference_uid, trainee_uid, background_tasks, common_db, tenant_id
    )


@router.get("/attendance", response_model=list[AttendanceListItemOut])
def list_attendance(
    org: bool = False,
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    if org and getattr(admin, "role", None) != "admin":
        raise forbidden("This view requires an admin account")
    # org=True's authorization comes from the admin_access grant (resolved inside
    # list_attendance), not apply_identity_scope's legacy company/zone columns - same as the
    # Training List. org=False (a trainer's own attendance) is unaffected: it was already
    # scoped to that trainer's own conferences, nothing to do with company/zone.
    return training_service.list_attendance(db, admin, org, filters, common_db=common_db, tenant_id=tenant_id)


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
    cursor: Optional[str] = Query(None, max_length=500),
    limit: int = Query(10, ge=1, le=200),
    page: Optional[int] = Query(None, ge=1, le=100_000),
    filters: ConferenceFilters = Depends(get_conference_filters),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin_role),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return training_service.list_attendance_page(
        db, admin, filters, mode, q, sort, dir == "desc", cursor, limit, page,
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


@router.get("/trainees", response_model=list[TraineeAdminOut])
def list_trainees_admin(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
):
    return trainee_admin_service.list_trainees_admin(db, admin, common_db, tenant_id)

