"""scripts/migrate_suite_uids.py on a synthetic in-memory database (never a real one).

Every question set ends up with an ASM<YY><5 digits> ID: the ones already in that format keep
theirs, the rest continue after the highest number in use, in creation order. Every link -
questions, answers, scores, a training's Pre-Test / Standard Test / Survey, and the
"assessmentSuiteUid"s inside its sessionConfig JSON (the Live Quiz's only link) - follows. The ASM
counter moves past them. A dry run writes nothing; a second run finds nothing to do; a rollback
puts every old ID back; a plan that would leave a link pointing nowhere writes nothing at all."""

import json
import unittest

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models import *  # noqa: F401,F403 - registers every table
from scripts import migrate_suite_uids as migration
from scripts.migrate_suite_uids import Rename

DEFAULT_SET = "default:S26 Review meeting"
QUIZ_SET = "quiz-galaxy-ai-flagship"
DEMO_SET = "posttest-galaxy-s26-demo"
LIVE_CONFIG = {
    "attendance": {"geoFencing": True, "checkInOpens": "09:00 AM"},
    "standardTest": {"category": "POST TEST", "assessmentSuiteUid": DEFAULT_SET},
    "liveQuiz": {"assessmentSuiteUid": QUIZ_SET, "startTime": "10:00 AM", "unlockCondition": "Manual"},
}


def asm(sequence: int) -> str:
    return migration.new_suite_id(sequence)


class SuiteUidMigrationTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(self.engine)
        self.addCleanup(self.engine.dispose)
        with self.engine.begin() as conn:
            for row_id, uid in enumerate([DEFAULT_SET, "ASM2610001", QUIZ_SET, "ASM2610002", DEMO_SET], start=1):
                conn.execute(text("INSERT INTO assessmentsuite (id, assessmentSuiteUid, status) VALUES (:i, :u, 'Approved')"),
                             {"i": row_id, "u": uid})
                conn.execute(text("INSERT INTO questions (assessmentSuiteUid, question) VALUES (:u, 'Q')"), {"u": uid})
            conn.execute(text("INSERT INTO uid_sequence (prefix, next_val) VALUES ('ASM', 10003)"))
            for uid in (DEFAULT_SET, QUIZ_SET):
                conn.execute(text("INSERT INTO assessment (assessmentSuiteUid, conferenceUid, traineeUid, questionId) "
                                  "VALUES (:u, 'CONF-A', 'TRN1', '1')"), {"u": uid})
            for uid in (DEFAULT_SET, "ASM2610001"):
                conn.execute(text("INSERT INTO assessment_results (assessmentSuiteUid, conferenceUid, traineeUid, status) "
                                  "VALUES (:u, 'CONF-A', 'TRN1', 'Submitted')"), {"u": uid})
            self.add_conference(conn, "CONF-A", post=DEFAULT_SET, survey="ASM2610002", config=json.dumps(LIVE_CONFIG))
            self.add_conference(conn, "CONF-B", pre=DEMO_SET, config="not json {")
            self.add_conference(conn, "CONF-C", post="a-set-deleted-long-ago")    # already broken before

    @staticmethod
    def add_conference(conn, uid, *, pre=None, post=None, survey=None, config=None):
        conn.execute(
            text("INSERT INTO conference (conferenceUid, preAssessmentUid, postAssessmentUid, surveyUid, sessionConfig) "
                 "VALUES (:c, :pre, :post, :survey, :config)"),
            {"c": uid, "pre": pre, "post": post, "survey": survey, "config": config},
        )

    def scalar(self, sql, **params):
        with self.engine.connect() as conn:
            return conn.execute(text(sql), params).scalar()

    def column(self, sql):
        with self.engine.connect() as conn:
            return [row[0] for row in conn.execute(text(sql))]

    def snapshot(self):
        return {
            "suites": self.column("SELECT assessmentSuiteUid FROM assessmentsuite ORDER BY id"),
            "questions": self.column("SELECT assessmentSuiteUid FROM questions ORDER BY id"),
            "answers": self.column("SELECT assessmentSuiteUid FROM assessment ORDER BY id"),
            "results": self.column("SELECT assessmentSuiteUid FROM assessment_results ORDER BY id"),
            # COALESCE: in SQL a NULL in a || chain empties the whole value.
            "trainings": self.column(
                "SELECT COALESCE(preAssessmentUid, '-') || '|' || COALESCE(postAssessmentUid, '-') || '|' || "
                "COALESCE(surveyUid, '-') FROM conference ORDER BY id"
            ),
            "configs": [json.loads(c) if c and c.startswith("{") else c
                        for c in self.column("SELECT sessionConfig FROM conference ORDER BY id")],
            "counter": self.scalar("SELECT next_val FROM uid_sequence WHERE prefix = 'ASM'"),
        }

    def plan(self):
        with self.engine.connect() as conn:
            return migration.plan(conn)

    def apply(self, renames=None):
        with self.engine.begin() as conn:
            migration.apply(conn, renames if renames is not None else migration.plan(conn))


