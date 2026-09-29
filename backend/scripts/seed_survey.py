"""One-off script to seed a real "Survey" assessment suite with a handful
of Likert-scale + free-text questions, so the trainer's session-flow
builder has at least one genuine, working Survey question set to pick for
the Survey module (mirrors seed_post_test.py, using the same
assessmentsuite/questions tables - there's no separate survey table).

Run from backend/ with: venv/Scripts/python.exe scripts/seed_survey.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import SessionLocal
from app.models.quiz import AssessmentSuite, Question

SUITE_UID = "survey-june-classroom-feedback-demo"

LIKERT_OPTIONS = [
    {"id": "very_effective", "text": "Very Effective"},
    {"id": "effective", "text": "Effective"},
    {"id": "neutral", "text": "Neutral"},
    {"id": "ineffective", "text": "Ineffective"},
    {"id": "very_ineffective", "text": "Very Ineffective"},
]

QUESTIONS = [
    {"question": "How would you rate the June Activity-led classroom training session?", "question_type": "multiple_choice", "options": LIKERT_OPTIONS},
    {"question": "How effective was the AICO approach for pitch practice?", "question_type": "multiple_choice", "options": LIKERT_OPTIONS},
    {"question": "How effective was the trainer's product knowledge delivery?", "question_type": "multiple_choice", "options": LIKERT_OPTIONS},
    {"question": "How effective was the Samsung Delight activity for customer competition?", "question_type": "multiple_choice", "options": LIKERT_OPTIONS},
    {"question": "How effective was the activity-led training session compared to a regular training session?", "question_type": "multiple_choice", "options": LIKERT_OPTIONS},
    {"question": "How effective was the pace and structure of the session?", "question_type": "multiple_choice", "options": LIKERT_OPTIONS},
    {"question": "What do you feel could be improved about this session?", "question_type": "short_answer", "options": []},
    {"question": "Additional Comments", "question_type": "paragraph", "options": []},
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
                courseName="SECs Feedback",
                examTitle="SECs Feedback | June Classroom Training Sessions",
                assessment_type="Survey",
                settings=json.dumps({"type": "Survey"}),
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
                    question_type=q["question_type"],
                    sort_order=index,
                    options=json.dumps(q["options"]),
                    correct_answer=None,
                    points=0,
                    status="Approved",
                )
            )
        db.commit()
        print(f"Created suite {SUITE_UID!r} with {len(QUESTIONS)} questions")
finally:
    db.close()
