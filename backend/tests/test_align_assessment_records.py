"""scripts/align_assessment_records.py - brings saved answers and results in line with the other
system's format: option ids become option numbers (answer keys, and Standard Test / Live Quiz answers;
never Survey answers) and "Submitted" results become "Completed". It keeps an undo file, changes
nothing on a second run or in any score, and reports - never changes - what it can't tell: a number on
a question whose numeric option ids are out of order, a value that is none of the options, an answer
whose training is gone.

In-memory SQLite only."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models.conference import Conference
from app.models.quiz import Assessment, AssessmentResult, Question
from app.services import answer_numbers
from scripts import align_assessment_records as script


def options(ids):
    return json.dumps([{"id": i, "text": f"Option {i}"} for i in ids])


class AlignAssessmentRecords(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        uid = patch("app.models.uid_events.next_uid", return_value=None)
        uid.start()
        self.addCleanup(uid.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        backups = patch.object(script, "BACKUP_DIR", Path(tmp.name))
        backups.start()
        self.addCleanup(backups.stop)
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)

        self.db.add(Conference(conferenceUid="CONF-1", postAssessmentUid="SUITE-T", surveyUid="SUITE-S",
                               sessionConfig=json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-L"}})))
        self.q = {
            "test": Question(assessmentSuiteUid="SUITE-T", question="T", options=options("ABC"), correct_answer="B", points=1),
            "quiz": Question(assessmentSuiteUid="SUITE-L", question="L", options=options("ab"), correct_answer="a", points=1),
            "survey": Question(assessmentSuiteUid="SUITE-S", question="S", options=options(["very_good", "poor"]), points=1),
            "builder": Question(assessmentSuiteUid="SUITE-T", question="N", options=options("123"), correct_answer="2", points=1),
            "gapped": Question(assessmentSuiteUid="SUITE-T", question="G", options=options("134"), correct_answer="3", points=1),
        }
        self.db.add_all(self.q.values())
        self.db.flush()
        self.a = {
            "test": self.answer("SUITE-T", "test", "C"),
            "test_right": self.answer("SUITE-T", "test", "B"),
            "quiz": self.answer("SUITE-L", "quiz", "b"),
            "survey": self.answer("SUITE-S", "survey", "poor"),
            "builder": self.answer("SUITE-T", "builder", "3"),
            "numbered": self.answer("SUITE-T", "test", "2"),       # saved by the numbering backend
            "unknown": self.answer("SUITE-T", "test", "Z"),
            "gapped": self.answer("SUITE-T", "gapped", "4"),
            "gone": self.answer("SUITE-T", "test", "A", conference="CONF-GONE"),
        }
        self.r = {status: self.result(status) for status in ("Submitted", "Completed", "Started")}
        self.db.commit()

    def answer(self, suite, question, value, conference="CONF-1"):
        row = Assessment(conferenceUid=conference, traineeUid="TRN1", assessmentSuiteUid=suite,
                         questionId=str(self.q[question].id), selectedOption=value)
        self.db.add(row)
        self.db.flush()
        return row

    def result(self, status):
        row = AssessmentResult(conferenceUid="CONF-1", traineeUid=f"TRN-{status}", assessmentSuiteUid="SUITE-T", status=status)
        self.db.add(row)
        self.db.flush()
        return row

    def values(self):
        self.db.expire_all()
        return (
            {key: q.correct_answer for key, q in self.q.items()},
            {key: a.selectedOption for key, a in self.a.items()},
            {key: r.status for key, r in self.r.items()},
        )

    def correctness(self):
        self.db.expire_all()
        return {key: answer_numbers.is_correct(self.db.get(Question, int(a.questionId)), a.selectedOption)
                for key, a in self.a.items() if key not in ("survey", "gone")}

    def test_the_preview_plans_only_option_ids_and_submitted_results_and_writes_nothing(self):
        before = self.values()
        plan = script.make_plan(self.db)
        self.assertEqual(
            {(c.table, c.row_id, c.old, c.new) for c in plan.changes},
            {("questions", self.q["test"].id, "B", "2"), ("questions", self.q["quiz"].id, "a", "1"),
             ("assessment", self.a["test"].id, "C", "3"), ("assessment", self.a["test_right"].id, "B", "2"),
             ("assessment", self.a["quiz"].id, "b", "2"),
             ("assessment_results", self.r["Submitted"].id, "Submitted", "Completed")},
        )
        self.assertEqual(plan.left, {"survey answer": 1, "already a number": 3, "empty": 1})
        self.assertEqual(len(plan.problems), 4)  # gapped answer key + answer, unknown option, training gone
        self.assertEqual(self.values(), before)

    def test_apply_changes_them_and_keeps_an_undo_file(self):
        done, backup = script.apply(self.db, script.make_plan(self.db), "samsung")
        self.assertEqual(done, 6)
        keys, answers, results = self.values()
        self.assertEqual((keys["test"], keys["quiz"], keys["survey"], keys["builder"], keys["gapped"]), ("2", "1", None, "2", "3"))
        self.assertEqual({k: answers[k] for k in ("test", "test_right", "quiz", "survey", "unknown", "gapped")},
                         {"test": "3", "test_right": "2", "quiz": "2", "survey": "poor", "unknown": "Z", "gapped": "4"})
        self.assertEqual(results, {"Submitted": "Completed", "Completed": "Completed", "Started": "Started"})
        self.assertEqual(len(json.loads(backup.read_text(encoding="utf-8"))["changes"]), 6)

    def test_a_second_run_changes_nothing(self):
        script.apply(self.db, script.make_plan(self.db), "samsung")
        self.assertEqual(script.make_plan(self.db).changes, [])

    def test_no_answer_changes_from_right_to_wrong_or_back(self):
        before = self.correctness()
        script.apply(self.db, script.make_plan(self.db), "samsung")
        self.assertEqual(self.correctness(), before)

    def test_undo_puts_back_exactly_its_values_and_leaves_rows_changed_since(self):
        before = self.values()
        _, backup = script.apply(self.db, script.make_plan(self.db), "samsung")
        self.db.query(Assessment).filter(Assessment.id == self.a["test"].id).update({"selectedOption": "1"})
        self.db.commit()
        self.assertEqual(script.undo(self.db, backup, "samsung"), (5, 1))
        keys, answers, results = self.values()
        self.assertEqual((keys, results), (before[0], before[2]))
        self.assertEqual(answers, {**before[1], "test": "1"})

    def test_undo_refuses_another_tenants_file(self):
        _, backup = script.apply(self.db, script.make_plan(self.db), "samsung")
        with self.assertRaises(SystemExit):
            script.undo(self.db, backup, "demo")
