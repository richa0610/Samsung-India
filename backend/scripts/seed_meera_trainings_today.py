"""One-off: 5 Approved trainings for TODAY (2026-09-03) for trainer Meera Iyer
(9988770002), GEOFENCING OFF, each with 6 pre-assigned "Pending" roster rows
in the attendance table.

Purpose: exercise the trainer Session Dashboard's Audience Breakdown -
  - a roster trainee who joins via QR  -> ASSIGNED
  - a non-roster existing trainee who logs in + joins  -> UNASSIGNED
  - a brand-new trainee (scan QR -> register -> join)  -> FRESH

Run from backend/ with:
    venv/Scripts/python.exe scripts/seed_meera_trainings_today.py

Conferences are created via the ORM so the before_insert hook assigns a
sequential CONF26NNNNN id. Re-running ADDS another batch (no upsert) - delete
the rows first for a clean redo.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401  (registers the before_insert UID hooks)
from app.database.connection import SessionLocal
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee

TRAINER_ID = "9988770002"
TRAINER_NAME = "Meera Iyer"
DATE = "2026-09-03"

STANDARD_TEST_SUITE = "ASM2610001"  # -> STANDARD_TEST (conference.postAssessmentUid)
LIVE_QUIZ_SUITE = "ASM2610003"  # -> LIVE_QUIZ (sessionConfig.liveQuiz)
SURVEY_SUITE = "ASM2610004"  # -> SURVEY (conference.surveyUid)

# (title, start time, district, state) - one per training.
TRAININGS = [
    ("Galaxy S26 Product Knowledge", "09:00 AM", "Gurugram", "Haryana"),
    ("Galaxy Z Fold7 Deep Dive", "10:30 AM", "Bengaluru", "Karnataka"),
    ("AI Camera Features Workshop", "12:00 PM", "Pune", "Maharashtra"),
    ("Retail Excellence Program", "02:00 PM", "Faridabad", "Haryana"),
    ("Galaxy Watch8 Selling Skills", "03:30 PM", "Mysuru", "Karnataka"),
]

# Roster pool (all Approved, spanning Haryana / Karnataka / Maharashtra). Each
# training gets a rotating window of 6 so the per-session numbers differ.
ROSTER_POOL = [
    "TRN2610001", "TRN2610002", "TRN2610003", "TRN2610004", "TRN2610005", "TRN2610006",
    "TRN2610007", "TRN2610008", "TRN2610009", "TRN2610010", "TRN2610011", "TRN2610013",
]


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


def _roster_for(index: int) -> list[str]:
    start = (index * 2) % len(ROSTER_POOL)
    return [ROSTER_POOL[(start + offset) % len(ROSTER_POOL)] for offset in range(6)]


def main() -> None:
    db = SessionLocal()
    now = datetime.now()
    phones = {t.traineeUid: (t.name, t.phone) for t in db.query(Trainee).all()}
    created: list[tuple] = []
    try:
        for i, (title, start, district, state) in enumerate(TRAININGS):
            conf = Conference(
                zone="North Zone",
                region=f"{state} Region",
                company="Samsung India",
                requestedBy="Training Ops",
                trainerEmployeeId=TRAINER_ID,
                trainerName=TRAINER_NAME,
                conferenceType="Non Residential Conference",
                conferenceDate=DATE,
                conferenceTime=start,
                conferenceStatus="Scheduled",
                liveQuizState="IDLE",
                enableCheckIn=1,
                trainingHub=f"{district} Training Hub",
                audience="Retail Sales Executives",
                sessionType="Classroom Training",
                trainingType="Product Training",
                batchSize="25",
                confirmedPax="25",
                attendanceSheetPax="0",
                suiteTitle=title,
                state=state,
                district=district,
                # Geofencing OFF: no venue coordinates + geoFencing:false in the
                # session config - either one alone disables geofence_enabled().
                venueUid=None,
                geoLatitude=None,
                geoLongitude=None,
                assessmentFor="Post Training",
                postAssessmentUid=STANDARD_TEST_SUITE,
                surveyUid=SURVEY_SUITE,
                noOfQuestion="3",
                sessionConfig=_session_config(start),
                updatedBy="seed_meera_trainings_today",
                updationOn=now,
                status="Approved",
                auditStatus="Approved",
                timestamp=now,
            )
            db.add(conf)
            db.flush()  # assign conferenceUid via before_insert hook

            roster = _roster_for(i)
            for trainee_uid in roster:
                name, phone = phones.get(trainee_uid, (trainee_uid, None))
                db.add(
                    Attendance(
                        conferenceUid=conf.conferenceUid,
                        trainerUid=TRAINER_ID,
                        traineeUid=trainee_uid,
                        phone=phone,
                        status="Pending",
                    )
                )
            created.append((conf.conferenceUid, title, DATE, start, roster))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"\nCreated {len(created)} trainings for {TRAINER_NAME} ({TRAINER_ID}) on {DATE}, geofencing OFF:\n")
    for uid, title, date_str, start, roster in created:
        print(f"  {uid}  {date_str} {start}  {title}")
        print("    assigned roster (6):")
        for trainee_uid in roster:
            name, phone = phones.get(trainee_uid, (trainee_uid, None))
            print(f"      {trainee_uid}  {name:<20}  {phone}")
        print()

    off_roster = [uid for uid in phones if uid not in set(ROSTER_POOL)]
    print("  Off-roster trainees (join -> NOT ALLOCATED / Unassigned):")
    for trainee_uid in sorted(off_roster)[:8]:
        name, phone = phones[trainee_uid]
        print(f"      {trainee_uid}  {name:<20}  {phone}")


if __name__ == "__main__":
    main()
