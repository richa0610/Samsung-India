from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_trainee
from app.dependencies.database import get_db
import math
import uuid
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
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
from app.core.media import ALLOWED_IMAGE_CONTENT_TYPES, MAX_UPLOAD_BYTES, media_subdir
from app.dependencies.auth import get_current_trainee
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.schemas.attendance import (
    AttendanceOut,
    CheckInRequest,
    VerifyLocationOut,
    VerifyLocationRequest,
)
from app.routers.ws import manager as ws_manager
from app.services import attendance_service
from app.utils.helpers import (
    distance_meters,
    geofence_enabled,
    within_geofence,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _nudge_dashboard(background_tasks: BackgroundTasks, conference_uid: str) -> None:
    """Tell the trainer's Session Dashboard (on the conference's /ws/live room)
    to refetch, so the Participant Master List shows the new Present status
    right away instead of on the next 5s poll."""
    background_tasks.add_task(ws_manager.send_to_room, conference_uid, {"type": "session"})


@router.post("/check-in", response_model=AttendanceOut)
def check_in(
    payload: CheckInRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    conference = (
        db.query(Conference)
        .filter(Conference.conferenceUid == payload.conferenceUid)
        .first()
    )
    # A geofenced session must be checked into through the secure endpoint,
    # which carries the trainee's coordinates - the plain check-in has none to
    # validate, so refuse it here rather than silently letting it bypass.
    if geofence_enabled(conference):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This session needs a location check-in. Please use secure check-in.",
        )
    module_id = (
        conference.activeModuleId
        if (conference and conference.activeModuleId)
        else "ATTENDANCE"
    )

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.conferenceUid == payload.conferenceUid,
            Attendance.traineeUid == trainee.traineeUid,
        )
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You're not on this session's roster yet.",
        )
    if existing.status == "Absent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You've been marked absent for this session.",
        )
    # Any trainee who has joined (Joined/Pending, assigned or not) can
    # self-admit here - only a trainer's already-final Present/Absent
    # decision blocks a self check-in, same rule as the trainee app's
    # plain (non-secure) check-in on the other branch.

    if existing.status != "Present":
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing.status = "Present"
        existing.markedOn = now_str
        existing.trainerUid = existing.trainerUid or (conference.trainerEmployeeId if conference else None)
        db.query(AttendanceLog).filter(
            AttendanceLog.conferenceUid == payload.conferenceUid,
            AttendanceLog.traineeUid == trainee.traineeUid,
            AttendanceLog.moduleId == module_id,
        ).delete()
        db.add(
            AttendanceLog(
                conferenceUid=payload.conferenceUid,
                traineeUid=trainee.traineeUid,
                moduleId=module_id,
                markedAt=datetime.now(),
                status="Present",
            )
        )
        db.commit()
        db.refresh(existing)
        _nudge_dashboard(background_tasks, payload.conferenceUid)
        return AttendanceOut(status=existing.status, markedOn=existing.markedOn)

    if not settings.ALLOW_ATTENDANCE_RETEST:
        return AttendanceOut(status=existing.status, markedOn=existing.markedOn)
    db.delete(existing)

    existing_logs = (
        db.query(AttendanceLog)
        .filter(
            AttendanceLog.conferenceUid == payload.conferenceUid,
            AttendanceLog.traineeUid == trainee.traineeUid,
            AttendanceLog.moduleId == module_id,
        )
        .all()
    )
    for log in existing_logs:
        db.delete(log)

    db.flush()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attendance = Attendance(
        conferenceUid=payload.conferenceUid,
        trainerUid=conference.trainerEmployeeId if conference else None,
        traineeUid=trainee.traineeUid,
        phone=trainee.phone,
        markedOn=now_str,
        status="Present",
        attemptCount=1,
    )
    db.add(attendance)

    client_ip = request.client.host if request.client else None
    user_agent = (
        request.headers.get("user-agent", "")[:255]
        if request.headers.get("user-agent")
        else None
    )

    attendance_log = AttendanceLog(
        conferenceUid=payload.conferenceUid,
        traineeUid=trainee.traineeUid,
        moduleId=module_id,
        markedAt=datetime.now(),
        status="Present",
        ipAddress=client_ip,
        deviceInfo=user_agent,
    )
    db.add(attendance_log)

    db.commit()
    db.refresh(attendance)
    return AttendanceOut(status=attendance.status, markedOn=attendance.markedOn)


