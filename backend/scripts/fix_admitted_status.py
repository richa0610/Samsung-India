"""One-off cleanup: normalise the single leftover attendance row whose status
is the retired value "Admitted" (from the reverted trainer-admits-then-trainee-
checks-in model) to "Present".

Context: the trainer's last action on this row was "ADMITTED" (not "ABSENT"),
and the conference is Completed - so "Present" is the correct final state. The
old value is preserved in `attendance.remarks` (append log) plus the line this
script adds.

Run once:  venv/Scripts/python.exe -m scripts.fix_admitted_status   (from backend/)
"""

from datetime import datetime

from app.database.session import SessionLocal
from app.models.attendance import Attendance

TARGET_STATUS = "Admitted"
NEW_STATUS = "Present"


def main() -> None:
    db = SessionLocal()
    try:
        rows = db.query(Attendance).filter(Attendance.status == TARGET_STATUS).all()
        print(f"Found {len(rows)} attendance row(s) with status {TARGET_STATUS!r}")
        if not rows:
            print("Nothing to do.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in rows:
            print(
                f"  id={row.id} conference={row.conferenceUid} trainee={row.traineeUid} "
                f"{TARGET_STATUS!r} -> {NEW_STATUS!r}"
            )
            row.status = NEW_STATUS
            row.markedOn = now
            line = f'[{now}] system -> PRESENT: normalised retired "Admitted" status'
            row.remarks = f"{line}\n{row.remarks}" if row.remarks else line

        db.commit()
        print(f"Committed. Updated {len(rows)} row(s).")

        remaining = db.query(Attendance).filter(Attendance.status == TARGET_STATUS).count()
        print(f"Rows still {TARGET_STATUS!r}: {remaining}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
