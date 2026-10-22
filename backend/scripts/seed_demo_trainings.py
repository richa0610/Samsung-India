"""Seed 2 trainings for every trainer in the 'demo' company tenant.
- Creates standard Assessment Suites and Questions in tops_demo (Test, Quiz, Survey).
- Creates realistic Venues in tops_demo.
- Creates 2 Approved Trainings (1 Today, 1 Tomorrow) for each of the 4 trainers.
- Ensures geofencing is OFF so sessions can be tested without GPS restrictions.
"""

import json
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # registers before_insert hooks
from sqlalchemy import text
from app.database.common import CommonSessionLocal
from app.database.tenant import tenant_manager
from app.models.conference import Conference
from app.models.quiz import AssessmentSuite, Question
from app.models.venue import Venue

TENANT_UID = "demo"
COMPANY_NAME = "DEMO Bharat Electronics Pvt Ltd"

TRAINERS = [
    {
        "employee_id": "OFF26000",
        "username": "demotrainer1",
        "name": "DEMO Trainer",
        "zone": "North Zone",
        "region": "North 1",
        "hub": "Delhi Training Hub",
        "state": "Delhi",
        "district": "New Delhi",
        "titles": [
            "Smart Devices & IoT Systems Training",
            "Advanced Power Electronics & Sensors Seminar",
        ],
    },
    {
        "employee_id": "OFF26001",
        "username": "9811122001",
        "name": "Rajesh Khanna",
        "zone": "North Zone",
        "region": "North 1",
        "hub": "Noida Training Hub",
        "state": "Uttar Pradesh",
        "district": "Noida",
        "titles": [
            "Industrial Avionics & Navigation Systems Workshop",
            "Radar & Communication Hardware Deep Dive",
        ],
    },
    {
        "employee_id": "OFF26002",
        "username": "9811122002",
        "name": "Pooja Hegde",
        "zone": "South Zone",
        "region": "South 1",
        "hub": "Bengaluru Training Hub",
        "state": "Karnataka",
        "district": "Bengaluru",
        "titles": [
            "Defense Communication Tech & Protocols Training",
            "Next-Gen Optoelectronics Certification Batch",
        ],
    },
    {
        "employee_id": "OFF26003",
        "username": "9811122003",
        "name": "Amitabh Sen",
        "zone": "West Zone",
        "region": "West 1",
        "hub": "Mumbai Training Hub",
        "state": "Maharashtra",
        "district": "Mumbai",
        "titles": [
            "Field Systems Reliability & Maintenance Masterclass",
            "Security Systems & Sensor Integration Workshop",
        ],
    },
]

VENUES_DATA = [
    {
        "name": "Radisson Blu Hotel Sector 18",
        "city": "Noida",
        "district": "Noida",
        "state": "Uttar Pradesh",
        "zone": "North Zone",
        "region": "North 1",
        "latitude": 28.5684,
        "longitude": 77.3218,
    },
    {
        "name": "The Leela Palace Bengaluru",
        "city": "Bengaluru",
        "district": "Bengaluru",
        "state": "Karnataka",
        "zone": "South Zone",
        "region": "South 1",
        "latitude": 12.9606,
        "longitude": 77.6484,
    },
    {
        "name": "Grand Hyatt Mumbai Santacruz",
        "city": "Mumbai",
        "district": "Mumbai",
        "state": "Maharashtra",
        "zone": "West Zone",
        "region": "West 1",
        "latitude": 19.0760,
        "longitude": 72.8530,
    },
]

