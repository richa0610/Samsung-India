"""
Script to reset all trainee progress, attendance, and assessment results for the active session.
Run whenever you want to test the entire trainee flow from scratch.
"""

from app.database.database import SessionLocal
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.conference import Conference
from app.models.quiz import Assessment, AssessmentResult
from app.models.trainee import Trainee


def reset_all_sessions():
    db = SessionLocal()
    try:
        trainee = db.query(Trainee).first()
        conference = db.query(Conference).first()

        conf_uid = conference.conferenceUid if conference else None
        trainee_uid = trainee.traineeUid if trainee else None

        print("--> Resetting session data for:")
        print(f"    Trainee: {trainee.name if trainee else 'All'} ({trainee_uid})")
        print(f"    Conference: {conference.suiteTitle if conference else 'All'} ({conf_uid})")

        # 1. Clear Attendance & Logs
        att_count = db.query(Attendance).delete()
        log_count = db.query(AttendanceLog).delete()

        # 2. Clear Quiz / Standard Test Submissions for trainee
        ans_count = db.query(Assessment).delete()
        if trainee_uid:
            res_count = (
                db.query(AssessmentResult)
                .filter(AssessmentResult.traineeUid == trainee_uid)
                .delete()
            )
        else:
            res_count = db.query(AssessmentResult).delete()

        # 3. Reset Conference active module back to ATTENDANCE
        if conference:
            conference.activeModuleId = "ATTENDANCE"
            conference.conferenceStatus = "Ongoing"

        db.commit()

        print("\n[SUCCESS] Session reset successfully!")
        print(f"   - Deleted {att_count} Attendance record(s)")
        print(f"   - Deleted {log_count} AttendanceLog record(s)")
        print(f"   - Deleted {ans_count} Question Answer(s)")
        print(f"   - Deleted {res_count} Assessment Result(s)")
        print("   - Reset activeModuleId -> ATTENDANCE")
        print("\n[NEXT STEP] Reload your Expo app (press 'r' in Expo terminal) to start fresh from Step 1!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error resetting session: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    reset_all_sessions()
