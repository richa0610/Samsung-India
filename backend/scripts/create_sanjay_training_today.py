"""One-off: a single Approved training for TODAY for trainer Sanjay Rawat
(9988770003), geofencing OFF (no venue coordinates + geoFencing:false in the
session config - same convention as create_meera_training_today.py).

Run from backend/ with:
    venv/Scripts/python.exe scripts/create_sanjay_training_today.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401  (registers the before_insert UID hooks)
from app.database.connection import SessionLocal
from app.models.conference import Conference

TRAINER_ID = "9988770003"
TRAINER_NAME = "Sanjay Rawat"
DATE = datetime.now().strftime("%Y-%m-%d")
START = "11:00 AM"
TITLE = "Galaxy Buds & Wearables Training"

STANDARD_TEST_SUITE = "ASM2610001"
LIVE_QUIZ_SUITE = "ASM2610003"
SURVEY_SUITE = "ASM2610004"


def _shift(time_str: str, minutes: int) -> str:
    return (datetime.strptime(time_str, "%I:%M %p") + timedelta(minutes=minutes)).strftime("%I:%M %p")


def _session_config(start: str) -> str:
    return json.dumps(
        {
            "attendance": {
                "checkInOpens": start,
                "checkOutCloses": _shift(start, 20),
                "geoFencing": False,
            },
            "standardTest": {
                "category": "Product Knowledge",
                "startTime": _shift(start, 30),
                "endTime": _shift(start, 75),
                "checkIn": True,
                "unlockCondition": "Manual Broadcast",
            },
            "liveQuiz": {
                "assessmentSuiteUid": LIVE_QUIZ_SUITE,
                "category": "Product Knowledge",
                "startTime": _shift(start, 80),
                "endTime": _shift(start, 110),
                "unlockCondition": "Manual Broadcast",
            },
            "survey": {
                "category": "Feedback",
                "startTime": _shift(start, 115),
                "endTime": _shift(start, 145),
                "checkIn": True,
                "unlockCondition": "Manual Broadcast",
            },
        }
    )


def main() -> None:
    db = SessionLocal()
    now = datetime.now()
    try:
        conf = Conference(
            zone="North Zone",
            region="Uttar Pradesh Region",
            company="Samsung India",
            requestedBy="Training Ops",
            trainerEmployeeId=TRAINER_ID,
            trainerName=TRAINER_NAME,
            conferenceType="Non Residential Conference",
            conferenceDate=DATE,
            conferenceTime=START,
            conferenceStatus="Scheduled",
            liveQuizState="IDLE",
            enableCheckIn=1,
            trainingHub="Noida Training Hub",
            audience="Retail Sales Executives",
            sessionType="Classroom Training",
            trainingType="Product Training",
            batchSize="25",
            confirmedPax="25",
            attendanceSheetPax="0",
            suiteTitle=TITLE,
            state="Uttar Pradesh",
            district="Noida",
            # Geofencing OFF: no venue coordinates + geoFencing:false in the
            # session config - either one alone disables geofence_enabled().
            venueUid=None,
            geoLatitude=None,
            geoLongitude=None,
            assessmentFor="Post Training",
            postAssessmentUid=STANDARD_TEST_SUITE,
            surveyUid=SURVEY_SUITE,
            noOfQuestion="3",
            sessionConfig=_session_config(START),
            updatedBy="create_sanjay_training_today",
            updationOn=now,
            status="Approved",
            auditStatus="Approved",
            timestamp=now,
        )
        db.add(conf)
        db.commit()
        db.refresh(conf)
    except Exception:
        db.rollback()
        raise
    finally:
        conference_uid = conf.conferenceUid
        db.close()

    print(f"Created {conference_uid}  {DATE} {START}  {TITLE}  for {TRAINER_NAME} ({TRAINER_ID}) - geofencing OFF")


if __name__ == "__main__":
    main()
