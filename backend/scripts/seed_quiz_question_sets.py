"""Seed 3 comprehensive Question Sets for the Quiz module (Live Quiz / FFF).

Each set contains 5 realistic, high-quality multiple-choice questions
tailored for Samsung India sales, product knowledge, and SEC training:
1. Galaxy AI & Flagship Series Quiz (S26 / S25 series features)
2. Galaxy Connected Ecosystem Quiz (Watch, Buds, SmartThings, Quick Share)
3. SEC Retail Sales & In-Store Demo Quiz (Sales journey, demo checklist, trade-in, Care+)

Run from backend/ with:
    python scripts/seed_quiz_question_sets.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401
from app.database.connection import SessionLocal
from app.models.quiz import AssessmentSuite, Question

QUESTION_SETS = [
    {
        "suiteUid": "quiz-galaxy-ai-flagship",
        "title": "Galaxy AI & Flagship Series Quiz",
        "courseName": "Galaxy AI & Flagship Series",
        "description": "Assessment covering flagship Galaxy AI capabilities, camera enhancements, and core device hardware.",
        "category": "Quiz",
        "testTime": "5",
        "questions": [
            {
                "question": "Which Galaxy AI feature enables users to circle any text or image on their screen to instantly initiate a Google search without switching apps?",
                "options": [
                    {"id": "A", "text": "Circle to Search"},
                    {"id": "B", "text": "Quick Share Lens"},
                    {"id": "C", "text": "AI Smart Select"},
                    {"id": "D", "text": "Instant Object Lookup"},
                ],
                "correct_answer": "A",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Circle to Search with Google lets users circle, highlight, or tap anything on the screen to search without leaving their current app.",
            },
            {
                "question": "Which feature allows real-time, two-way voice and text translations during phone calls within the native Phone app?",
                "options": [
                    {"id": "A", "text": "Interpreter Mode"},
                    {"id": "B", "text": "Live Translate"},
                    {"id": "C", "text": "Chat Assist"},
                    {"id": "D", "text": "Note Assist"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Live Translate provides real-time, on-device audio and text translation during phone calls in supported languages.",
            },
            {
                "question": "What does the Generative Edit feature in Galaxy AI's Photo Assist allow the user to do?",
                "options": [
                    {"id": "A", "text": "Increase device charging speed while editing photos"},
                    {"id": "B", "text": "Relocate, resize, or remove objects and fill in the missing background seamlessly"},
                    {"id": "C", "text": "Convert JPEG files into video format automatically"},
                    {"id": "D", "text": "Lock camera aperture physically"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 25,
                "explanation": "Generative Edit enables users to move, resize, or remove subjects in a photo, automatically generating matching background to fill empty spaces.",
            },
            {
                "question": "What is the primary display enhancement feature in the Galaxy Ultra series designed to drastically reduce glare under bright sunlight?",
                "options": [
                    {"id": "A", "text": "Corning Gorilla Armor with anti-reflective treatment"},
                    {"id": "B", "text": "Polarized Plastic Coating"},
                    {"id": "C", "text": "Liquid Crystal Dimming"},
                    {"id": "D", "text": "Mirror Finish Glass"},
                ],
                "correct_answer": "A",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Corning Gorilla Armor on the Ultra reduces ambient reflections by up to 75% for superior outdoor readability.",
            },
            {
                "question": "Which Galaxy AI feature in Samsung Notes automatically summarizes, formats, and spell-checks lengthy meeting notes?",
                "options": [
                    {"id": "A", "text": "Audio Eraser"},
                    {"id": "B", "text": "Note Assist"},
                    {"id": "C", "text": "Transcribe View"},
                    {"id": "D", "text": "Smart Summary Card"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Note Assist formats notes with bullet points, generates concise summaries, and translates handwritten or typed notes.",
            },
        ],
    },
    {
        "suiteUid": "quiz-galaxy-ecosystem",
        "title": "Galaxy Connected Ecosystem Quiz",
        "courseName": "Galaxy Connected Ecosystem",
        "description": "Test understanding of connected experience across Galaxy Watch, Buds, SmartThings, and Galaxy Book.",
        "category": "Quiz",
        "testTime": "5",
        "questions": [
            {
                "question": "Which Samsung ecosystem capability enables Galaxy Buds to automatically switch playback from a Galaxy Tab to a Galaxy phone when an incoming call arrives?",
                "options": [
                    {"id": "A", "text": "Dual Audio Broadcast"},
                    {"id": "B", "text": "Auto Switch"},
                    {"id": "C", "text": "Bluetooth Multipoint Sync"},
                    {"id": "D", "text": "Quick Pair Share"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Auto Switch automatically shifts audio from a Galaxy tablet or PC to the Galaxy smartphone when receiving a phone call.",
            },
            {
                "question": "Which service allows users to locate offline Samsung Galaxy devices, including Watch, Buds, and SmartTag?",
                "options": [
                    {"id": "A", "text": "Samsung Care+"},
                    {"id": "B", "text": "SmartThings Find"},
                    {"id": "C", "text": "Device Care Manager"},
                    {"id": "D", "text": "Samsung Members Beacon"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "SmartThings Find uses the SmartThings Find Network of nearby Galaxy devices to locate lost Galaxy devices even when offline.",
            },
            {
                "question": "What advanced 3-in-1 sensor powers the health and fitness tracking on the Galaxy Watch series?",
                "options": [
                    {"id": "A", "text": "BioActive Sensor"},
                    {"id": "B", "text": "Tri-Health Optical Chip"},
                    {"id": "C", "text": "BioMetric Pulse Array"},
                    {"id": "D", "text": "CardioSync Sensor"},
                ],
                "correct_answer": "A",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "The Samsung BioActive Sensor combines Optical Heart Rate, Electrical Heart Signal (ECG), and Bioelectrical Impedance Analysis (BIA).",
            },
            {
                "question": "What feature allows users to seamlessly share large files, photos, and documents between Samsung devices with zero compression?",
                "options": [
                    {"id": "A", "text": "Nearby Direct"},
                    {"id": "B", "text": "Quick Share"},
                    {"id": "C", "text": "Wi-Fi Beam"},
                    {"id": "D", "text": "Samsung Cloud Cast"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Quick Share allows fast, secure, uncompressed local file transfers between Galaxy smartphones, tablets, and Galaxy Books.",
            },
            {
                "question": "Which feature lets you control a Galaxy tablet using the keyboard and mouse of a connected Galaxy Book laptop?",
                "options": [
                    {"id": "A", "text": "Second Screen"},
                    {"id": "B", "text": "Multi Control"},
                    {"id": "C", "text": "Link to Windows"},
                    {"id": "D", "text": "Smart View Mirror"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 25,
                "explanation": "Multi Control allows users to control their Galaxy smartphone or tablet using their Galaxy Book keyboard and trackpad, drag-and-dropping content across screens.",
            },
        ],
    },
    {
        "suiteUid": "quiz-sec-retail-excellence",
        "title": "SEC Retail Sales & In-Store Demo Quiz",
        "courseName": "SEC Retail Sales Excellence",
        "description": "Assess SEC customer handling, consultative selling, demo checklist compliance, and warranty pitches.",
        "category": "Quiz",
        "testTime": "5",
        "questions": [
            {
                "question": "When a customer walks into the Samsung Experience Store showing interest in an upgrade, what should the SEC do first?",
                "options": [
                    {"id": "A", "text": "Immediately push the highest-priced flagship model"},
                    {"id": "B", "text": "Greet warmly, ask open-ended discovery questions, and understand their current device usage"},
                    {"id": "C", "text": "Hand them a product brochure and wait until they call you"},
                    {"id": "D", "text": "Tell them to compare prices on e-commerce websites"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Greeting warmly and conducting needs discovery helps tailor the right Galaxy device and features to the customer's lifestyle.",
            },
            {
                "question": "What is the mandatory step an SEC must take before letting a customer test a demo device?",
                "options": [
                    {"id": "A", "text": "Ensure the demo device is clean, fully charged, in Retail Mode, and ready for hands-on experience"},
                    {"id": "B", "text": "Turn off all Wi-Fi connections to save data"},
                    {"id": "C", "text": "Keep the device locked inside the display case"},
                    {"id": "D", "text": "Disable the camera so customers cannot take sample photos"},
                ],
                "correct_answer": "A",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "In-store demo units must always be clean, charged, connected, and set up in Retail Mode to showcase premium features.",
            },
            {
                "question": "How should an SEC officially evaluate a customer's trade-in phone value in India?",
                "options": [
                    {"id": "A", "text": "Guess an estimate based on the phone's age"},
                    {"id": "B", "text": "Inspect physical condition and run diagnostics using the official Samsung Trade-In / SmartExchange tool"},
                    {"id": "C", "text": "Direct the customer to a third-party repair shop"},
                    {"id": "D", "text": "Refuse trade-ins unless the device has zero scratches"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 25,
                "explanation": "Accurate trade-in quotes require physical inspection and diagnostic grading through the authorized Samsung Trade-in / SmartExchange app.",
            },
            {
                "question": "What is the primary benefit to highlight when pitching Samsung Care+ to a customer purchasing a new Galaxy device?",
                "options": [
                    {"id": "A", "text": "Free ringtones for 1 year"},
                    {"id": "B", "text": "Comprehensive protection against accidental liquid and physical damage with genuine Samsung parts"},
                    {"id": "C", "text": "Double the device battery capacity"},
                    {"id": "D", "text": "Free accessories with every recharge"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 20,
                "explanation": "Samsung Care+ provides peace of mind with coverage for accidental screen damage, liquid ingress, and hardware breakdown using 100% genuine parts.",
            },
            {
                "question": "Which approach is recommended when a customer expresses price hesitation about a flagship Galaxy device?",
                "options": [
                    {"id": "A", "text": "Immediately discount your commission"},
                    {"id": "B", "text": "Highlight value propositions including trade-in bonuses, bank cashback offers, No-Cost EMI, and 7-year OS updates"},
                    {"id": "C", "text": "Tell the customer that flagship devices are not meant for budget buyers"},
                    {"id": "D", "text": "Recommend they purchase a refurbished phone elsewhere"},
                ],
                "correct_answer": "B",
                "points": 10,
                "timerSeconds": 25,
                "explanation": "Breaking down affordability through affordability tools (No-Cost EMI, upgrade bonuses, long-term software support) resolves price objections effectively.",
            },
        ],
    },
]


def seed_quiz_sets():
    db = SessionLocal()
    now = datetime.now()
    created_count = 0
    updated_count = 0

    try:
        for item in QUESTION_SETS:
            suite_uid = item["suiteUid"]
            suite = db.query(AssessmentSuite).filter(AssessmentSuite.assessmentSuiteUid == suite_uid).first()

            if not suite:
                suite = AssessmentSuite(
                    assessmentSuiteUid=suite_uid,
                    courseName=item["courseName"],
                    examTitle=item["title"],
                    description=item["description"],
                    assessment_type=item["category"],
                    settings=json.dumps({"type": "Quiz"}),
                    noOfQuestion=len(item["questions"]),
                    testTime=item["testTime"],
                    status="Approved",
                    updatedBy="seed_quiz_question_sets",
                    updationOn=now,
                    timestamp=now,
                )
                db.add(suite)
                db.flush()
                created_count += 1
                print(f"[+] Created Suite: {suite_uid} ('{item['title']}')")
            else:
                suite.courseName = item["courseName"]
                suite.examTitle = item["title"]
                suite.description = item["description"]
                suite.assessment_type = item["category"]
                suite.noOfQuestion = len(item["questions"])
                suite.testTime = item["testTime"]
                suite.status = "Approved"
                suite.updationOn = now
                updated_count += 1
                print(f"[*] Updating existing Suite: {suite_uid}")

            # Clear existing questions for idempotent re-seed
            db.query(Question).filter(Question.assessmentSuiteUid == suite_uid).delete()

            for order, q_data in enumerate(item["questions"], start=1):
                db.add(
                    Question(
                        assessmentSuiteUid=suite_uid,
                        question=q_data["question"],
                        question_type="multiple_choice",
                        sort_order=order,
                        options=json.dumps(q_data["options"]),
                        correct_answer=q_data["correct_answer"],
                        points=q_data["points"],
                        descriptions=q_data.get("explanation"),
                        settings=json.dumps({
                            "timerSeconds": q_data.get("timerSeconds", 20),
                            "explanation": q_data.get("explanation", ""),
                        }),
                        status="Approved",
                        updatedBy="seed_quiz_question_sets",
                        updationOn=now,
                        timestamp=now,
                    )
                )

        db.commit()
        print(f"\nDone! Created: {created_count}, Updated: {updated_count}. Total Question Sets seeded: {len(QUESTION_SETS)}")
    except Exception as e:
        db.rollback()
        print(f"Error seeding question sets: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_quiz_sets()
