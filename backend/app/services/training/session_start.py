"""Starting a session: the gates a start must pass (approved, on or after its date, at the venue,
on schedule or with a reason) and the start itself, with the trainer's check-in photo."""

from fastapi import BackgroundTasks, HTTPException, UploadFile, status as http_status
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, conflict, forbidden
from app.core.media import media_subdir
from app.models.admin import Admin
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.repositories import activity_log_repository, conference_repository
from app.schemas.training import TrainingOut
from app.services.activity_log_service import log_activity
from app.services.module_flow import log_module_action, trainer_position, venue_override_remark
from app.services.training.common import nudge_session_room, owned_conference, training_out
from app.utils.date_utils import VENUE_TIME_FORMAT, ist_now, ist_to_iso, parse_module_start, utc_now
from app.utils.helpers import geofence_enabled, within_geofence
from app.utils.status import title_status
from app.utils.validators import read_photo_upload

SCHEDULE_GRACE_SECONDS = 60  # +/- tolerance before a start counts as "off schedule"


def _resolve_start_geofence(
    conference: Conference,
    latitude: float | None,
    longitude: float | None,
    venue_latitude: float | None,
    venue_longitude: float | None,
) -> None:
    """Geofence gate for starting a session.

    - If the trainer supplied `venue_latitude`/`venue_longitude` they've chosen
      to correct the location from the "you're not at the venue" prompt: this
      is scoped to THIS conference only - it updates `conference.geoLatitude/
      geoLongitude` and locks further correction for this conference, but
      never touches the shared `venue` row. A different training at the same
      venue (even the very next one) starts from the venue's own coordinates
      and can independently correct its own conference if it needs to -
      one trainer's fix doesn't silently shift the geofence under every other
      session at that venue.
    - Else, if the session is geofenced (venue has coordinates + geoFencing on)
      and the trainer's position is outside the radius, raise a 409 the app
      recognises to show that prompt - offering the one-time correction above
      only while this conference isn't already locked. A session that isn't
      geofenced starts with no location check.
    """
    if venue_latitude is not None and venue_longitude is not None:
        # Already corrected once for this conference - can't be corrected
        # again, even by resubmitting this form field directly.
        if conference.venueLocationOverridden:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "code": "OUTSIDE_VENUE_LOCKED",
                    "message": (
                        "This session's location was already confirmed once and can't be "
                        "corrected again. Start the session from the venue."
                    ),
                },
            )
        conference.geoLatitude = venue_latitude
        conference.geoLongitude = venue_longitude
        conference.venueLocationOverridden = 1
        return

    if not geofence_enabled(conference):
        return

    # Geofenced session: the trainer's location is mandatory - without it we
    # can't confirm they're at the venue, and skipping the check would be a
    # bypass. The app surfaces this as "turn on location".
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "LOCATION_REQUIRED",
                "message": "Turn on location to start this session - it confirms you're at the venue.",
            },
        )

    within, distance = within_geofence(conference, latitude, longitude)
    if within:
        return

    radius = conference.geoRadius or 100
    if conference.venueLocationOverridden:
        # No correction offered - this conference's location was already
        # confirmed once, so the app shows a hard block instead of the
        # "update the venue location?" prompt.
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail={
                "code": "OUTSIDE_VENUE_LOCKED",
                "message": (
                    f"You're about {distance:.0f} m from the venue (allowed: {radius} m). "
                    "This session's location has already been confirmed and can't be corrected "
                    "again - start the session from the venue."
                ),
                "distanceMeters": round(distance),
                "radius": radius,
            },
        )
    raise HTTPException(
        status_code=http_status.HTTP_409_CONFLICT,
        detail={
            "code": "OUTSIDE_VENUE",
            "message": (
                f"You're about {distance:.0f} m from the venue (allowed: {radius} m). "
                "Start the session from the venue, or update the venue location."
            ),
            "distanceMeters": round(distance),
            "radius": radius,
        },
    )


def _resolve_schedule_override(conference: Conference, reason: str | None) -> bool:
    """Off-schedule start gate: starting more than SCHEDULE_GRACE_SECONDS
    away from the scheduled moment - earlier, later on the same day, or on a
    later day entirely (there's a separate hard block further up against
    starting on an EARLIER day) - requires the trainer to give a reason
    before the session is allowed to proceed at all. `conferenceTime` is
    venue-local (IST), so the "now" it's compared against has to be IST too,
    not the host's naive clock.

    Applies the reason onto `conference.scheduleOverrideReason` (the source
    of truth) and returns whether this start actually was off-schedule -
    False for an on-schedule start, where there's nothing to do. Raises 409
    SCHEDULE_OVERRIDE if a reason was required but not given."""
    override_reason = (reason or "").strip()[:500]
    scheduled_start = parse_module_start(conference.conferenceDate, conference.conferenceTime)
    off_schedule = (
        conference.actualStartedAt is None
        and scheduled_start is not None
        and abs((ist_now() - scheduled_start).total_seconds()) > SCHEDULE_GRACE_SECONDS
    )
    if not off_schedule:
        return False

    if not override_reason:
        scheduled_label = conference.conferenceTime or scheduled_start.strftime(VENUE_TIME_FORMAT)
        early = ist_now() < scheduled_start
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail={
                "code": "SCHEDULE_OVERRIDE",
                "message": (
                    f"This session was scheduled to start at {scheduled_label}. "
                    f"Add a reason for starting it {'early' if early else 'late'} to proceed."
                ),
                "scheduledFor": ist_to_iso(scheduled_start),
                "early": early,
            },
        )

    conference.scheduleOverrideReason = override_reason
    return True


