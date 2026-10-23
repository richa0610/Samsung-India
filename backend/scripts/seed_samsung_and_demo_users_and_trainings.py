"""
Seeds:
- 2 Trainers in Samsung (mmtbtwob_tops_samsung.agencyteam)
- 2 Trainees in Samsung (mmtbtwob_tops_samsung.trainee)
- 2 Approved Scheduled Trainings in Samsung (mmtbtwob_tops_samsung.conference) with attendees
- 2 Trainers in Demo (mmtbtwob_tops_demo.agencyteam)
- 2 Trainees in Demo (mmtbtwob_tops_demo.trainee)
- 2 Approved Scheduled Trainings in Demo (mmtbtwob_tops_demo.conference) with attendees
- Synchronizes all accounts into the Common DB user_registry.
"""

import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import app.models  # registers before_insert hooks
from app.core.security import hash_password
from app.database.common import CommonSessionLocal
from app.database.tenant import tenant_manager
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.models.venue import Venue
from app.services import user_registry_service

DEFAULT_PASSWORD = "Trainer@123"
HASHED_PASSWORD = hash_password(DEFAULT_PASSWORD)

TODAY = datetime.now().strftime("%Y-%m-%d")
TOMORROW = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
TODAY_START = (datetime.now() + timedelta(minutes=30)).strftime("%I:%M %p")
TOMORROW_START = "10:30 AM"

def _shift(time_str: str, minutes: int) -> str:
    return (datetime.strptime(time_str, "%I:%M %p") + timedelta(minutes=minutes)).strftime("%I:%M %p")

def build_session_config(start: str, test_suite: str, quiz_suite: str, survey_suite: str) -> str:
    return json.dumps({
        "attendance": {
            "checkInOpens": start,
            "checkOutCloses": _shift(start, 25),
            "geoFencing": False,
        },
        "standardTest": {
            "assessmentSuiteUid": test_suite,
            "category": "Product Knowledge",
            "startTime": _shift(start, 30),
            "endTime": _shift(start, 70),
            "checkIn": True,
            "unlockCondition": "Manual Broadcast",
        },
        "liveQuiz": {
            "assessmentSuiteUid": quiz_suite,
            "category": "Product Knowledge",
            "startTime": _shift(start, 75),
            "endTime": _shift(start, 105),
            "unlockCondition": "Manual Broadcast",
        },
        "survey": {
            "assessmentSuiteUid": survey_suite,
            "category": "Feedback",
            "startTime": _shift(start, 110),
            "endTime": _shift(start, 130),
            "checkIn": True,
            "unlockCondition": "Manual Broadcast",
        },
    })

