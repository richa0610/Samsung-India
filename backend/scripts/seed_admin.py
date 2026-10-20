"""One-off script to seed demo admin/trainer accounts. Run from backend/ with:
venv/Scripts/python.exe scripts/seed_admin.py

`demoadmin` seeds into the legacy `admin` table (admin-panel accounts).
`demotrainer` seeds into BOTH `admin` and `agencyteam` - login checks
`admin` first and falls back to `agencyteam`, so keeping it in both lets
it authenticate either way while `agencyteam` becomes the org-authoritative
source for real trainers going forward.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam

ADMIN_ACCOUNTS = [
    {"username": "admin", "password": "1234", "name": "Admin", "role": "admin"},
    {"username": "demoadmin", "password": "1234", "name": "Demo Admin", "role": "admin"},
    {"username": "demotrainer", "password": "1234", "name": "Demo Trainer", "role": "trainer"},
    {"username": "Tushar", "password": "1234", "name": "Tushar", "role": "trainer"},
]

AGENCY_TEAM_ACCOUNTS = [
    {"username": "demotrainer", "password": "1234", "name": "Demo Trainer", "role": "trainer", "status": "Approved"},
    {"username": "Tushar", "password": "1234", "name": "Tushar", "role": "trainer", "status": "Approved"},
]

db = SessionLocal()
try:
    for account in ADMIN_ACCOUNTS:
        existing = db.query(Admin).filter(Admin.username == account["username"]).first()
        if existing:
            print(f"Skipping admin {account['username']!r} - already exists")
            continue
        db.add(
            Admin(
                username=account["username"],
                password=hash_password(account["password"]),
                name=account["name"],
                role=account["role"],
            )
        )
        print(f"Created admin {account['username']!r} ({account['role']})")

    for account in AGENCY_TEAM_ACCOUNTS:
        existing = db.query(AgencyTeam).filter(AgencyTeam.username == account["username"]).first()
        if existing:
            print(f"Skipping agencyteam {account['username']!r} - already exists")
            continue
        db.add(
            AgencyTeam(
                username=account["username"],
                password=hash_password(account["password"]),
                name=account["name"],
                role=account["role"],
                status=account["status"],
            )
        )
        print(f"Created agencyteam {account['username']!r} ({account['role']})")

    db.commit()
finally:
    db.close()