STANDARD_TEST_QUESTIONS = [
    {
        "question": "What is the primary operational frequency range of high-performance radar modules?",
        "options": ["1 GHz - 2 GHz", "8 GHz - 12 GHz (X-band)", "50 Hz - 60 Hz", "300 kHz - 500 kHz"],
        "correct_answer": "B",
        "points": 10,
    },
    {
        "question": "Which communication protocol is widely adopted for ruggedized industrial bus architectures?",
        "options": ["CAN Bus / MIL-STD-1553", "I2C only", "Bluetooth Low Energy", "HTTP/1.1"],
        "correct_answer": "A",
        "points": 10,
    },
    {
        "question": "In dual-redundant power electronics, what prevents reverse voltage feed-through?",
        "options": ["Step-up Transformer", "Schottky ORing Diodes / Ideal Diode Controllers", "Low-pass Filter", "Ferrite Bead"],
        "correct_answer": "B",
        "points": 10,
    },
]

LIVE_QUIZ_QUESTIONS = [
    {
        "question": "What metric defines the signal clarity relative to background RF noise?",
        "options": ["SNR (Signal-to-Noise Ratio)", "Impedance", "Capacitance", "Duty Cycle"],
        "correct_answer": "A",
        "points": 15,
    },
    {
        "question": "Which modulation scheme is standard in spread-spectrum digital transceivers?",
        "options": ["DSSS / QPSK", "AM only", "FM only", "CW only"],
        "correct_answer": "A",
        "points": 15,
    },
    {
        "question": "What does MTBF stand for in hardware reliability assessments?",
        "options": ["Mean Time Between Failures", "Maximum Transmission Bandwidth Factor", "Module Temperature Bias Feedback", "Memory Transfer Buffer Format"],
        "correct_answer": "A",
        "points": 15,
    },
]

SURVEY_QUESTIONS = [
    {
        "question": "How clear were the technical explanations provided during this training session?",
        "options": ["Excellent", "Good", "Satisfactory", "Needs Improvement"],
        "points": 0,
    },
    {
        "question": "How relevant was the course material to your daily field operations?",
        "options": ["Highly Relevant", "Moderately Relevant", "Somewhat Relevant", "Not Relevant"],
        "points": 0,
    },
    {
        "question": "How would you rate the hands-on live quiz and assessment pacing?",
        "options": ["Paced Perfectly", "Too Fast", "Too Slow", "Average"],
        "points": 0,
    },
]


def _session_config(start: str, live_quiz_suite_uid: str) -> str:
    start_dt = datetime.strptime(start, "%I:%M %p")
    def _shift(minutes: int) -> str:
        return (start_dt + timedelta(minutes=minutes)).strftime("%I:%M %p")

    return json.dumps({
        "attendance": {
            "checkInOpens": _shift(0),
            "checkOutCloses": _shift(30),
            "geoFencing": False,
        },
        "standardTest": {
            "category": "Technical Assessment",
            "startTime": _shift(35),
            "endTime": _shift(75),
            "checkIn": True,
            "unlockCondition": "Manual Broadcast",
        },
        "liveQuiz": {
            "assessmentSuiteUid": live_quiz_suite_uid,
            "category": "Live Quiz",
            "startTime": _shift(80),
            "endTime": _shift(110),
            "unlockCondition": "Manual Broadcast",
        },
        "survey": {
            "category": "Session Survey",
            "startTime": _shift(115),
            "endTime": _shift(145),
            "checkIn": True,
            "unlockCondition": "Manual Broadcast",
        },
    })


