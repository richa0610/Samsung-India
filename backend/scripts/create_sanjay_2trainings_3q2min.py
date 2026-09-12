"""One-off: TWO Approved trainings for TODAY for trainer Sanjay Rawat
(9988770003), both starting 10 minutes from run-time, geofencing OFF (same
convention as create_sanjay_training_today.py). Every question module
(Standard Test, Live Quiz, Survey) gets its own fresh 3-question suite with
testTime="2" (2-minute test window), instead of reusing the shared
ASM2610001/3/4 suites which don't match that 3Q/2min shape.

Run from backend/ with:
    ../venv/Scripts/python.exe scripts/create_sanjay_2trainings_3q2min.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401  (registers the before_insert UID hooks)
from app.database.connection import SessionLocal
from app.models.conference import Conference
from app.models.quiz import AssessmentSuite, Question

TRAINER_ID = "9988770003"
TRAINER_NAME = "Sanjay Rawat"
DATE = datetime.now().strftime("%Y-%m-%d")
START = (datetime.now() + timedelta(minutes=10)).strftime("%I:%M %p")
TITLES = [
    "Galaxy Buds & Wearables Training - Batch 1",
    "Galaxy Buds & Wearables Training - Batch 2",
]


def _shift(time_str: str, minutes: int) -> str:
    return (datetime.strptime(time_str, "%I:%M %p") + timedelta(minutes=minutes)).strftime("%I:%M %p")


def _session_config(start: str, live_quiz_suite: str) -> str:
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
                "assessmentSuiteUid": live_quiz_suite,
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


def _make_suite(db, *, course_name: str, exam_title: str, assessment_type: str, now: datetime) -> AssessmentSuite:
    suite = AssessmentSuite(
        courseName=course_name,
        examTitle=exam_title,
        assessment_type=assessment_type,
        noOfQuestion=3,
        testTime="2",
        status="Approved",
        updatedBy="create_sanjay_2trainings_3q2min",
        updationOn=now,
        timestamp=now,
    )
    db.add(suite)
    db.flush()  # assigns assessmentSuiteUid via the before_insert hook
    return suite


def _add_questions(db, suite_uid: str, questions: list[dict], now: datetime) -> None:
    for i, q in enumerate(questions, start=1):
        db.add(
            Question(
                assessmentSuiteUid=suite_uid,
                question=q["question"],
                question_type="multiple_choice",
                sort_order=i,
                options=json.dumps(q["options"]),
                correct_answer=q.get("correct_answer"),
                points=q.get("points", 0),
                descriptions=q.get("descriptions"),
                status="Approved",
                updatedBy="create_sanjay_2trainings_3q2min",
                updationOn=now,
                timestamp=now,
            )
        )


STANDARD_TEST_QUESTIONS = [
    {
        "question": "What is the standard battery capacity of the Galaxy Buds charging case?",
        "options": [{"id": "A", "text": "270mAh"}, {"id": "B", "text": "500mAh"}, {"id": "C", "text": "1200mAh"}, {"id": "D", "text": "2000mAh"}],
        "correct_answer": "A",
        "points": 10,
        "descriptions": "The Galaxy Buds charging case ships with a 270mAh battery.",
    },
    {
        "question": "Which feature lets Galaxy Buds automatically switch between two connected devices?",
        "options": [{"id": "A", "text": "Auto Switch"}, {"id": "B", "text": "Dual Audio"}, {"id": "C", "text": "SmartThings Find"}, {"id": "D", "text": "Voice Detect"}],
        "correct_answer": "A",
        "points": 10,
        "descriptions": "Auto Switch hands the audio connection off between paired Galaxy devices.",
    },
    {
        "question": "What does Active Noise Cancellation (ANC) primarily reduce?",
        "options": [{"id": "A", "text": "Bluetooth latency"}, {"id": "B", "text": "Ambient background noise"}, {"id": "C", "text": "Battery drain"}, {"id": "D", "text": "Touch-control sensitivity"}],
        "correct_answer": "B",
        "points": 10,
        "descriptions": "ANC uses microphones to cancel out ambient background noise.",
    },
]

LIVE_QUIZ_QUESTIONS = [
    {
        "question": "Which app is used to locate misplaced Galaxy Buds?",
        "options": [{"id": "A", "text": "SmartThings Find"}, {"id": "B", "text": "Galaxy Wearable"}, {"id": "C", "text": "Samsung Members"}, {"id": "D", "text": "Bixby"}],
        "correct_answer": "A",
        "points": 10,
        "descriptions": "SmartThings Find tracks the last-known location of paired Galaxy accessories.",
    },
    {
        "question": "What water-resistance rating do current Galaxy Buds typically carry?",
        "options": [{"id": "A", "text": "IP68"}, {"id": "B", "text": "IPX7"}, {"id": "C", "text": "IP54"}, {"id": "D", "text": "No rating"}],
        "correct_answer": "B",
        "points": 10,
        "descriptions": "Current-generation Galaxy Buds are typically rated IPX7 for water resistance.",
    },
    {
        "question": "Which gesture is commonly used to control volume on Galaxy Buds?",
        "options": [{"id": "A", "text": "Double tap"}, {"id": "B", "text": "Swipe up/down on the stem"}, {"id": "C", "text": "Long press only"}, {"id": "D", "text": "Shake the case"}],
        "correct_answer": "B",
        "points": 10,
        "descriptions": "A swipe gesture along the earbud stem adjusts volume on most Galaxy Buds models.",
    },
]

SURVEY_QUESTIONS = [
    {
        "question": "How would you rate the trainer's product knowledge?",
        "options": [{"id": "A", "text": "Excellent"}, {"id": "B", "text": "Good"}, {"id": "C", "text": "Average"}, {"id": "D", "text": "Poor"}],
    },
    {
        "question": "Was the session duration adequate?",
        "options": [{"id": "A", "text": "Too long"}, {"id": "B", "text": "Just right"}, {"id": "C", "text": "Too short"}],
    },
    {
        "question": "Would you recommend this training to a colleague?",
        "options": [{"id": "A", "text": "Definitely"}, {"id": "B", "text": "Maybe"}, {"id": "C", "text": "No"}],
    },
]


def main() -> None:
    db = SessionLocal()
    now = datetime.now()
    try:
        standard_test_suite = _make_suite(
            db, course_name="Galaxy Buds & Wearables", exam_title="Standard Test", assessment_type="POST TEST", now=now
        )
        _add_questions(db, standard_test_suite.assessmentSuiteUid, STANDARD_TEST_QUESTIONS, now)

        live_quiz_suite = _make_suite(
            db, course_name="Galaxy Buds & Wearables", exam_title="Live Quiz", assessment_type="Quiz", now=now
        )
        _add_questions(db, live_quiz_suite.assessmentSuiteUid, LIVE_QUIZ_QUESTIONS, now)

        survey_suite = _make_suite(
            db, course_name="Galaxy Buds & Wearables", exam_title="Session Feedback Survey", assessment_type="Survey", now=now
        )
        _add_questions(db, survey_suite.assessmentSuiteUid, SURVEY_QUESTIONS, now)

        db.flush()

        created = []
        for title in TITLES:
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
                suiteTitle=title,
                state="Uttar Pradesh",
                district="Noida",
                # Geofencing OFF: no venue coordinates + geoFencing:false in the
                # session config - either one alone disables geofence_enabled().
                venueUid=None,
                geoLatitude=None,
                geoLongitude=None,
                assessmentFor="Post Training",
                postAssessmentUid=standard_test_suite.assessmentSuiteUid,
                surveyUid=survey_suite.assessmentSuiteUid,
                noOfQuestion="3",
                sessionConfig=_session_config(START, live_quiz_suite.assessmentSuiteUid),
                updatedBy="create_sanjay_2trainings_3q2min",
                updationOn=now,
                status="Approved",
                auditStatus="Approved",
                timestamp=now,
            )
            db.add(conf)
            created.append(conf)

        db.commit()
        for conf in created:
            db.refresh(conf)
        conference_uids = [c.conferenceUid for c in created]
        suite_uids = (standard_test_suite.assessmentSuiteUid, live_quiz_suite.assessmentSuiteUid, survey_suite.assessmentSuiteUid)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Suites created (3 questions, testTime=2 each): standardTest={suite_uids[0]} liveQuiz={suite_uids[1]} survey={suite_uids[2]}")
    for uid, title in zip(conference_uids, TITLES):
        print(f"Created {uid}  {DATE} {START}  {title}  for {TRAINER_NAME} ({TRAINER_ID}) - geofencing OFF")


if __name__ == "__main__":
    main()
