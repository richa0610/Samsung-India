"""One-off: reset the live-session state of specific conferences back to a
fresh "Scheduled" so they can be started again from the trainer dashboard.

Used after CONF2610134 / CONF2610135 were started + ended during testing -
`start_training` refuses to re-run an ended session (`conferenceEndsOn` set),
and test scripts had also left `conferenceStatus` inconsistent.

Clears: conference session/live-quiz/checkout state + module activity logs +
attendance_logs, and resets every attendance row to status "Pending" (drops
check-in photos, geo distance, proctoring locks, sessionMeta audience tag,
remarks). Approval status ("Approved") is left alone.

Run from backend/:  venv/Scripts/python.exe scripts/reset_conference_session.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401
from app.database.connection import SessionLocal
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog

CONFERENCE_UIDS = ["CONF2610134", "CONF2610135"]


def main() -> None:
    db = SessionLocal()
    try:
        for uid in CONFERENCE_UIDS:
            conf = db.query(Conference).filter(Conference.conferenceUid == uid).first()
            if conf is None:
                print(f"  {uid}: not found, skipped")
                continue

            conf.conferenceStatus = "Scheduled"
            conf.activeModuleId = None
            conf.actualStartedAt = None
            conf.actualEndedAt = None
            conf.conferenceEndsOn = None
            conf.liveQuizState = "IDLE"
            conf.liveQuestionId = None
            conf.liveTimerEndsAt = None
            conf.startConferenceImage = None
            conf.conferenceImage = None
            conf.attendanceSheet = None

            logs = db.query(ConferenceActivityLog).filter(
                ConferenceActivityLog.conferenceUid == uid
            ).delete()
            alogs = db.query(AttendanceLog).filter(AttendanceLog.conferenceUid == uid).delete()

            rows = db.query(Attendance).filter(Attendance.conferenceUid == uid).all()
            for a in rows:
                a.status = "Pending"
                a.markedOn = None
                a.checkInPhoto = None
                a.checkOutPhoto = None
                a.checkOutTime = None
                a.checkInDistance = None
                a.isTheftLocked = 0
                a.theftAttemptsLeft = 3
                a.theftRemarks = None
                a.sessionMeta = None
                a.remarks = None
                a.updatedBy = None

            print(
                f"  {uid}: Scheduled | {len(rows)} attendance rows -> Pending | "
                f"{logs} activity logs + {alogs} attendance_logs deleted"
            )

        db.commit()
        print("\nDone. Start Session should now work for these conferences.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