def seed_samsung():
    print("\n================== SEEDING SAMSUNG ==================")
    tenant_uid = "samsung"
    company_name = "Samsung India"
    common_db = CommonSessionLocal()
    db = tenant_manager.get_session(tenant_uid, common_db)

    try:
        # 1. Trainers
        trainers_data = [
            {
                "username": "samsung.trainer1",
                "offerId": "SAM_TRN_101",
                "name": "Karan Malhotra",
                "email": "karan.malhotra@samsung-india.test",
                "phone": 9899110011,
                "designation": "Master Product Trainer",
                "jobCity": "Gurugram",
                "jobState": "Haryana",
            },
            {
                "username": "samsung.trainer2",
                "offerId": "SAM_TRN_102",
                "name": "Neha Kapoor",
                "email": "neha.kapoor@samsung-india.test",
                "phone": 9899110022,
                "designation": "Field Readiness Trainer",
                "jobCity": "Noida",
                "jobState": "Uttar Pradesh",
            },
        ]

        created_trainers = []
        for td in trainers_data:
            trainer = db.query(AgencyTeam).filter(
                (AgencyTeam.username == td["username"]) | (AgencyTeam.phone == td["phone"])
            ).first()
            if not trainer:
                trainer = AgencyTeam(
                    agencyTeamUid=f"AGT{uuid.uuid4().hex[:7].upper()}",
                    username=td["username"],
                    offerId=td["offerId"],
                    name=td["name"],
                    email=td["email"],
                    phone=td["phone"],
                    password=HASHED_PASSWORD,
                    role="trainer",
                    status="Approved",
                    company=company_name,
                    designation=td["designation"],
                    jobCity=td["jobCity"],
                    jobState=td["jobState"],
                )
                db.add(trainer)
                db.flush()
                print(f"Created Samsung Trainer: {trainer.name} ({trainer.username})")
            else:
                trainer.password = HASHED_PASSWORD
                trainer.role = "trainer"
                trainer.status = "Approved"
                trainer.company = company_name
                print(f"Existing Samsung Trainer verified: {trainer.name} ({trainer.username})")
            created_trainers.append(trainer)

        # 2. Trainees
        trainees_data = [
            {
                "phone": 9188001001,
                "username": "samsung.trainee1",
                "employee_id": "SAM_EMP_501",
                "name": "Sameer Joshi",
                "email": "sameer.joshi@samsung-india.test",
                "gender": "Male",
                "designation": "Galaxy Consultant",
                "district": "Gurugram",
                "state": "Haryana",
                "zone": "North Zone",
                "region": "North 1",
            },
            {
                "phone": 9188001002,
                "username": "samsung.trainee2",
                "employee_id": "SAM_EMP_502",
                "name": "Meera Chawla",
                "email": "meera.chawla@samsung-india.test",
                "gender": "Female",
                "designation": "Retail Specialist",
                "district": "New Delhi",
                "state": "Delhi",
                "zone": "North Zone",
                "region": "North 1",
            },
        ]

        created_trainees = []
        for trd in trainees_data:
            trainee = db.query(Trainee).filter(
                (Trainee.phone == trd["phone"]) | (Trainee.username == trd["username"])
            ).first()
            if not trainee:
                trainee = Trainee(
                    traineeUid=f"TRN{uuid.uuid4().hex[:7].upper()}",
                    employee_id=trd["employee_id"],
                    username=trd["username"],
                    name=trd["name"],
                    email=trd["email"],
                    phone=trd["phone"],
                    gender=trd["gender"],
                    designation=trd["designation"],
                    district=trd["district"],
                    state=trd["state"],
                    zone=trd["zone"],
                    region=trd["region"],
                    company=company_name,
                    password=HASHED_PASSWORD,
                    status="Approved",
                    jobStatus="Active",
                )
                db.add(trainee)
                db.flush()
                print(f"Created Samsung Trainee: {trainee.name} ({trainee.phone})")
            else:
                trainee.status = "Approved"
                trainee.jobStatus = "Active"
                trainee.company = company_name
                print(f"Existing Samsung Trainee verified: {trainee.name} ({trainee.phone})")
            created_trainees.append(trainee)

        # 3. Trainings
        venues = db.query(Venue).limit(2).all()
        venue1_uid = venues[0].venueUid if venues else "VEN2610001"
        venue2_uid = venues[1].venueUid if len(venues) > 1 else venue1_uid

        conf_data = [
            {
                "trainer": created_trainers[0],
                "date": TODAY,
                "start": TODAY_START,
                "venue_uid": venue1_uid,
                "title": "Galaxy AI Ecosystem Certification 2026",
                "trainingType": "BROADCAST",
                "sessionType": "Classroom",
            },
            {
                "trainer": created_trainers[1],
                "date": TOMORROW,
                "start": TOMORROW_START,
                "venue_uid": venue2_uid,
                "title": "Neo QLED & SmartThings Integration Masterclass",
                "trainingType": "BROADCAST",
                "sessionType": "Classroom",
            },
        ]

        created_conferences = []
        for c in conf_data:
            conf_uid = f"CONF{uuid.uuid4().hex[:7].upper()}"
            s_config = build_session_config(c["start"], "ASM2610009", "ASM2610010", "ASM2610010")
            conf = Conference(
                conferenceUid=conf_uid,
                trainerEmployeeId=c["trainer"].username,
                trainerName=c["trainer"].name,
                requestedBy=c["trainer"].name,
                company=company_name,
                zone="North Zone",
                region="North 1",
                conferenceDate=c["date"],
                conferenceEndsOn=c["date"],
                conferenceTime=c["start"],
                trainingType=c["trainingType"],
                sessionType=c["sessionType"],
                batchSize=20,
                confirmedPax=2,
                venueUid=c["venue_uid"],
                state="Haryana",
                district="Gurugram",
                status="Approved",
                conferenceStatus="Scheduled",
                enableCheckIn="Yes",
                sessionConfig=s_config,
                postAssessmentUid="ASM2610009",
            )
            db.add(conf)
            db.flush()
            print(f"Created Samsung Training: {conf.conferenceUid} - {c['title']} by {c['trainer'].name} on {c['date']}")
            created_conferences.append(conf)

            # Pre-assign trainees to conference attendance
            for trainee in created_trainees:
                att = db.query(Attendance).filter(
                    Attendance.conferenceUid == conf.conferenceUid,
                    Attendance.traineeUid == trainee.traineeUid,
                ).first()
                if not att:
                    att = Attendance(
                        conferenceUid=conf.conferenceUid,
                        traineeUid=trainee.traineeUid,
                        status="Pending",
                        marked=0,
                        checkInDate=c["date"],
                        checkInTime=c["start"],
                    )
                    db.add(att)
                    print(f"  Assigned Trainee {trainee.name} to {conf.conferenceUid}")

        db.commit()

    finally:
        db.close()
        common_db.close()

