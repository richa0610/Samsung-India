import json
import math
from typing import Optional


def attendance_is_assigned(attendance) -> bool:
    """True when the trainee is on the trainer's roster for this session - a
    pre-seeded "Pending" row, or a row tagged ASSIGNED at QR-join time
    (session_service._set_attendance_audience -> sessionMeta.audience).

    Assigned trainees self-admit: completing Secure Check-In marks them
    Present without the trainer's manual "mark present" step. Walk-ins
    (UNASSIGNED / FRESH) stay trainer-gated."""
    if attendance is None:
        return False
    if attendance.status == "Pending":
        return True
    try:
        return (json.loads(attendance.sessionMeta or "{}") or {}).get("audience") == "ASSIGNED"
    except (ValueError, TypeError):
        return False


def geofence_enabled(conference) -> bool:
    """True when this session's attendance module is configured for geofenced
    check-in AND the conference has venue coordinates to fence against. When
    either is missing the geofence simply isn't enforced."""
    if conference is None or conference.geoLatitude is None or conference.geoLongitude is None:
        return False
    if not conference.sessionConfig:
        return False
    try:
        return bool(json.loads(conference.sessionConfig).get("attendance", {}).get("geoFencing"))
    except (ValueError, AttributeError):
        return False


def within_geofence(conference, latitude: float, longitude: float) -> tuple[bool, Optional[float]]:
    """(is_within, distance_m) for a trainee's check-in position against the
    conference's geofence. Assumes `geofence_enabled(conference)` is True."""
    distance = distance_meters(
        latitude, longitude, float(conference.geoLatitude), float(conference.geoLongitude)
    )
    if distance is None:
        return True, None
    return distance <= (conference.geoRadius or 100), distance


def distance_meters(
    lat1: Optional[float], lng1: Optional[float], lat2: Optional[float], lng2: Optional[float]
) -> Optional[float]:
    """Great-circle distance between two lat/lng points, in meters."""
    if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
        return None

    earth_radius_m = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_m * c
