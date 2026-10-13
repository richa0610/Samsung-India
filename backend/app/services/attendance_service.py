import json

from sqlalchemy.orm import Session

from app.core.exceptions import conflict, forbidden, not_found
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import attendance_repository, conference_repository
from app.schemas.attendance import VerifyLocationOut, VerifyLocationRequest
from app.utils.date_utils import utc_now
from app.utils.helpers import distance_meters, geofence_enabled, within_geofence


def _now_stamp() -> str:
    return utc_now().strftime("%Y-%m-%d %H:%M:%S")


def open_check_in(db: Session, conference_uid: str) -> Conference:
    """The session a trainee may check in to right now, locked for the roster change: it exists,
    it is running, and the trainer has its Attendance module open - the rule the trainee session
    screen shows (the Attendance card is live only while activeModuleId is ATTENDANCE). Any other
    time a check-in is refused instead of marking the trainee Present, which is what unlocks the
    session's tests."""
    from app.services.session_service import session_is_running  # local: session_service imports module_flow

    conference = conference_repository.lock_for_roster_change(db, conference_uid)
    if conference is None:
        raise not_found("Session not found")
    if not session_is_running(conference) or conference.activeModuleId != "ATTENDANCE":
        raise conflict("Check-in isn't open for this session right now")
    return conference


def outside_venue_refusal(conference: Conference, latitude: float, longitude: float) -> str | None:
    """Why a geofenced session refuses a check-in from this position (outside the venue radius), or
    None when the check-in may go ahead (inside it, or no geofence)."""
    if not geofence_enabled(conference):
        return None
    is_within, distance = within_geofence(conference, latitude, longitude)
    if is_within:
        return None
    return (
        f"You appear to be about {distance:.0f} m from the venue. "
        f"Move within {conference.geoRadius or 100} m to check in."
    )


def count_refused_check_in(attendance: Attendance) -> None:
    """A secure check-in refused for being outside the venue still counts as a try: `attemptCount`
    is the try the trainee got in on - 1 on the first, each refused try adds 1 (refused twice, then
    in = 3). Nothing else on the row changes."""
    attendance.attemptCount = (attendance.attemptCount or 1) + 1


def distance_from_venue(conference: Conference, latitude: float, longitude: float) -> float | None:
    """Metres from the session's venue, or None when the venue has no coordinates."""
    venue_lat = float(conference.geoLatitude) if conference.geoLatitude is not None else None
    venue_lng = float(conference.geoLongitude) if conference.geoLongitude is not None else None
    return distance_meters(latitude, longitude, venue_lat, venue_lng)


def joined_attendance(db: Session, conference: Conference, conference_uid: str, trainee: Trainee) -> Attendance:
    """The trainee's attendance row on this session, created as "Joined" - tagged with how they
    reached it - when they have none yet. Any trainee who joined (Joined / Pending, assigned or not)
    may self-admit; only a trainer's already-final Absent refuses the check-in."""
    attendance = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee.traineeUid)
    if not attendance:
        audience = "ASSIGNED" if trainee.trainerEmployeeId == conference.trainerEmployeeId else "UNASSIGNED"
        attendance = Attendance(
            conferenceUid=conference_uid,
            trainerUid=conference.trainerEmployeeId,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            status="Joined",
            sessionMeta=json.dumps({"audience": audience}),
        )
        db.add(attendance)
        db.flush()
    if attendance.status == "Absent":
        raise forbidden("You've been marked absent for this session.")
    return attendance


def mark_self_present(attendance: Attendance, conference: Conference) -> None:
    """A trainee self-admitting: Joined / Pending -> Present, stamped now. Their own check-in
    passed the session's location rule, so any earlier trainer bypass no longer applies."""
    attendance.status = "Present"
    attendance.markedOn = _now_stamp()
    attendance.trainerUid = attendance.trainerUid or conference.trainerEmployeeId
    attendance.geofenceBypass = 0
    attendance.bypassRemark = None


def record_check_in_log(
    db: Session, conference: Conference, conference_uid: str, trainee_uid: str, **details: object
) -> None:
    """This check-in's attendance_logs row under the live module (ATTENDANCE - see open_check_in),
    replacing any earlier one. `details`: ipAddress / deviceInfo / locationData, when known."""
    attendance_repository.replace_attendance_log(
        db, conference_uid, trainee_uid, conference.activeModuleId or "ATTENDANCE",
        markedAt=utc_now(), status="Present", **details,
    )


def retake_check_in(
    db: Session,
    previous: Attendance,
    conference: Conference,
    conference_uid: str,
    trainee: Trainee,
    caller_ip: str | None,
    user_agent: str | None,
) -> Attendance:
    """ALLOW_ATTENDANCE_RETEST only: a trainee who is already Present checks in again - their row is
    replaced by a fresh Present one (attempt 1), and the module's log with it."""
    db.delete(previous)
    db.flush()  # the old row goes before its replacement is inserted
    attendance = Attendance(
        conferenceUid=conference_uid,
        trainerUid=conference.trainerEmployeeId,
        traineeUid=trainee.traineeUid,
        phone=trainee.phone,
        markedOn=_now_stamp(),
        status="Present",
        attemptCount=1,
    )
    db.add(attendance)
    record_check_in_log(db, conference, conference_uid, trainee.traineeUid, ipAddress=caller_ip, deviceInfo=user_agent)
    db.commit()
    db.refresh(attendance)
    return attendance


def verify_location(db: Session, payload: VerifyLocationRequest, *, face_detection_required: bool = True) -> VerifyLocationOut:
    """First step of the geofenced check-in flow (see check_in_secure) - lets
    the "Location Verified" screen show the trainee's distance from the venue
    and whether they're inside the radius. This is only a pre-check for the UI;
    the hard block happens server-side in check_in_secure. Also tells the app
    whether this tenant runs the face check before the check-in photo."""
    conference = conference_repository.get_by_uid(db, payload.conferenceUid)
    if not conference:
        raise not_found("Session not found")

    distance = distance_from_venue(conference, payload.latitude, payload.longitude)
    radius = conference.geoRadius or 100

    return VerifyLocationOut(
        distanceMeters=distance,
        withinRadius=(distance <= radius) if distance is not None else None,
        radiusMeters=radius,
        venueLabel=", ".join(filter(None, [conference.district, conference.state])) or None,
        faceDetectionRequired=face_detection_required,
    )