@router.post("/verify-location", response_model=VerifyLocationOut)
def verify_location(
    payload: VerifyLocationRequest,
    db: Session = Depends(get_db),
    _trainee: Trainee = Depends(get_current_trainee),
):
    return attendance_service.verify_location(db, payload)


@router.post("/check-in/secure", response_model=AttendanceOut)
async def check_in_secure(
    background_tasks: BackgroundTasks,
    request: Request,
    conferenceUid: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    trainee: Trainee = Depends(get_current_trainee),
):
    """Geofenced check-in: captures the trainee's location and a face photo
    alongside the usual attendance row. Stores records in both `attendance`
    and `attendance_logs` tables."""
    extension = ALLOWED_IMAGE_CONTENT_TYPES.get(photo.content_type or "")
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG or WEBP images are allowed",
        )

    contents = await photo.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo must be 5MB or smaller",
        )

    conference = (
        db.query(Conference)
        .filter(Conference.conferenceUid == conferenceUid)
        .first()
    )

    # Geofence: a geofenced session rejects a check-in from outside the venue
    # radius. Checked before any DB write so a failed attempt changes nothing.
    if geofence_enabled(conference):
        is_within, distance_from_venue = within_geofence(conference, latitude, longitude)
        if not is_within:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"You appear to be about {distance_from_venue:.0f} m from the venue. "
                    f"Move within {conference.geoRadius or 100} m to check in."
                ),
            )

    module_id = (
        conference.activeModuleId
        if (conference and conference.activeModuleId)
        else "ATTENDANCE"
    )

    # Any trainee who has joined this conference (Attendance row exists from
    # session_service.join_session) can self-admit via Secure Check-In -
    # only a trainer's already-final Present/Absent decision blocks it.
    existing = (
        db.query(Attendance)
        .filter(
            Attendance.conferenceUid == conferenceUid,
            Attendance.traineeUid == trainee.traineeUid,
        )
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You're not on this session's roster yet.",
        )
    if existing.status == "Absent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You've been marked absent for this session.",
        )
    if existing.checkInPhoto and not settings.ALLOW_ATTENDANCE_RETEST:
        return AttendanceOut(status=existing.status, markedOn=existing.markedOn)

    venue_lat = float(conference.geoLatitude) if conference and conference.geoLatitude is not None else None
    venue_lng = float(conference.geoLongitude) if conference and conference.geoLongitude is not None else None
    distance = distance_meters(latitude, longitude, venue_lat, venue_lng)

    photo_dir = media_subdir("attendance_photos")
    filename = f"{uuid.uuid4().hex}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Trainee self-admitting - promote Joined/Pending -> Present (no-op if
    # the trainer already marked them).
    existing.status = "Present"
    existing.markedOn = now_str
    existing.trainerUid = existing.trainerUid or (conference.trainerEmployeeId if conference else None)
    existing.checkInDistance = f"{distance:.0f}" if distance is not None else None
    existing.checkInPhoto = f"attendance_photos/{filename}"

    client_ip = request.client.host if request.client else None
    user_agent = (
        request.headers.get("user-agent", "")[:255]
        if request.headers.get("user-agent")
        else None
    )

    db.query(AttendanceLog).filter(
        AttendanceLog.conferenceUid == conferenceUid,
        AttendanceLog.traineeUid == trainee.traineeUid,
        AttendanceLog.moduleId == module_id,
    ).delete()
    db.add(
        AttendanceLog(
            conferenceUid=conferenceUid,
            traineeUid=trainee.traineeUid,
            moduleId=module_id,
            markedAt=datetime.now(),
            status="Present",
            ipAddress=client_ip,
            deviceInfo=user_agent,
            locationData=f"{latitude},{longitude}",
        )
    )

    db.commit()
    db.refresh(existing)
    _nudge_dashboard(background_tasks, conferenceUid)
    return AttendanceOut(status=existing.status, markedOn=existing.markedOn, distanceMeters=distance)


