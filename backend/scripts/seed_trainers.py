"""One-off script to seed sample real-looking trainer accounts into
`agencyteam` (the org-authoritative table for real trainers, per
seed_admin.py's comment) and link a few existing `trainee` rows that
have no assigned trainer yet. Run from backend/ with:

    venv/Scripts/python.exe scripts/seed_trainers.py

`agencyteam.trainerEmployeeId`-style linking on other tables actually
stores the trainer's `username` (see `trainee.trainerEmployeeId` /
`conference.trainerEmployeeId`, resolved via AgencyTeam.username in
app/services/training_service.py's `_resolve_performer_names`), not a
separate employee-id column - so `username` doubles as that identifier here.

Uses raw SQL for the insert/update because the `AgencyTeam` ORM model
is deliberately trimmed to the columns the app currently reads
(see app/models/agency_team.py); the underlying `agencyteam` table
still has the richer columns (email, phone, designation, etc.) from
the original schema, so we write straight to them.
"""

import sys
import uuid
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database.connection import SessionLocal

DEFAULT_PASSWORD = "Trainer@123"

TRAINERS = [
    {
        "phone": 9876543210,
        "name": "Ankit Sharma",
        "email": "ankit.sharma@samsung.com",
        "designation": "Senior Trainer",
        "jobCity": "Gurugram",
        "jobState": "Haryana",
    },
    {
        "phone": 9845123456,
        "name": "Priya Nair",
        "email": "priya.nair@samsung.com",
        "designation": "Trainer",
        "jobCity": "Bengaluru",
        "jobState": "Karnataka",
    },
    {
        "phone": 9811223344,
        "name": "Rohit Verma",
        "email": "rohit.verma@samsung.com",
        "designation": "Lead Trainer",
        "jobCity": "Noida",
        "jobState": "Uttar Pradesh",
    },
    {
        "phone": 9963321100,
        "name": "Sneha Reddy",
        "email": "sneha.reddy@samsung.com",
        "designation": "Trainer",
        "jobCity": "Hyderabad",
        "jobState": "Telangana",
    },
    {
        "phone": 9888112233,
        "name": "Vikram Singh",
        "email": "vikram.singh@samsung.com",
        "designation": "Senior Trainer",
        "jobCity": "Chandigarh",
        "jobState": "Punjab",
    },
]
for trainer in TRAINERS:
    trainer["username"] = str(trainer["phone"])

INSERT_SQL = text(
    """
    INSERT INTO agencyteam
        (agencyTeamUid, company, name, email, phone, officialEmail,
         designation, role, jobCity, jobState, username, password, status)
    VALUES
        (:agencyTeamUid, :company, :name, :email, :phone, :officialEmail,
         :designation, :role, :jobCity, :jobState, :username, :password, :status)
    """
)

db = SessionLocal()
try:
    created_usernames = []
    for trainer in TRAINERS:
        existing = db.execute(
            text("SELECT id FROM agencyteam WHERE username = :username"),
            {"username": trainer["username"]},
        ).first()
        if existing:
            print(f"Skipping trainer {trainer['username']!r} - already exists")
            continue
        db.execute(
            INSERT_SQL,
            {
                "agencyTeamUid": uuid.uuid4().hex,
                "company": "Samsung India",
                "name": trainer["name"],
                "email": trainer["email"],
                "phone": trainer["phone"],
                "officialEmail": trainer["email"],
                "designation": trainer["designation"],
                "role": "trainer",
                "jobCity": trainer["jobCity"],
                "jobState": trainer["jobState"],
                "username": trainer["username"],
                "password": hash_password(DEFAULT_PASSWORD),
                "status": "Approved",
            },
        )
        created_usernames.append(trainer["username"])
        print(f"Created trainer {trainer['username']!r} ({trainer['name']})")

    db.commit()

    # Link a few existing trainee rows that have no trainer assigned yet
    # to the newly seeded trainers, round-robin, so they show up as
    # actually trained by someone instead of dangling NULLs.
    if created_usernames:
        unassigned = db.execute(
            text("SELECT id FROM trainee WHERE trainerEmployeeId IS NULL ORDER BY id")
        ).fetchall()
        for i, (trainee_id,) in enumerate(unassigned):
            trainer = TRAINERS[i % len(TRAINERS)]
            db.execute(
                text(
                    "UPDATE trainee SET trainerEmployeeId = :emp, trainerName = :name "
                    "WHERE id = :id"
                ),
                {"emp": trainer["username"], "name": trainer["name"], "id": trainee_id},
            )
            print(f"Linked trainee id={trainee_id} -> trainer {trainer['username']!r}")
        db.commit()
finally:
    db.close()
