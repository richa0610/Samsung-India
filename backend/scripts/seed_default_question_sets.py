"""Backs every placeholder "Select Question Set" option under the POST
TEST category (see DEFAULT_QUESTION_SET_OPTIONS in add_training.tsx) with
a real assessmentsuite + a few real multiple-choice questions, using the
exact same `default:<name>` UID the frontend already generates for them.

Without this, picking one of those display-only options produces a
conference whose `postAssessmentUid` points at nothing - the module can
unlock fine, but the trainee gets a 404 loading the test. Run from backend/ with:
venv/Scripts/python.exe scripts/seed_default_question_sets.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import SessionLocal
from app.models.quiz import AssessmentSuite, Question

GENERIC_QUESTIONS = [
    {
        "question": "Which of these is a genuine Samsung Galaxy AI feature?",
        "options": [
            {"id": "A", "text": "Circle to Search"},
            {"id": "B", "text": "Deep Focus Mode"},
            {"id": "C", "text": "Turbo Render"},
            {"id": "D", "text": "Quantum Sync"},
        ],
        "correct_answer": "A",
    },
    {
        "question": "What should a SEC do first when a customer asks about trade-in value?",
        "options": [
            {"id": "A", "text": "Quote a value from memory"},
            {"id": "B", "text": "Run the device through the official trade-in evaluation tool"},
            {"id": "C", "text": "Tell them trade-ins aren't available"},
            {"id": "D", "text": "Ask them to check online themselves"},
        ],
        "correct_answer": "B",
    },
    {
        "question": "Which of these is NOT part of a proper in-store demo checklist?",
        "options": [
            {"id": "A", "text": "Confirming the demo unit is charged"},
            {"id": "B", "text": "Walking the customer through Galaxy AI features"},
            {"id": "C", "text": "Leaving the customer's personal data logged in"},
            {"id": "D", "text": "Resetting the demo unit after each customer"},
        ],
        "correct_answer": "C",
    },
]

QUESTION_SET_NAMES = [
    "S26 Review meeting",
    "Samsung Test 1",
    "Samsung Test 2",
    "MX-Training Offline Post Training For June 26",
    "Laptop Classroom/Webinar: Post Test June 26",
    "MX-Training Offline Post Test (July'26)",
    "Laptop Classroom/Webinar: Post Test July'26",
]

def question_set_uid(name: str) -> str:
    """Must stay byte-for-byte identical to `questionSetUid` in
    src/components/training/add-training/constants.ts. Length-capped because
    `assessment_results.assessmentSuiteUid` is varchar(50) in the real schema."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40].rstrip("-")
    return f"default:{slug}"


db = SessionLocal()
try:
    for name in QUESTION_SET_NAMES:
        suite_uid = question_set_uid(name)
        existing = db.query(AssessmentSuite).filter(AssessmentSuite.assessmentSuiteUid == suite_uid).first()
        if existing:
            print(f"Skipping {suite_uid!r} - already exists")
            continue

        db.add(
            AssessmentSuite(
                assessmentSuiteUid=suite_uid,
                courseName=name,
                examTitle=name,
                assessment_type="POST TEST",
                noOfQuestion=len(GENERIC_QUESTIONS),
                testTime="10",
                status="Approved",
            )
        )
        for index, q in enumerate(GENERIC_QUESTIONS, start=1):
            db.add(
                Question(
                    assessmentSuiteUid=suite_uid,
                    question=q["question"],
                    question_type="multiple_choice",
                    sort_order=index,
                    options=json.dumps(q["options"]),
                    correct_answer=q["correct_answer"],
                    points=1,
                    status="Approved",
                )
            )
        print(f"Created {suite_uid!r} with {len(GENERIC_QUESTIONS)} questions")

    db.commit()
finally:
    db.close()
