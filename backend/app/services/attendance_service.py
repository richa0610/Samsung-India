from sqlalchemy.orm import Session

from app.core.exceptions import conflict, not_found
from app.models.conference import Conference
from app.repositories import conference_repository
from app.schemas.attendance import VerifyLocationOut, VerifyLocationRequest
from app.utils.helpers import distance_meters


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
