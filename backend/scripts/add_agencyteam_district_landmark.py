"""One-off schema migration: add `district` and `landmark` columns to the
real `agencyteam` table.

Context: the Trainer Profile's Local Address section requires District and
State to be filled in (see sanitizeProfile.ts's validateProfileSection on
the frontend), but AgencyTeam - the table real trainers actually log in
through - had no `district` or `landmark` column at all. A real trainer's
District was silently accepted and then dropped on every save
(_apply_profile_update only persists fields present in a table's field
map), so the required-field check could never actually be satisfied for
them. `admin` (internal/seeded accounts) already has both columns.

Safe to run more than once - checks for the column before adding it.

Run once:  venv/Scripts/python.exe -m scripts.add_agencyteam_district_landmark   (from backend/)
"""

from sqlalchemy import text

from app.core.config import settings
from app.database.tenant import tenant_manager

NEW_COLUMNS = [
    ("district", "VARCHAR(80) NULL"),
    ("landmark", "VARCHAR(200) NULL"),
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