def seed_demo():
    print("\n================== SEEDING DEMO ==================")
    tenant_uid = "demo"
    company_name = "DEMO Bharat Electronics Pvt Ltd"
    common_db = CommonSessionLocal()
    db = tenant_manager.get_session(tenant_uid, common_db)

    try:
        # 1. Trainers
        trainers_data = [
            {
                "username": "demo.trainer1",
                "offerId": "DEMO_TRN_201",
                "name": "Sunil Verma",
                "email": "sunil.verma@demoelectronics.in",
                "phone": 9811122091,
                "designation": "Industrial Avionics Trainer",
                "jobCity": "Pune",
                "jobState": "Maharashtra",
            },
            {
                "username": "demo.trainer2",
                "offerId": "DEMO_TRN_202",
                "name": "Kavita Rao",
                "email": "kavita.rao@demoelectronics.in",
                "phone": 9811122092,
                "designation": "IoT & Sensor Specialist Trainer",
                "jobCity": "Bengaluru",
                "jobState": "Karnataka",
            },
        ]

        created_trainers = []
        for td in trainers_data:
            trainer = db.query(AgencyTeam).filter(
                (AgencyTeam.username == td["username"]) | (AgencyTeam.phone == td["phone"])
            ).first()
            if not trainer:
                trainer = AgencyTeam(
                    agencyTeamUid=f"AT_{uuid.uuid4().hex[:8].upper()}",
                    username=td["username"],
                    offerId=td["offerId"],
                    name=td["name"],
                    email=td["email"],
                    phone=td["phone"],
                    password=HASHED_PASSWORD,
                    role="trainer",
                    status="Approved",
                    company=company_name,
                    designation=td["designation"],
                    jobCity=td["jobCity"],
                    jobState=td["jobState"],
                )
                db.add(trainer)
                db.flush()
                print(f"Created Demo Trainer: {trainer.name} ({trainer.username})")
            else:
                trainer.password = HASHED_PASSWORD
                trainer.role = "trainer"
                trainer.status = "Approved"
                trainer.company = company_name
                print(f"Existing Demo Trainer verified: {trainer.name} ({trainer.username})")
            created_trainers.append(trainer)

        # 2. Trainees
        trainees_data = [
            {
                "phone": 9822001191,
                "username": "demo.trainee1",
                "employee_id": "DEMO_EMP_301",
                "name": "Akash Deshmukh",
                "email": "akash.deshmukh@demoelectronics.in",
                "gender": "Male",
                "designation": "Avionics Field Engineer",
                "district": "Pune",
                "state": "Maharashtra",
                "zone": "West Zone",
                "region": "West 1",
            },
            {
                "phone": 9822001192,
                "username": "demo.trainee2",
                "employee_id": "DEMO_EMP_302",
                "name": "Ritu Sengupta",
                "email": "ritu.sengupta@demoelectronics.in",
                "gender": "Female",
                "designation": "Systems Support Executive",
                "district": "Pune",
                "state": "Maharashtra",
                "zone": "West Zone",
                "region": "West 1",
            },
        ]

        created_trainees = []
        for trd in trainees_data:
            trainee = db.query(Trainee).filter(
                (Trainee.phone == trd["phone"]) | (Trainee.username == trd["username"])
            ).first()
            if not trainee:
                trainee = Trainee(
                    traineeUid=f"TRN_{uuid.uuid4().hex[:8].upper()}",
                    employee_id=trd["employee_id"],
                    username=trd["username"],
                    name=trd["name"],
                    email=trd["email"],
                    phone=trd["phone"],
                    gender=trd["gender"],
                    designation=trd["designation"],
                    district=trd["district"],
                    state=trd["state"],
                    zone=trd["zone"],
                    region=trd["region"],
                    company=company_name,
                    password=HASHED_PASSWORD,
                    status="Approved",
                    jobStatus="Active",
                )
                db.add(trainee)
                db.flush()
                print(f"Created Demo Trainee: {trainee.name} ({trainee.phone})")
            else:
                trainee.status = "Approved"
                trainee.jobStatus = "Active"
                trainee.company = company_name
                print(f"Existing Demo Trainee verified: {trainee.name} ({trainee.phone})")
            created_trainees.append(trainee)

        # 3. Trainings
        venues = db.query(Venue).limit(2).all()
        venue1_uid = venues[0].venueUid if venues else "VEN_DEMO_01"
        venue2_uid = venues[1].venueUid if len(venues) > 1 else venue1_uid

        conf_data = [
            {
                "trainer": created_trainers[0],
                "date": TODAY,
                "start": TODAY_START,
                "venue_uid": venue1_uid,
                "title": "Industrial Radar & Telemetry Operations",
                "trainingType": "BROADCAST",
                "sessionType": "Classroom",
            },
            {
                "trainer": created_trainers[1],
                "date": TOMORROW,
                "start": TOMORROW_START,
                "venue_uid": venue2_uid,
                "title": "Avionics Safety Protocols & Sensor Calibrations",
                "trainingType": "BROADCAST",
                "sessionType": "Classroom",
            },
        ]

        for c in conf_data:
            conf_uid = f"CONF_{uuid.uuid4().hex[:7].upper()}"
            s_config = build_session_config(c["start"], "ASM_DEMO_TEST", "ASM_DEMO_QUIZ", "ASM_DEMO_SURVEY")
            conf = Conference(
                conferenceUid=conf_uid,
                trainerEmployeeId=c["trainer"].username,
                trainerName=c["trainer"].name,
                requestedBy=c["trainer"].name,
                company=company_name,
                zone="West Zone",
                region="West 1",
                conferenceDate=c["date"],
                conferenceEndsOn=c["date"],
                conferenceTime=c["start"],
                trainingType=c["trainingType"],
                sessionType=c["sessionType"],
                batchSize=15,
                confirmedPax=2,
                venueUid=c["venue_uid"],
                state="Maharashtra",
                district="Pune",
                status="Approved",
                conferenceStatus="Scheduled",
                enableCheckIn="Yes",
                sessionConfig=s_config,
                postAssessmentUid="ASM_DEMO_TEST",
            )
            db.add(conf)
            db.flush()
            print(f"Created Demo Training: {conf.conferenceUid} - {c['title']} by {c['trainer'].name} on {c['date']}")

            # Pre-assign trainees to conference attendance
            for trainee in created_trainees:
                att = db.query(Attendance).filter(
                    Attendance.conferenceUid == conf.conferenceUid,
                    Attendance.traineeUid == trainee.traineeUid,
                ).first()
                if not att:
                    att = Attendance(
                        conferenceUid=conf.conferenceUid,
                        traineeUid=trainee.traineeUid,
                        status="Pending",
                        marked=0,
                        checkInDate=c["date"],
                        checkInTime=c["start"],
                    )
                    db.add(att)
                    print(f"  Assigned Trainee {trainee.name} to {conf.conferenceUid}")

        db.commit()

    finally:
        db.close()
        common_db.close()

def sync_all_users():
    print("\n================== SYNCING CENTRAL USER REGISTRY ==================")
    common_db = CommonSessionLocal()
    try:
        report = user_registry_service.reconcile_all(common_db)
        print("User Registry reconciled across all tenants.")
    finally:
        common_db.close()

if __name__ == "__main__":
    seed_samsung()
    seed_demo()
    sync_all_users()
    print("\nAll seedings and registry synchronizations completed successfully!")
