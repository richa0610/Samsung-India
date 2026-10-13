import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import bad_request
from app.core.media import media_subdir
from app.core.request_context import caller_device
from app.dependencies.auth import get_current_trainee
from app.dependencies.database import get_common_db, get_db, get_tenant_id_from_request
from app.models.trainee import Trainee
from app.schemas.attendance import (
    AttendanceOut,
    CheckInRequest,
    VerifyLocationOut,
    VerifyLocationRequest,
)
from app.routers.ws import manager as ws_manager
from app.services import attendance_service, tenant_settings_service
from app.utils.helpers import geofence_enabled
from app.utils.validators import read_photo_upload

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _nudge_dashboard(background_tasks: BackgroundTasks, tenant_id: str, conference_uid: str) -> None:
    """Tell the trainer's Session Dashboard (on the conference's /ws/live room)
    to refetch, so the Participant Master List shows the new Present status
    right away instead of on the next 5s poll."""
    background_tasks.add_task(ws_manager.send_to_room, tenant_id, conference_uid, {"type": "session"})


@router.post("/check-in", response_model=AttendanceOut)
def check_in(
    payload: CheckInRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    # Exists, running, Attendance module open - and locked, so this trainee's row is created once.
    conference = attendance_service.open_check_in(db, payload.conferenceUid)
    # A geofenced session must be checked into through the secure endpoint,
    # which carries the trainee's coordinates - the plain check-in has none to
    # validate, so refuse it here rather than silently letting it bypass.
    if geofence_enabled(conference):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session needs a location check-in. Please use secure check-in.",
        )
    attendance = attendance_service.joined_attendance(db, conference, payload.conferenceUid, trainee)

    if attendance.status != "Present":
        attendance_service.mark_self_present(attendance, conference)
        attendance_service.record_check_in_log(db, conference, payload.conferenceUid, trainee.traineeUid)
        db.commit()
        db.refresh(attendance)
        _nudge_dashboard(background_tasks, get_tenant_id_from_request(request), payload.conferenceUid)
    elif settings.ALLOW_ATTENDANCE_RETEST:
        device = caller_device()
        attendance = attendance_service.retake_check_in(
            db, attendance, conference, payload.conferenceUid, trainee, device["ipAddress"], device["deviceInfo"]
        )
    return AttendanceOut(status=attendance.status, markedOn=attendance.markedOn)


@router.post("/verify-location", response_model=VerifyLocationOut)
def verify_location(
    payload: VerifyLocationRequest,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    tenant_id: str = Depends(get_tenant_id_from_request),
    _trainee: Trainee = Depends(get_current_trainee),
):
    return attendance_service.verify_location(
        db, payload, face_detection_required=tenant_settings_service.checkin_face_detection_enabled(common_db, tenant_id)
    )


@router.post("/check-in/secure", response_model=AttendanceOut)
async def check_in_secure(
    background_tasks: BackgroundTasks,
    request: Request,
    # Snake case here; the form field stays `conferenceUid`, which is what the app sends.
    conference_uid: str = Form(..., alias="conferenceUid"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    """Geofenced check-in: captures the trainee's location and a face photo
    alongside the usual attendance row. Stores records in both `attendance`
    and `attendance_logs` tables."""
    contents, extension = await read_photo_upload(photo, size_error_detail="Photo must be 5MB or smaller")

    # Exists, running, Attendance module open - and locked, so this trainee's row is created once.
    conference = attendance_service.open_check_in(db, conference_uid)

    # Any trainee who has joined this conference (Attendance row exists from
    # session_service.join_session) can self-admit via Secure Check-In -
    # only a trainer's already-final Absent decision blocks it.
    attendance = attendance_service.joined_attendance(db, conference, conference_uid, trainee)
    if attendance.checkInPhoto and not settings.ALLOW_ATTENDANCE_RETEST:
        return AttendanceOut(status=attendance.status, markedOn=attendance.markedOn)

    # Outside a geofenced venue: the try is counted (attemptCount), nothing else is saved - no
    # photo, no Present, no log.
    refusal = attendance_service.outside_venue_refusal(conference, latitude, longitude)
    if refusal:
        attendance_service.count_refused_check_in(attendance)
        db.commit()
        raise bad_request(refusal)

    distance = attendance_service.distance_from_venue(conference, latitude, longitude)
    tenant_id = get_tenant_id_from_request(request)
    photo_dir = media_subdir("attendance_photos", tenant_id)
    filename = f"{uuid.uuid4().hex}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    # Trainee self-admitting - promote Joined/Pending -> Present (no-op if
    # the trainer already marked them).
    attendance_service.mark_self_present(attendance, conference)
    attendance.checkInDistance = f"{distance:.0f}" if distance is not None else None
    attendance.checkInPhoto = f"attendance_photos/{filename}"
    attendance_service.record_check_in_log(
        db, conference, conference_uid, trainee.traineeUid,
        **caller_device(), locationData=f"{latitude},{longitude}",
    )

    db.commit()
    db.refresh(attendance)
    _nudge_dashboard(background_tasks, tenant_id, conference_uid)
    return AttendanceOut(status=attendance.status, markedOn=attendance.markedOn, distanceMeters=distance)


