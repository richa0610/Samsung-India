"""One-off: seed 10 Approved trainings per trainer (5 for tomorrow, 5 for the
day after) so the trainer app has a full, ready-to-start Training List and the
trainee app has live sessions to join.

Run from backend/ with:
    venv/Scripts/python.exe scripts/seed_bulk_trainings.py

Every conference is created via the ORM so the `before_insert` UID hook
assigns a sequential CONF26NNNNN id. Idempotency: re-running adds another
batch - it does not upsert. Delete the rows first if you want a clean redo.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401  (registers the before_insert UID hooks)
from app.database.connection import SessionLocal
from app.models.conference import Conference

# Trainer username (== conference.trainerEmployeeId) -> display name.
TRAINERS = {
    "9988770001": "Aditya Kumar",
    "9988770002": "Meera Iyer",
    "9988770003": "Sanjay Rawat",
    "9988770004": "Rohit Verma",
    "9988770005": "Sneha Reddy",
    "9988770006": "Karan Malhotra",
    "9988770007": "Priya Nair",
    "9988770008": "Arjun Deshmukh",
    "demotrainer": "Demo Trainer",
}

DATES = ["2026-09-02", "2026-09-03"]
START_TIMES = ["09:00 AM", "10:30 AM", "12:00 PM", "02:00 PM", "03:30 PM"]

VENUES = [
    # venueUid, district, state, lat, lon
    ("VEN2610001", "Noida", "Uttar Pradesh", "28.57210000", "77.32100000"),
    ("VEN2610002", "Gurugram", "Haryana", "28.45950000", "77.02660000"),
    ("VEN2610003", "New Delhi", "Delhi", "28.63280000", "77.21950000"),
    ("VEN2610004", "Lucknow", "Uttar Pradesh", "26.84670000", "80.94620000"),
    ("VEN2610005", "Faridabad", "Haryana", "28.40890000", "77.31780000"),
]

TITLES = [
    "Galaxy S26 Product Knowledge",
    "Galaxy Z Fold7 Deep Dive",
    "AI Camera Features Workshop",
    "Retail Excellence Program",
    "Galaxy Watch8 Selling Skills",
    "Galaxy Buds3 Pro Training",
    "One UI 8 Feature Walkthrough",
    "Galaxy Tab S11 Productivity Training",
    "Neo QLED TV Demo Training",
    "Customer Experience Masterclass",
]

BATCH_SIZES = ["20", "25", "30", "15", "25"]
ZONES = [("North Zone", "Delhi NCR"), ("North Zone", "UP West"), ("North Zone", "Haryana")]

STANDARD_TEST_SUITE = "ASM2610001"  # Galaxy S26 Post Training Test, 5 q -> STANDARD_TEST
LIVE_QUIZ_SUITE = "ASM2610003"  # Quiz, 3 q -> LIVE_QUIZ (via sessionConfig)
SURVEY_SUITE = "ASM2610004"  # Survey, 3 questions -> SURVEY


def _shift(time_str: str, minutes: int) -> str:
    return (datetime.strptime(time_str, "%I:%M %p") + timedelta(minutes=minutes)).strftime("%I:%M %p")


def _session_config(start: str) -> str:
    return json.dumps(
        {
            "attendance": {
                "checkInOpens": start,
                "checkOutCloses": _shift(start, 20),
                "geoFencing": True,
            },
            "standardTest": {
                "category": "Product Knowledge",
                "startTime": _shift(start, 30),
                "endTime": _shift(start, 75),
                "checkIn": True,
                "unlockCondition": "Manual",
            },
            "liveQuiz": {
                "assessmentSuiteUid": LIVE_QUIZ_SUITE,
                "category": "Product Knowledge",
                "startTime": _shift(start, 80),
                "endTime": _shift(start, 110),
                "unlockCondition": "Manual",
            },
            "survey": {
                "category": "Feedback",
                "startTime": _shift(start, 115),
                "endTime": _shift(start, 145),
                "checkIn": True,
                "unlockCondition": "Manual",
            },
        }
    )


def main() -> None:
    db = SessionLocal()
    now = datetime.now()
    created = []
    try:
        for emp_id, trainer_name in TRAINERS.items():
            slot = 0
            for date_str in DATES:
                for i in range(5):
                    start = START_TIMES[i]
                    venue_uid, district, state, lat, lon = VENUES[slot % len(VENUES)]
                    zone, region = ZONES[slot % len(ZONES)]
                    conf = Conference(
                        zone=zone,
                        region=region,
                        company="Samsung India",
                        requestedBy="Training Ops",
                        trainerEmployeeId=emp_id,
                        trainerName=trainer_name,
                        conferenceType="Non Residential Conference",
                        conferenceDate=date_str,
                        conferenceTime=start,
                        conferenceStatus="Scheduled",
                        liveQuizState="IDLE",
                        enableCheckIn=1,
                        trainingHub=f"{district} Training Hub",
                        audience="Retail Sales Executives",
                        sessionType="Classroom Training",
                        trainingType="Product Training",
                        batchSize=BATCH_SIZES[slot % len(BATCH_SIZES)],
                        confirmedPax=BATCH_SIZES[slot % len(BATCH_SIZES)],
                        attendanceSheetPax="0",
                        suiteTitle=TITLES[slot % len(TITLES)],
                        state=state,
                        district=district,
                        venueUid=venue_uid,
                        geoLatitude=lat,
                        geoLongitude=lon,
                        geoRadius=100,
                        assessmentFor="Post Training",
                        postAssessmentUid=STANDARD_TEST_SUITE,
                        surveyUid=SURVEY_SUITE,
                        noOfQuestion="3",
                        sessionConfig=_session_config(start),
                        updatedBy="seed_bulk_trainings",
                        updationOn=now,
                        status="Approved",
                        auditStatus="Approved",
                        timestamp=now,
                    )
                    db.add(conf)
                    db.flush()  # assign conferenceUid via before_insert hook
                    created.append((conf.conferenceUid, emp_id, date_str, start, conf.suiteTitle))
                    slot += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Created {len(created)} conferences:")
    for uid, emp, date_str, start, title in created:
        print(f"  {uid}  {emp:12}  {date_str} {start}  {title}")


if __name__ == "__main__":
    main()
