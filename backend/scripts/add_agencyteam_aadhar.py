"""One-off schema migration: add `aadharImage` column to the real
`agencyteam` table, matching the column `admin` already has
(see models/admin.py).

Context: the Trainer Profile's Documents section lets a trainer pick and
upload their Aadhaar card (see trainer_service.upload_aadhar_document),
but AgencyTeam - the table real trainers actually log in through - had
no column to store the resulting file path in at all. Same gap already
fixed for district/landmark and the permanent address fields.

Safe to run more than once - checks for the column before adding it.

Run once:  venv/Scripts/python.exe -m scripts.add_agencyteam_aadhar   (from backend/)
"""

from sqlalchemy import text

from app.core.config import settings
from app.database.tenant import tenant_manager


def main() -> None:
    db = tenant_manager.get_session(settings.DEFAULT_TENANT_ID)
    try:
        existing = {
            row[0] for row in db.execute(text("SHOW COLUMNS FROM agencyteam")).fetchall()
        }
        if "aadharImage" in existing:
            print("Column 'aadharImage' already exists, skipping.")
        else:
            print("Adding column 'aadharImage'...")
            db.execute(text("ALTER TABLE agencyteam ADD COLUMN aadharImage VARCHAR(300) NULL"))
        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