def seed():
    common_db = CommonSessionLocal()
    tenant_db = tenant_manager.get_session(TENANT_UID, common_db)
    now = datetime.now()

    try:
        # 1. Seed Venues if not present
        print("--- Seeding Venues in tops_demo ---")
        created_venues = []
        for v_data in VENUES_DATA:
            v = tenant_db.query(Venue).filter(Venue.name == v_data["name"]).first()
            if not v:
                v = Venue(
                    name=v_data["name"],
                    city=v_data["city"],
                    district=v_data["district"],
                    state=v_data["state"],
                    zone=v_data["zone"],
                    region=v_data["region"],
                    company=COMPANY_NAME,
                    latitude=v_data["latitude"],
                    longitude=v_data["longitude"],
                    venueType="Hotel Conference Room",
                )
                tenant_db.add(v)
                tenant_db.flush()
                print(f"Created Venue: {v.name} (UID: {v.venueUid})")
            created_venues.append(v)
        tenant_db.commit()

        # 2. Seed Assessment Suites & Questions if not present
        print("\n--- Seeding Assessment Suites in tops_demo ---")
        std_suite = tenant_db.query(AssessmentSuite).filter(AssessmentSuite.assessment_type == "POST TEST").first()
        if not std_suite:
            std_suite = AssessmentSuite(
                courseName="Technical Knowledge Base",
                examTitle="Technical Product Assessment",
                assessment_type="POST TEST",
                noOfQuestion=len(STANDARD_TEST_QUESTIONS),
                testTime="15",
                status="Approved",
                updatedBy="seed_demo_trainings",
                updationOn=now,
                timestamp=now,
            )
            tenant_db.add(std_suite)
            tenant_db.flush()
            for idx, q in enumerate(STANDARD_TEST_QUESTIONS, start=1):
                tenant_db.add(Question(
                    assessmentSuiteUid=std_suite.assessmentSuiteUid,
                    question=q["question"],
                    question_type="multiple_choice",
                    sort_order=idx,
                    options=json.dumps(q["options"]),
                    correct_answer=q["correct_answer"],
                    points=q["points"],
                    status="Approved",
                ))
            print(f"Created Standard Test Suite: {std_suite.examTitle} (UID: {std_suite.assessmentSuiteUid})")

        live_suite = tenant_db.query(AssessmentSuite).filter(AssessmentSuite.assessment_type == "Quiz").first()
        if not live_suite:
            live_suite = AssessmentSuite(
                courseName="Real-Time Competition",
                examTitle="Live Operations Quiz",
                assessment_type="Quiz",
                noOfQuestion=len(LIVE_QUIZ_QUESTIONS),
                testTime="5",
                status="Approved",
                updatedBy="seed_demo_trainings",
                updationOn=now,
                timestamp=now,
            )
            tenant_db.add(live_suite)
            tenant_db.flush()
            for idx, q in enumerate(LIVE_QUIZ_QUESTIONS, start=1):
                tenant_db.add(Question(
                    assessmentSuiteUid=live_suite.assessmentSuiteUid,
                    question=q["question"],
                    question_type="multiple_choice",
                    sort_order=idx,
                    options=json.dumps(q["options"]),
                    correct_answer=q["correct_answer"],
                    points=q["points"],
                    status="Approved",
                ))
            print(f"Created Live Quiz Suite: {live_suite.examTitle} (UID: {live_suite.assessmentSuiteUid})")

        survey_suite = tenant_db.query(AssessmentSuite).filter(AssessmentSuite.assessment_type == "Survey").first()
        if not survey_suite:
            survey_suite = AssessmentSuite(
                courseName="Feedback Assessment",
                examTitle="Training Feedback Survey",
                assessment_type="Survey",
                noOfQuestion=len(SURVEY_QUESTIONS),
                testTime="10",
                status="Approved",
                updatedBy="seed_demo_trainings",
                updationOn=now,
                timestamp=now,
            )
            tenant_db.add(survey_suite)
            tenant_db.flush()
            for idx, q in enumerate(SURVEY_QUESTIONS, start=1):
                tenant_db.add(Question(
                    assessmentSuiteUid=survey_suite.assessmentSuiteUid,
                    question=q["question"],
                    question_type="multiple_choice",
                    sort_order=idx,
                    options=json.dumps(q["options"]),
                    correct_answer=None,
                    points=0,
                    status="Approved",
                ))
            print(f"Created Survey Suite: {survey_suite.examTitle} (UID: {survey_suite.assessmentSuiteUid})")

        tenant_db.commit()

        # 3. Create 2 Trainings for each of the 4 Trainers
        print("\n--- Seeding 2 Trainings for each Trainer ---")
        today_date = date.today().strftime("%Y-%m-%d")
        tomorrow_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        created_trainings = []
        for trainer in TRAINERS:
            # Training 1: Today
            t1_title = trainer["titles"][0]
            start_time_t1 = "10:00 AM"
            end_time_t1 = "01:00 PM"
            conf1 = Conference(
                zone=trainer["zone"],
                region=trainer["region"],
                company=COMPANY_NAME,
                requestedBy="Training Department",
                trainerEmployeeId=trainer["username"],
                trainerName=trainer["name"],
                conferenceType="Non Residential Conference",
                conferenceDate=today_date,
                conferenceEndsOn=today_date,
                conferenceTime=start_time_t1,
                conferenceStatus="Scheduled",
                liveQuizState="IDLE",
                enableCheckIn=1,
                trainingHub=trainer["hub"],
                audience="Field Engineers & Trainees",
                sessionType="Classroom Training",
                trainingType="Product Training",
                batchSize="25",
                confirmedPax="25",
                attendanceSheetPax="0",
                suiteTitle=t1_title,
                state=trainer["state"],
                district=trainer["district"],
                venueUid=created_venues[0].venueUid if created_venues else None,
                geoLatitude=None,
                geoLongitude=None,
                geoRadius=500,
                venueLocationOverridden=0,
                assessmentFor="Post Training",
                postAssessmentUid=std_suite.assessmentSuiteUid,
                surveyUid=survey_suite.assessmentSuiteUid,
                noOfQuestion=str(std_suite.noOfQuestion),
                sessionConfig=_session_config(start_time_t1, live_suite.assessmentSuiteUid),
                updatedBy="seed_demo_trainings",
                updationOn=now,
                status="Approved",
                auditStatus="Approved",
                timestamp=now,
            )
            tenant_db.add(conf1)
            created_trainings.append((trainer["name"], t1_title, today_date, start_time_t1, conf1))

            # Training 2: Tomorrow
            t2_title = trainer["titles"][1]
            start_time_t2 = "02:00 PM"
            end_time_t2 = "05:00 PM"
            conf2 = Conference(
                zone=trainer["zone"],
                region=trainer["region"],
                company=COMPANY_NAME,
                requestedBy="Training Department",
                trainerEmployeeId=trainer["username"],
                trainerName=trainer["name"],
                conferenceType="Non Residential Conference",
                conferenceDate=tomorrow_date,
                conferenceEndsOn=tomorrow_date,
                conferenceTime=start_time_t2,
                conferenceStatus="Scheduled",
                liveQuizState="IDLE",
                enableCheckIn=1,
                trainingHub=trainer["hub"],
                audience="Field Engineers & Trainees",
                sessionType="Classroom Training",
                trainingType="Product Training",
                batchSize="25",
                confirmedPax="25",
                attendanceSheetPax="0",
                suiteTitle=t2_title,
                state=trainer["state"],
                district=trainer["district"],
                venueUid=created_venues[1].venueUid if len(created_venues) > 1 else None,
                geoLatitude=None,
                geoLongitude=None,
                geoRadius=500,
                venueLocationOverridden=0,
                assessmentFor="Post Training",
                postAssessmentUid=std_suite.assessmentSuiteUid,
                surveyUid=survey_suite.assessmentSuiteUid,
                noOfQuestion=str(std_suite.noOfQuestion),
                sessionConfig=_session_config(start_time_t2, live_suite.assessmentSuiteUid),
                updatedBy="seed_demo_trainings",
                updationOn=now,
                status="Approved",
                auditStatus="Approved",
                timestamp=now,
            )
            tenant_db.add(conf2)
            created_trainings.append((trainer["name"], t2_title, tomorrow_date, start_time_t2, conf2))

        tenant_db.commit()

        print("\nAll 8 trainings created successfully:")
        for trainer_name, title, c_date, c_time, conf in created_trainings:
            tenant_db.refresh(conf)
            print(f"- [{conf.conferenceUid}] {trainer_name}: '{title}' on {c_date} at {c_time} (Status: {conf.conferenceStatus}/{conf.status})")

    finally:
        tenant_db.close()
        common_db.close()


if __name__ == "__main__":
    seed()
