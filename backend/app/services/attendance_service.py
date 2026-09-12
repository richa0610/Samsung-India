import uuid
from datetime import datetime

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import not_found
from app.core.media import media_subdir
from app.models.attendance import Attendance
from app.models.trainee import Trainee
from app.repositories import attendance_repository, conference_repository
from app.routers.ws import manager as ws_manager
from app.schemas.attendance import AttendanceOut, CheckInRequest, VerifyLocationOut, VerifyLocationRequest
from app.utils.helpers import distance_meters
from app.utils.validators import validate_image_upload


def _clear_existing_if_retest_allowed(db: Session, conference_uid: str, trainee_uid: str) -> Attendance | None:
    existing = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee_uid)
    if existing and settings.ALLOW_ATTENDANCE_RETEST:
        attendance_repository.delete(db, existing)
        return None
    return existing


def _promote_if_pending(db: Session, existing: Attendance) -> AttendanceOut:
    """A trainee who joined via QR/link already has a "Pending" attendance
    row (see session_service.join_session) - check-in flips it to Present
    rather than being a no-op."""
    if existing.status != "Present":
        existing.status = "Present"
        existing.markedOn = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        attendance_repository.save(db)
    return AttendanceOut(status=existing.status, markedOn=existing.markedOn)


def check_in(db: Session, trainee: Trainee, payload: CheckInRequest, background_tasks: BackgroundTasks) -> AttendanceOut:
    existing = _clear_existing_if_retest_allowed(db, payload.conferenceUid, trainee.traineeUid)
    if existing:
        return _promote_if_pending(db, existing)

    conference = conference_repository.get_by_uid(db, payload.conferenceUid)

    attendance = attendance_repository.create(
        db,
        Attendance(
            conferenceUid=payload.conferenceUid,
            trainerUid=conference.trainerEmployeeId if conference else None,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            markedOn=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="Present",
        ),
    )

    background_tasks.add_task(
        ws_manager.send_to,
        conference.trainerEmployeeId if conference else None,
        {"type": "attendance_marked", "conferenceUid": payload.conferenceUid, "traineeUid": trainee.traineeUid},
    )

    return AttendanceOut(status=attendance.status, markedOn=attendance.markedOn)


def verify_location(db: Session, payload: VerifyLocationRequest) -> VerifyLocationOut:
    """First step of the geofenced check-in flow (see check_in_secure) - lets
    the "Location Verified" screen show the trainee's distance from the venue
    and whether they're inside the radius. This is only a pre-check for the UI;
    the hard block happens server-side in check_in_secure."""
    conference = conference_repository.get_by_uid(db, payload.conferenceUid)
    if not conference:
        raise not_found("Session not found")

    venue_lat = float(conference.geoLatitude) if conference.geoLatitude is not None else None
    venue_lng = float(conference.geoLongitude) if conference.geoLongitude is not None else None
    distance = distance_meters(payload.latitude, payload.longitude, venue_lat, venue_lng)
    radius = conference.geoRadius or 100

    return VerifyLocationOut(
        distanceMeters=distance,
        withinRadius=(distance <= radius) if distance is not None else None,
        radiusMeters=radius,
        venueLabel=", ".join(filter(None, [conference.district, conference.state])) or None,
    )


async def check_in_secure(
    db: Session,
    trainee: Trainee,
    background_tasks: BackgroundTasks,
    conference_uid: str,
    latitude: float,
    longitude: float,
    photo: UploadFile,
) -> AttendanceOut:
    """Geofenced check-in: captures the trainee's location and a face photo
    alongside the usual attendance row. Used instead of `check_in` when the
    session's attendance module has `geoFencing` enabled."""
    contents = await photo.read()
    extension = validate_image_upload(photo.content_type, contents, size_error_detail="Photo must be 5MB or smaller")

    existing = _clear_existing_if_retest_allowed(db, conference_uid, trainee.traineeUid)
    if existing:
        return _promote_if_pending(db, existing)

    conference = conference_repository.get_by_uid(db, conference_uid)

    venue_lat = float(conference.geoLatitude) if conference and conference.geoLatitude is not None else None
    venue_lng = float(conference.geoLongitude) if conference and conference.geoLongitude is not None else None
    distance = distance_meters(latitude, longitude, venue_lat, venue_lng)

    photo_dir = media_subdir("attendance_photos")
    filename = f"{uuid.uuid4().hex}.{extension}"
    (photo_dir / filename).write_bytes(contents)

    attendance = attendance_repository.create(
        db,
        Attendance(
            conferenceUid=conference_uid,
            trainerUid=conference.trainerEmployeeId if conference else None,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            markedOn=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="Present",
            checkInDistance=f"{distance:.0f}" if distance is not None else None,
            checkInPhoto=f"attendance_photos/{filename}",
        ),
    )

    background_tasks.add_task(
        ws_manager.send_to,
        conference.trainerEmployeeId if conference else None,
        {"type": "attendance_marked", "conferenceUid": conference_uid, "traineeUid": trainee.traineeUid},
    )

    return AttendanceOut(status=attendance.status, markedOn=attendance.markedOn, distanceMeters=distance)
