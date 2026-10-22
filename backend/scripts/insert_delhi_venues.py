import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import app.models  # Registers before_insert UID event hooks
from sqlalchemy.orm import sessionmaker
from app.database.common import CommonSessionLocal
from app.database.connection import SessionLocal
from app.database.tenant import tenant_manager
from app.models.venue import Venue
from app.utils.uid import next_uid

SAMSUNG_ADMIN_UID = "ADM2690226"
DEMO_ADMIN_UID = "ADM2610008"

DELHI_VENUES = [
    {
        "name": "Samsung Executive Briefing Centre - Connaught Place",
        "city": "New Delhi",
        "district": "Central Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "latitude": Decimal("28.63150000"),
        "longitude": Decimal("77.21670000"),
        "venueType": "Auditorium / Training Studio",
        "contactPersonName": "Rajesh Khanna",
        "contactPersonPhone": 9811001101,
    },
    {
        "name": "The Lalit New Delhi - Regal Training Hall",
        "city": "New Delhi",
        "district": "Central Delhi",
        "state": "Delhi",
        "pincode": "110001",
        "latitude": Decimal("28.63280000"),
        "longitude": Decimal("77.22890000"),
        "venueType": "Hotel Conference Hall",
        "contactPersonName": "Sunita Kapoor",
        "contactPersonPhone": 9811001102,
    },
    {
        "name": "Pullman Aerocity Executive Training Centre",
        "city": "New Delhi",
        "district": "South West Delhi",
        "state": "Delhi",
        "pincode": "110075",
        "latitude": Decimal("28.55010000"),
        "longitude": Decimal("77.12150000"),
        "venueType": "Conference Centre",
        "contactPersonName": "Amitabh Sen",
        "contactPersonPhone": 9811001103,
    },
    {
        "name": "Saket Tech & Innovation Training Hub",
        "city": "New Delhi",
        "district": "South Delhi",
        "state": "Delhi",
        "pincode": "110019",
        "latitude": Decimal("28.52840000"),
        "longitude": Decimal("77.21910000"),
        "venueType": "Corporate Training Hub",
        "contactPersonName": "Neha Singhania",
        "contactPersonPhone": 9811001104,
    },
]


def insert_venues_for_tenant(db_session, engine, company_name: str, admin_uid: str, tenant_name: str) -> None:
    now = datetime.now()
    created_uids = []

    for item in DELHI_VENUES:
        # Check if venue with this name already exists in tenant
        existing = db_session.query(Venue).filter(Venue.name == item["name"]).first()
        if existing:
            continue

        with engine.begin() as conn:
            venue_uid = next_uid(conn, "VEN")

        venue = Venue(
            venueUid=venue_uid,
            name=item["name"],
            zone="North Zone",
            region="Delhi NCR",
            company=company_name,
            city=item["city"],
            district=item["district"],
            state=item["state"],
            pincode=item["pincode"],
            latitude=item["latitude"],
            longitude=item["longitude"],
            venueType=item["venueType"],
            contactPersonName=item["contactPersonName"],
            contactPersonPhone=item["contactPersonPhone"],
            status="Approved",
            updatedBy=admin_uid,
            updationOn=now,
            isRead="No",
            timestamp=now,
        )
        db_session.add(venue)
        db_session.commit()
        created_uids.append((venue_uid, item["name"], item["district"]))

    print(f"=== Tenant: {tenant_name} ({company_name}) ===")
    for uid, name, dist in created_uids:
        print(f"  + Added Venue: {uid} | {name} | District: {dist} | UpdatedBy: {admin_uid}")


def main() -> None:
    # 1. Samsung India
    samsung_db = SessionLocal()
    samsung_engine = samsung_db.get_bind()
    try:
        insert_venues_for_tenant(samsung_db, samsung_engine, "Samsung India", SAMSUNG_ADMIN_UID, "Samsung India")
    finally:
        samsung_db.close()

    # 2. Demo Company
    common_db = CommonSessionLocal()
    try:
        demo_engine = tenant_manager.get_engine("demo", common_db=common_db)
        DemoSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=demo_engine)
        demo_db = DemoSessionLocal()
        try:
            insert_venues_for_tenant(demo_db, demo_engine, "DEMO Bharat Electronics Pvt Ltd", DEMO_ADMIN_UID, "Demo Company")
        finally:
            demo_db.close()
    finally:
        common_db.close()


if __name__ == "__main__":
    main()
