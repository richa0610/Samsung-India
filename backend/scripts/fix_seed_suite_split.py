"""One-off: on the bulk-seeded trainings, point the Standard Test module at a
different assessment suite from the Live Quiz module so the Session Report's
two participant tables are actually distinct.

    Standard Test  -> ASM2610001 (Galaxy S26 Post Training Test)
    Live Quiz      -> ASM2610003 (kept, from sessionConfig.liveQuiz)

Run from backend/ with:
    venv/Scripts/python.exe scripts/fix_seed_suite_split.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

from app.database.connection import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        updated = db.execute(
            text(
                "UPDATE conference SET postAssessmentUid = 'ASM2610001' "
                "WHERE updatedBy = 'seed_bulk_trainings' AND postAssessmentUid = 'ASM2610003'"
            )
        ).rowcount
        db.commit()
        print(f"Updated {updated} rows: postAssessmentUid -> ASM2610001")
        for row in db.execute(
            text(
                "SELECT postAssessmentUid, COUNT(*) n FROM conference "
                "WHERE updatedBy = 'seed_bulk_trainings' GROUP BY postAssessmentUid"
            )
        ):
            print(" ", dict(row._mapping))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
