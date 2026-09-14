"""One-off script to seed sample real-looking Venue and Checklist
(Category/SubCategory) reference data, powering the Add Training form's
Venue and Checklist pickers. Run from backend/ with:

    venv/Scripts/python.exe scripts/seed_catalog.py

`district` values match the district `value` codes in
src/data/states.ts, so the Venue picker's State/District gating filters
correctly against real rows.
"""

import sys
import uuid
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import SessionLocal

VENUES = [
    {"name": "Main Auditorium", "zone": "North Zone", "region": "North 1", "city": "Noida", "district": "noida", "state": "Uttar Pradesh", "venueType": "Auditorium"},
    {"name": "Conference Hall A", "zone": "North Zone", "region": "North 2", "city": "Gurugram", "district": "gurugram", "state": "Haryana", "venueType": "Conference Hall"},
    {"name": "Conference Hall B", "zone": "North Zone", "region": "North 1", "city": "New Delhi", "district": "new_delhi", "state": "Delhi", "venueType": "Conference Hall"},
    {"name": "Training Room 1", "zone": "North Zone", "region": "North 3", "city": "Lucknow", "district": "lucknow", "state": "Uttar Pradesh", "venueType": "Training Room"},
    {"name": "Training Room 2", "zone": "North Zone", "region": "North 2", "city": "Faridabad", "district": "faridabad", "state": "Haryana", "venueType": "Training Room"},
]

CHECKLIST_ITEMS = [
    "Hall",
    "Projector",
    "Microphone Set",
    "Attendance Sheet",
    "Feedback Forms",
    "ID Cards",
    "Refreshments",
    "Banner/Standee",
]

db = SessionLocal()
try:
    existing_venues = {
        row[0] for row in db.execute(text("SELECT name FROM venue")).fetchall()
    }
    for venue in VENUES:
        if venue["name"] in existing_venues:
            print(f"Skipping venue {venue['name']!r} - already exists")
            continue
        db.execute(
            text(
                """
                INSERT INTO venue
                    (venueUid, zone, region, company, name, city, district, state, venueType, status)
                VALUES
                    (:venueUid, :zone, :region, :company, :name, :city, :district, :state, :venueType, :status)
                """
            ),
            {
                "venueUid": uuid.uuid4().hex,
                "zone": venue["zone"],
                "region": venue["region"],
                "company": "Samsung India",
                "name": venue["name"],
                "city": venue["city"],
                "district": venue["district"],
                "state": venue["state"],
                "venueType": venue["venueType"],
                "status": "Approved",
            },
        )
        print(f"Created venue {venue['name']!r} ({venue['district']})")

    existing_category = db.execute(
        text("SELECT categoryUid FROM category WHERE name = 'Training Checklist'")
    ).first()
    if existing_category:
        category_uid = existing_category[0]
        print("Skipping category 'Training Checklist' - already exists")
    else:
        category_uid = uuid.uuid4().hex
        db.execute(
            text("INSERT INTO category (categoryUid, name, status) VALUES (:uid, :name, :status)"),
            {"uid": category_uid, "name": "Training Checklist", "status": "Approved"},
        )
        print("Created category 'Training Checklist'")

    existing_subcategories = {
        row[0]
        for row in db.execute(
            text("SELECT subCategory FROM subcategory WHERE categoryUid = :uid"),
            {"uid": category_uid},
        ).fetchall()
    }
    for item in CHECKLIST_ITEMS:
        if item in existing_subcategories:
            print(f"Skipping checklist item {item!r} - already exists")
            continue
        db.execute(
            text(
                "INSERT INTO subcategory (subCategoryUid, categoryUid, subCategory, status) "
                "VALUES (:uid, :categoryUid, :subCategory, :status)"
            ),
            {
                "uid": uuid.uuid4().hex,
                "categoryUid": category_uid,
                "subCategory": item,
                "status": "Approved",
            },
        )
        print(f"Created checklist item {item!r}")

    db.commit()
finally:
    db.close()
