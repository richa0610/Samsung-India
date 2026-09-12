"""One-off script to add more real-looking trainer accounts to `agencyteam`,
filling every column the live table actually has (not just the trimmed
ORM model's subset - see seed_trainers.py's docstring for why raw SQL is
used here). Continues the id/uid numbering the existing 3 trainers
(Aditya Kumar, Meera Iyer, Sanjay Rawat - AT26001-3 / OFF26001-3) already
established. Run from backend/ with:

    venv/Scripts/python.exe scripts/seed_more_trainers.py
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
        "seq": 4,
        "name": "Rohit Verma",
        "gender": "Male",
        "dob": "1988-03-15",
        "designation": "Lead Trainer",
        "jobCity": "Noida",
        "jobState": "Uttar Pradesh",
        "jobPincode": "201301",
    },
    {
        "seq": 5,
        "name": "Sneha Reddy",
        "gender": "Female",
        "dob": "1992-07-19",
        "designation": "Trainer",
        "jobCity": "Hyderabad",
        "jobState": "Telangana",
        "jobPincode": "500001",
    },
    {
        "seq": 6,
        "name": "Karan Malhotra",
        "gender": "Male",
        "dob": "1989-09-02",
        "designation": "Technical Trainer",
        "jobCity": "Chandigarh",
        "jobState": "Chandigarh",
        "jobPincode": "160001",
    },
    {
        "seq": 7,
        "name": "Priya Nair",
        "gender": "Female",
        "dob": "1991-04-27",
        "designation": "Senior Trainer",
        "jobCity": "Kochi",
        "jobState": "Kerala",
        "jobPincode": "682001",
    },
    {
        "seq": 8,
        "name": "Arjun Deshmukh",
        "gender": "Male",
        "dob": "1986-12-11",
        "designation": "Trainer",
        "jobCity": "Nagpur",
        "jobState": "Maharashtra",
        "jobPincode": "440001",
    },
]

for t in TRAINERS:
    first, *rest = t["name"].lower().split(" ")
    last = rest[-1] if rest else ""
    slug = f"{first}.{last}"
    t["phone"] = 9988770000 + t["seq"]
    t["altPhone"] = 9988770100 + t["seq"]
    t["email"] = f"{slug}@example.com"
    t["officialEmail"] = f"{slug}@samsung.com"
    t["username"] = str(t["phone"])
    t["agencyTeamUid"] = f"AT260{t['seq']:02d}"
    t["offerId"] = f"OFF260{t['seq']:02d}"

INSERT_SQL = text(
    """
    INSERT INTO agencyteam
        (agencyTeamUid, companyUid, company, name, email, phone, altPhone,
         officialEmail, dob, gender, offerId, designation, role, jobCity,
         jobState, jobPincode, profilePhoto, username, password, status)
    VALUES
        (:agencyTeamUid, :companyUid, :company, :name, :email, :phone, :altPhone,
         :officialEmail, :dob, :gender, :offerId, :designation, :role, :jobCity,
         :jobState, :jobPincode, :profilePhoto, :username, :password, :status)
    """
)

db = SessionLocal()
try:
    for t in TRAINERS:
        existing = db.execute(
            text("SELECT id FROM agencyteam WHERE username = :username OR offerId = :offerId"),
            {"username": t["username"], "offerId": t["offerId"]},
        ).first()
        if existing:
            print(f"Skipping {t['name']!r} ({t['username']}) - already exists")
            continue
        db.execute(
            INSERT_SQL,
            {
                "agencyTeamUid": t["agencyTeamUid"],
                "companyUid": "CMP26001",
                "company": "Samsung India",
                "name": t["name"],
                "email": t["email"],
                "phone": t["phone"],
                "altPhone": t["altPhone"],
                "officialEmail": t["officialEmail"],
                "dob": t["dob"],
                "gender": t["gender"],
                "offerId": t["offerId"],
                "designation": t["designation"],
                "role": "trainer",
                "jobCity": t["jobCity"],
                "jobState": t["jobState"],
                "jobPincode": t["jobPincode"],
                "profilePhoto": "defaultfile.png",
                "username": t["username"],
                "password": hash_password(DEFAULT_PASSWORD),
                "status": "Approved",
            },
        )
        print(f"Created trainer {t['offerId']} / {t['username']} ({t['name']})")
    db.commit()
finally:
    db.close()
