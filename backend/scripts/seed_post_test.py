"""One-off script to seed a real "POST TEST" assessment suite with a
handful of multiple-choice questions, so the trainer's session-flow
builder has at least one genuine, working Post Test question set to pick
(the "POST TEST" category option previously only existed as a display
label with nothing behind it - see add_training.tsx's
DEFAULT_CATEGORY_OPTIONS / DEFAULT_QUESTION_SET_OPTIONS).

Run from backend/ with: venv/Scripts/python.exe scripts/seed_post_test.py
"""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import SessionLocal
from app.models.quiz import AssessmentSuite, Question

SUITE_UID = "posttest-galaxy-s26-demo"

QUESTIONS = [
    {
        "question": "What is the display size of the Galaxy S26 Ultra?",
        "options": [
            {"id": "A", "text": "6.1-inch"},
            {"id": "B", "text": "6.3-inch"},
            {"id": "C", "text": "6.9-inch"},
            {"id": "D", "text": "7.2-inch"},
        ],
        "correct_answer": "C",
    },
    {
        "question": "Which processor powers the Galaxy S26 series?",
        "options": [
            {"id": "A", "text": "Exynos 2600"},
            {"id": "B", "text": "Snapdragon 8 Gen 2"},
            {"id": "C", "text": "MediaTek Dimensity 9000"},
            {"id": "D", "text": "Exynos 2200"},
        ],
        "correct_answer": "A",
    },
    {
        "question": "Which Galaxy AI feature lets a customer edit a photo right after taking it?",
        "options": [
            {"id": "A", "text": "Live Translate"},
            {"id": "B", "text": "Now Brief"},
            {"id": "C", "text": "Photo Assist"},
            {"id": "D", "text": "Samsung Wallet"},
        ],
        "correct_answer": "C",
    },
    {
        "question": "What is the standard warranty period for a Galaxy S26 in India?",
        "options": [
            {"id": "A", "text": "6 months"},
            {"id": "B", "text": "1 year"},
            {"id": "C", "text": "18 months"},
            {"id": "D", "text": "2 years"},
        ],
        "correct_answer": "B",
    },
    {
        "question": "Which of these is NOT a genuine Galaxy S26 accessory?",
        "options": [
            {"id": "A", "text": "25W Super Fast Charger"},
            {"id": "B", "text": "Galaxy Buds"},
            {"id": "C", "text": "S Pen Case"},
            {"id": "D", "text": "Universal USB-A Charger"},
        ],
        "correct_answer": "D",
    },
]

db = SessionLocal()
try:
    existing_suite = db.query(AssessmentSuite).filter(AssessmentSuite.assessmentSuiteUid == SUITE_UID).first()
    if existing_suite:
        print(f"Skipping suite {SUITE_UID!r} - already exists")
    else:
        db.add(
            AssessmentSuite(
                assessmentSuiteUid=SUITE_UID,
                courseName="Galaxy S26 Product Knowledge",
                examTitle="Galaxy S26 Post Training Test",
                assessment_type="POST TEST",
                noOfQuestion=len(QUESTIONS),
                testTime="10",
                status="Approved",
            )
        )
        for index, q in enumerate(QUESTIONS, start=1):
            db.add(
                Question(
                    assessmentSuiteUid=SUITE_UID,
                    question=q["question"],
                    question_type="multiple_choice",
                    sort_order=index,
                    options=json.dumps(q["options"]),
                    correct_answer=q["correct_answer"],
                    points=1,
                    status="Approved",
                )
            )
        db.commit()
        print(f"Created suite {SUITE_UID!r} with {len(QUESTIONS)} questions")
finally:
    db.close()