class ThePlan(SuiteUidMigrationTestCase):
    def test_asm_ids_stay_and_the_rest_follow_the_highest_in_creation_order(self):
        self.assertEqual(
            self.plan(),
            [Rename(1, DEFAULT_SET, asm(10003)), Rename(3, QUIZ_SET, asm(10004)), Rename(5, DEMO_SET, asm(10005))],
        )

    def test_numbering_also_respects_the_counter(self):
        with self.engine.begin() as conn:
            conn.execute(text("UPDATE uid_sequence SET next_val = 10050 WHERE prefix = 'ASM'"))
        self.assertEqual(self.plan()[0].new, asm(10050))

    def test_a_question_set_with_no_id_gets_one(self):
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO assessmentsuite (id, assessmentSuiteUid, status) VALUES (6, NULL, 'Approved')"))
        self.assertEqual(self.plan()[-1], Rename(6, None, asm(10006)))

    def test_it_counts_every_link_it_will_touch(self):
        with self.engine.connect() as conn:
            counts = migration.reference_counts(conn, [DEFAULT_SET, QUIZ_SET, DEMO_SET])
        # DEFAULT_SET: question, answer, result, CONF-A's post test, CONF-A's config. QUIZ_SET: question,
        # answer, CONF-A's Live Quiz in its config. DEMO_SET: question, CONF-B's pre-test.
        self.assertEqual(counts, {DEFAULT_SET: 5, QUIZ_SET: 3, DEMO_SET: 2})

    def test_planning_writes_nothing(self):
        before = self.snapshot()
        self.plan()
        self.assertEqual(self.snapshot(), before)


class Applying(SuiteUidMigrationTestCase):
    def test_every_question_set_ends_up_with_an_asm_id(self):
        self.apply()
        self.assertEqual(self.column("SELECT assessmentSuiteUid FROM assessmentsuite ORDER BY id"),
                         [asm(10003), "ASM2610001", asm(10004), "ASM2610002", asm(10005)])

    def test_every_link_follows(self):
        self.apply()
        self.assertEqual(self.column("SELECT assessmentSuiteUid FROM questions ORDER BY id"),
                         [asm(10003), "ASM2610001", asm(10004), "ASM2610002", asm(10005)])
        self.assertEqual(self.column("SELECT assessmentSuiteUid FROM assessment ORDER BY id"), [asm(10003), asm(10004)])
        self.assertEqual(self.column("SELECT assessmentSuiteUid FROM assessment_results ORDER BY id"),
                         [asm(10003), "ASM2610001"])
        self.assertEqual(self.scalar("SELECT postAssessmentUid FROM conference WHERE conferenceUid = 'CONF-A'"), asm(10003))
        self.assertEqual(self.scalar("SELECT surveyUid FROM conference WHERE conferenceUid = 'CONF-A'"), "ASM2610002")
        self.assertEqual(self.scalar("SELECT preAssessmentUid FROM conference WHERE conferenceUid = 'CONF-B'"), asm(10005))

    def test_the_live_quiz_link_inside_the_training_config_follows_and_nothing_else_changes(self):
        self.apply()
        config = json.loads(self.scalar("SELECT sessionConfig FROM conference WHERE conferenceUid = 'CONF-A'"))
        expected = json.loads(json.dumps(LIVE_CONFIG))
        expected["standardTest"]["assessmentSuiteUid"] = asm(10003)
        expected["liveQuiz"]["assessmentSuiteUid"] = asm(10004)
        self.assertEqual(config, expected)

    def test_unreadable_configs_and_already_broken_links_are_left_alone(self):
        self.apply()
        self.assertEqual(self.scalar("SELECT sessionConfig FROM conference WHERE conferenceUid = 'CONF-B'"), "not json {")
        self.assertEqual(self.scalar("SELECT postAssessmentUid FROM conference WHERE conferenceUid = 'CONF-C'"),
                         "a-set-deleted-long-ago")

    def test_the_counter_moves_past_the_new_ids(self):
        self.apply()
        self.assertEqual(self.scalar("SELECT next_val FROM uid_sequence WHERE prefix = 'ASM'"), 10006)

    def test_without_a_counter_row_one_is_added(self):
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM uid_sequence"))
        self.apply()
        self.assertEqual(self.scalar("SELECT next_val FROM uid_sequence WHERE prefix = 'ASM'"), 10006)

    def test_a_second_run_finds_nothing_to_do(self):
        self.apply()
        self.assertEqual(self.plan(), [])


class Safety(SuiteUidMigrationTestCase):
    def test_a_plan_that_would_break_a_link_writes_nothing(self):
        before = self.snapshot()
        # A stale plan: the row's ID changed since it was made, so its links wouldn't follow.
        stale = [Rename(1, "default:Some other name", asm(10003))]
        with self.assertRaises(RuntimeError):
            self.apply(stale)
        self.assertEqual(self.snapshot(), before)

    def test_rollback_puts_every_old_id_back(self):
        before = self.snapshot()
        renames = self.plan()
        self.apply(renames)
        self.assertNotEqual(self.snapshot()["trainings"], before["trainings"])  # the snapshot does see them
        with self.engine.begin() as conn:
            migration.rollback(conn, renames)
        # Everything as it was - except the counter, which stays past the numbers used.
        self.assertEqual({**self.snapshot(), "counter": None}, {**before, "counter": None})
        self.assertEqual(self.snapshot()["counter"], 10006)


if __name__ == "__main__":
    unittest.main()
