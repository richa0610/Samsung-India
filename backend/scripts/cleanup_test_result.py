"""One-off: remove a bogus 0/5 assessment_results row for CONF2610048 /
TRN2610002 that a dev test accidentally committed (submit_assessment commits
internally, so an outer rollback didn't undo it).

Run from backend/ with:
    venv/Scripts/python.exe scripts/cleanup_test_result.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.connection import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        n = db.execute(
            text(
                "DELETE FROM assessment_results "
                "WHERE conferenceUid = 'CONF2610048' AND traineeUid = 'TRN2610002' "
                "AND assessmentSuiteUid = 'ASM2610001' AND maxScore = 5 AND totalScore = 0"
            )
        ).rowcount
        m = db.execute(
            text(
                "DELETE FROM assessment "
                "WHERE conferenceUid = 'CONF2610048' AND traineeUid = 'TRN2610002' "
                "AND assessmentSuiteUid = 'ASM2610001'"
            )
        ).rowcount
        db.commit()
        print(f"Deleted {n} assessment_results row(s), {m} assessment answer row(s)")
        remaining = db.execute(
            text("SELECT COUNT(*) FROM assessment_results WHERE conferenceUid = 'CONF2610048'")
        ).scalar()
        print(f"assessment_results left for CONF2610048: {remaining}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