def check_schedule(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> dict:
    """Read-only pre-check for the Start Session flow: lets the app ask for
    a schedule-override reason right after the trainer taps "Start Session"
    - before the camera even opens - rather than only after they've already
    taken the check-in photo. Raises the exact same 409 SCHEDULE_OVERRIDE
    `_resolve_schedule_override` would raise if a reason is needed; returns
    a plain OK otherwise. Never persists anything (no reason to apply, no
    save) - the authoritative check+persist still happens inside
    start_training itself, so this can't be used to bypass it."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    _resolve_schedule_override(conference, None)
    return {"offSchedule": False}


async def start_training(
    db: Session,
    admin: Admin,
    conference_uid: str,
    photo: UploadFile,
    background_tasks: BackgroundTasks,
    latitude: float | None = None,
    longitude: float | None = None,
    venue_latitude: float | None = None,
    venue_longitude: float | None = None,
    schedule_override_reason: str | None = None,
    common_db: Session = None,
    tenant_id: str = None,
) -> TrainingOut:
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    if conference.conferenceEndsOn is not None:
        raise conflict("This session has already ended")
    if title_status(conference.conferenceStatus) == "Cancelled":
        raise conflict("This session was cancelled by an admin")
    if title_status(conference.status) != "Approved":
        raise forbidden("This session hasn't been approved by an admin yet")
    # A session can only be started on (or after) its scheduled date - not
    # ahead of time. `conferenceDate` is stored as "YYYY-MM-DD", so a plain
    # string compare against today's ISO date is correct.
    # Dates are India dates: compared with today in IST, not the server clock's (UTC) date.
    if conference.conferenceDate and conference.conferenceDate > ist_now().date().isoformat():
        raise bad_request("This session can only be started on its scheduled date")

    # Kept for the activity log: where this session's venue was before a trainer's override.
    original_venue = (conference.geoLatitude, conference.geoLongitude)
    _resolve_start_geofence(conference, latitude, longitude, venue_latitude, venue_longitude)
    venue_overridden = venue_latitude is not None and venue_longitude is not None

    # Schedule override: checked AFTER the geofence gate so a geofenced
    # session confirms the trainer is at the venue first, then asks for the
    # reason. Raises 409 SCHEDULE_OVERRIDE if one's needed but missing;
    # otherwise applies `conference.scheduleOverrideReason` and reports
    # whether this start needed one at all (for the activity-log mirror below).
    off_schedule = _resolve_schedule_override(conference, schedule_override_reason)

    # The trainer must capture a check-in photo to start the session - same
    # identity-verification idea as the trainee's secure attendance check-in.
    contents, extension = await read_photo_upload(photo, size_error_detail="Photo must be 5MB or smaller")
    photo_dir = media_subdir("trainer_checkin_photos", tenant_id)
    filename = f"{conference.conferenceUid}.{extension}"
    (photo_dir / filename).write_bytes(contents)
    conference.startConferenceImage = f"trainer_checkin_photos/{filename}"

    conference.conferenceStatus = "Ongoing"
    if conference.actualStartedAt is None:
        conference.actualStartedAt = utc_now()

    # Where the trainer started it from; a venue-location override is spelled out in the remark.
    position = trainer_position(conference, latitude, longitude)
    if venue_overridden:
        position["location_remark"] = venue_override_remark(original_venue, conference, latitude, longitude)
    log_module_action(db, conference.conferenceUid, None, "SESSION_STARTED", admin.username, **position)

    if off_schedule:
        # Mirrored onto the activity log (who/when, alongside the trainer's
        # location) so it also shows up in the Execution Flow audit log - the
        # conference row (set by _resolve_schedule_override) is the source
        # of truth.
        activity_log_repository.add(
            db,
            ConferenceActivityLog(
                conferenceUid=conference.conferenceUid,
                moduleId=None,
                action="SCHEDULE_OVERRIDE",
                performedBy=admin.username,
                trainerLat=latitude,
                trainerLng=longitude,
                locationRemark=conference.scheduleOverrideReason,
            ),
        )

    # Starting the session no longer auto-activates a module - the trainer
    # runs the flow forward one manual Start at a time (session_control.start_module), so
    # `activeModuleId` stays None until they tap Start on the first module.
    conference_repository.save(db, conference)
    nudge_session_room(background_tasks, conference_uid, tenant_id)

    log_activity(
        db,
        action="START_SESSION",
        username=admin.username,
        role=admin.role,
        remarks=f"Started session {conference.conferenceUid}",
        file_path=conference.startConferenceImage,
    )

    return training_out(conference)
