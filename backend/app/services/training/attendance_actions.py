"""What a trainer or admin changes on one participant from the Participant Master List: a manual
Present / Absent, lifting a proctoring lockout, or clearing the attendance record - each with a
reason in the audit trail, and each answered with the refreshed Session Dashboard."""

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import MAX_PROCTORING_UNLOCKS
from app.core.exceptions import conflict, not_found
from app.models.admin import Admin
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.repositories import attendance_repository
from app.schemas.training import (
    AttendanceMarkRequest,
    AttendanceResetRequest,
    ProctoringUnlockRequest,
    SessionDashboardOut,
)
from app.services import proctoring_strikes
from app.services.activity_log_service import log_activity
from app.services.training.common import nudge_session_room, owned_conference
from app.services.training.session_dashboard import build_dashboard, latest_post_test_results
from app.utils.date_utils import utc_now
from app.utils.helpers import geofence_enabled
from app.utils.conference_format import is_running


def _append_remark_line(existing: str | None, line: str) -> str:
    """This schema has no activity-log table - entity `remarks` longtext
    fields are used as running text logs (see `attendance.theftRemarks`
    COMMENT 'Log of tab switches'). Prepend a timestamped line so the newest
    entry is first."""
    entry = f"[{utc_now().strftime('%Y-%m-%d %H:%M:%S')}] {line}"
    return f"{entry}\n{existing}" if existing else entry


def _apply_geofence_bypass(record: Attendance, conference: Conference, reason: str) -> None:
    """`geofenceBypass` ("1=Bypassed by Trainer") with `bypassRemark` = the trainer's reason: the
    trainer marked this trainee Present on a session that checks the venue location, without the
    trainee's own located check-in (secure check-in leaves `checkInPhoto`). Any other mark - Absent,
    no location rule, or a trainee who already checked in themselves - is no bypass."""
    bypassed = record.status == "Present" and geofence_enabled(conference) and not record.checkInPhoto
    record.geofenceBypass = 1 if bypassed else 0
    record.bypassRemark = reason if bypassed else None


def mark_attendance(
    db: Session,
    admin: Admin,
    conference_uid: str,
    trainee_uid: str,
    payload: AttendanceMarkRequest,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
) -> SessionDashboardOut:
    """Manual Present/Absent from the Trainee Master List - only allowed
    while the session is running. Records who/when/why: sets `status` +
    `updatedBy`, appends a timestamped line to `attendance.remarks`, and
    upserts the `attendance_logs` snapshot for the ATTENDANCE module."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    if not is_running(conference):
        raise conflict("Attendance can only be changed while the session is running")

    now_str = utc_now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{admin.username} -> {payload.status.upper()}: {payload.reason.strip()}"

    record = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee_uid)
    # The path's trainee UID must be someone the session's Trainee Master List can show: a roster /
    # attendance row on this conference, or a Post Test attempt on it (the dashboard's "Attempted"
    # row, the only case with no attendance row yet). Any other UID is refused, so a caller can't
    # attach an arbitrary trainee to their session - and, through the roster, to their Trainee List.
    if record is None and trainee_uid not in latest_post_test_results(db, conference):
        raise not_found("Trainee not found in this training")
    reason = payload.reason.strip()
    if record:
        record.status = payload.status
        record.markedOn = now_str
        record.updatedBy = admin.username
        record.remarks = _append_remark_line(record.remarks, log_line)
        record.masterRemarks = reason
        _apply_geofence_bypass(record, conference, reason)
        attendance_repository.save(db)
    else:
        record = Attendance(
            conferenceUid=conference_uid,
            trainerUid=conference.trainerEmployeeId,
            traineeUid=trainee_uid,
            markedOn=now_str,
            status=payload.status,
            updatedBy=admin.username,
            remarks=_append_remark_line(None, log_line),
            masterRemarks=reason,
        )
        _apply_geofence_bypass(record, conference, reason)
        attendance_repository.create(db, record)

    attendance_repository.upsert_attendance_log(
        db, conference_uid, trainee_uid, "ATTENDANCE", payload.status
    )
    attendance_repository.save(db)

    log_activity(
        db,
        action="MARK_ATTENDANCE",
        username=admin.username,
        role=admin.role,
        remarks=f"Marked {trainee_uid} {payload.status} for {conference_uid}: {reason}",
        reason=reason,
    )

    nudge_session_room(background_tasks, conference_uid, tenant_id)
    return build_dashboard(db, conference)


def unlock_proctoring(
    db: Session,
    admin: Admin,
    conference_uid: str,
    trainee_uid: str,
    payload: ProctoringUnlockRequest,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
) -> SessionDashboardOut:
    """Clears a trainee's on-device proctoring lockout from the Participant
    Master List - at most MAX_PROCTORING_UNLOCKS times per trainee per training.
    proctoring_strikes.record_unlock unlocks, ADDS PROCTORING_UNLOCK_ADDED_ATTEMPTS
    to `theftAttemptsLeft`, counts and logs the unlock and keeps every strike
    count; the reason also goes into `remarks` / `masterRemarks`. The trainee's
    post-test screen sees the flip via `/sessions/current` and lets them back in
    (session_service.get_current_session)."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    # Locked until the commit: two unlocks at once (a double tap, a second trainer) run one after
    # the other, so the second sees the first's count and the limit can't be passed.
    record = attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee_uid, lock=True)
    if record is None or not record.isTheftLocked:
        raise conflict("This trainee isn't locked")
    if proctoring_strikes.unlocks_used(record) >= MAX_PROCTORING_UNLOCKS:
        raise conflict(
            f"This trainee has already been unlocked {MAX_PROCTORING_UNLOCKS} times in this training "
            "- no more unlocks are allowed"
        )

    reason = payload.reason.strip()
    proctoring_strikes.record_unlock(record, admin.username, reason)
    record.remarks = _append_remark_line(record.remarks, f"{admin.username} -> PROCTORING UNLOCK: {reason}")
    record.masterRemarks = reason
    record.updatedBy = admin.username
    attendance_repository.save(db)

    log_activity(
        db,
        action="UNLOCK_PROCTORING",
        username=admin.username,
        role=admin.role,
        remarks=f"Unlocked {trainee_uid} on {conference_uid}: {reason}",
        reason=reason,
    )

    nudge_session_room(background_tasks, conference_uid, tenant_id)
    return build_dashboard(db, conference)


def reset_attendance(
    db: Session,
    admin: Admin,
    conference_uid: str,
    trainee_uid: str,
    payload: AttendanceResetRequest,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
) -> SessionDashboardOut:
    """Clears a trainee's attendance record entirely - the "..." control on the Trainee Master
    List. Same rules as a manual mark (mark_attendance): only while the session is running, and
    with a reason, which goes into the audit trail."""
    conference = owned_conference(db, admin, conference_uid, common_db, tenant_id)
    if not is_running(conference):
        raise conflict("Attendance can only be changed while the session is running")
    if attendance_repository.delete_for_conference_and_trainee(db, conference_uid, trainee_uid):
        # Same audit trail as a manual mark or a proctoring unlock: who cleared whose record, where, why.
        log_activity(
            db,
            action="RESET_ATTENDANCE",
            username=admin.username,
            role=admin.role,
            remarks=f"Reset attendance of {trainee_uid} for {conference_uid}: {payload.reason}",
            reason=payload.reason,
        )
    nudge_session_room(background_tasks, conference_uid, tenant_id)
    return build_dashboard(db, conference)
