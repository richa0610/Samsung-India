"""One-off: undo dev-test pollution on CONF2610048 caused by service functions
that commit internally (an outer rollback couldn't undo them).

Restores:
- conference.conferenceStatus -> 'Completed' (session was ended; actualEndedAt is set)
- attendance TRN2610002: clears the test `remarks` lines and `updatedBy`
- deletes the test attendance_logs row

Run from backend/:  venv/Scripts/python.exe scripts/cleanup_test_pollution_2.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.connection import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        a = db.execute(
            text(
                "UPDATE conference SET conferenceStatus = 'Completed' "
                "WHERE conferenceUid = 'CONF2610048' AND actualEndedAt IS NOT NULL "
                "AND conferenceStatus <> 'Completed'"
            )
        ).rowcount
        b = db.execute(
            text(
                "UPDATE attendance SET remarks = NULL, updatedBy = NULL "
                "WHERE conferenceUid = 'CONF2610048' AND traineeUid = 'TRN2610002' "
                "AND remarks LIKE '%PRESENT: came back%'"
            )
        ).rowcount
        c = db.execute(
            text(
                "DELETE FROM attendance_logs "
                "WHERE conferenceUid = 'CONF2610048' AND traineeUid = 'TRN2610002' "
                "AND moduleId = 'ATTENDANCE'"
            )
        ).rowcount
        db.commit()
        print(f"conference status reset: {a} | attendance remarks cleared: {b} | attendance_logs deleted: {c}")
        for r in db.execute(
            text(
                "SELECT conferenceStatus, conferenceEndsOn FROM conference "
                "WHERE conferenceUid = 'CONF2610048'"
            )
        ):
            print(" conference now:", dict(r._mapping))
        for r in db.execute(
            text(
                "SELECT status, updatedBy, remarks FROM attendance "
                "WHERE conferenceUid = 'CONF2610048' AND traineeUid = 'TRN2610002'"
            )
        ):
            print(" attendance now:", dict(r._mapping))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
