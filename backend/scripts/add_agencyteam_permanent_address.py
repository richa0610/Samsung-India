"""One-off schema migration: add `permanentCity`, `permanentDistrict`,
`permanentState`, `permanentPinCode`, `permanentLandmark` columns to the
real `agencyteam` table, matching the columns `admin` already has
(see models/admin.py).

Context: the Trainer Profile's Local Address section is getting a
Permanent Address block (with a "same as local" toggle that copies
Local's values across), but AgencyTeam - the table real trainers
actually log in through - had no columns to store a permanent address
in at all. Same gap already fixed once for district/landmark
(add_agencyteam_district_landmark.py).

Safe to run more than once - checks for each column before adding it.

Run once:  venv/Scripts/python.exe -m scripts.add_agencyteam_permanent_address   (from backend/)
"""

from sqlalchemy import text

from app.core.config import settings
from app.database.tenant import tenant_manager

NEW_COLUMNS = [
    ("permanentCity", "VARCHAR(180) NULL"),
    ("permanentDistrict", "VARCHAR(180) NULL"),
    ("permanentState", "VARCHAR(180) NULL"),
    ("permanentPinCode", "VARCHAR(180) NULL"),
    ("permanentLandmark", "VARCHAR(180) NULL"),
]


def main() -> None:
    db = tenant_manager.get_session(settings.DEFAULT_TENANT_ID)
    try:
        existing = {
            row[0] for row in db.execute(text("SHOW COLUMNS FROM agencyteam")).fetchall()
        }
        for name, ddl in NEW_COLUMNS:
            if name in existing:
                print(f"Column {name!r} already exists, skipping.")
                continue
            print(f"Adding column {name!r}...")
            db.execute(text(f"ALTER TABLE agencyteam ADD COLUMN {name} {ddl}"))
        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
