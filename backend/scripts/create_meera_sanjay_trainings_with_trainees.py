"""One-off: 3 Approved trainings (geofencing OFF) across Meera Iyer and
Sanjay Rawat, spanning today and tomorrow, each with 2 trainees pre-assigned
(a "Pending" attendance row per trainee - see app/utils/helpers.py
attendance_is_assigned) so they self-admit via Secure Check-In instead of
being trainer-gated walk-ins. Also creates the 2 trainees themselves with
fixed, easy-to-share phone numbers for login (trainee login is phone-only,
no password - see trainee_service.login).

Run from backend/ with:
    ../venv/Scripts/python.exe scripts/create_meera_sanjay_trainings_with_trainees.py
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

TODAY = datetime.now().strftime("%Y-%m-%d")
TOMORROW = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
TODAY_START = (datetime.now() + timedelta(minutes=20)).strftime("%I:%M %p")
TOMORROW_START = "10:00 AM"

MEERA = {"id": "9988770002", "name": "Meera Iyer"}
SANJAY = {"id": "9988770003", "name": "Sanjay Rawat"}

# Reuses the original shared suites (5Q/10min Standard Test, 3Q/15min Live
# Quiz, 3Q/5min Survey) - same convention as create_sanjay_training_today.py.
STANDARD_TEST_SUITE = "ASM2610001"
LIVE_QUIZ_SUITE = "ASM2610003"
SURVEY_SUITE = "ASM2610004"

TRAINEES = [
    {"traineeUid": "TRN2610900", "name": "Rohan Mehta", "email": "rohan.mehta.test@example.com", "phone": 9000000001, "gender": "Male", "designation": "Sales Associate"},
    {"traineeUid": "TRN2610901", "name": "Priya Nair", "email": "priya.nair.test@example.com", "phone": 9000000002, "gender": "Female", "designation": "Sales Associate"},
]

TRAININGS = [
    {"trainer": MEERA, "date": TODAY, "start": TODAY_START, "title": "Galaxy S26 Product Training - Batch 1"},
    {"trainer": SANJAY, "date": TODAY, "start": TODAY_START, "title": "Galaxy S26 Product Training - Batch 2"},
    {"trainer": MEERA, "date": TOMORROW, "start": TOMORROW_START, "title": "Galaxy S26 Product Training - Batch 3"},
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
        # --- Trainees ---------------------------------------------------
        trainee_rows = []
        for t in TRAINEES:
            existing = db.query(Trainee).filter(Trainee.phone == t["phone"]).first()
            if existing:
                trainee_rows.append(existing)
                continue
            trainee = Trainee(
                traineeUid=t["traineeUid"],
                name=t["name"],
                email=t["email"],
                phone=t["phone"],
                gender=t["gender"],
                designation=t["designation"],
                status="Approved",
                jobStatus="Active",
                updatedBy="create_meera_sanjay_trainings_with_trainees",
                updationOn=now,
                timestamp=now,
            )
            db.add(trainee)
            trainee_rows.append(trainee)
        db.flush()

        # --- Trainings ----------------------------------------------------
        created_confs = []
        for spec in TRAININGS:
            conf = Conference(
                zone="North Zone",
                region="Uttar Pradesh Region",
                company="Samsung India",
                requestedBy="Training Ops",
                trainerEmployeeId=spec["trainer"]["id"],
                trainerName=spec["trainer"]["name"],
                conferenceType="Non Residential Conference",
                conferenceDate=spec["date"],
                conferenceTime=spec["start"],
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
                suiteTitle=spec["title"],
                state="Uttar Pradesh",
                district="Noida",
                # Geofencing OFF: no venue coordinates + geoFencing:false in
                # the session config - either alone disables geofence_enabled().
                venueUid=None,
                geoLatitude=None,
                geoLongitude=None,
                assessmentFor="Post Training",
                postAssessmentUid=STANDARD_TEST_SUITE,
                surveyUid=SURVEY_SUITE,
                noOfQuestion="5",
                sessionConfig=_session_config(spec["start"]),
                updatedBy="create_meera_sanjay_trainings_with_trainees",
                updationOn=now,
                status="Approved",
                auditStatus="Approved",
                timestamp=now,
            )
            db.add(conf)
            created_confs.append((conf, spec))
        db.flush()

        # --- Assign both trainees to every training (Pending = roster) ---
        for conf, spec in created_confs:
            for trainee in trainee_rows:
                db.add(
                    Attendance(
                        conferenceUid=conf.conferenceUid,
                        trainerUid=spec["trainer"]["id"],
                        traineeUid=trainee.traineeUid,
                        phone=trainee.phone,
                        status="Pending",
                        updatedBy="create_meera_sanjay_trainings_with_trainees",
                        updationOn=now,
                        timestamp=now,
                    )
                )

        db.commit()
        for conf, _ in created_confs:
            db.refresh(conf)
        for t in trainee_rows:
            db.refresh(t)

        summary = [(c.conferenceUid, spec["trainer"]["name"], spec["date"], spec["start"], spec["title"]) for c, spec in created_confs]
        trainee_summary = [(t.name, t.phone) for t in trainee_rows]
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("Trainings created:")
    for uid, trainer, date, start, title in summary:
        print(f"  {uid}  {date} {start}  {trainer}  - {title}")
    print()
    print("Trainees assigned to all 3 trainings (login = phone number only, no password):")
    for name, phone in trainee_summary:
        print(f"  {name}: {phone}")


if __name__ == "__main__":
    main()
