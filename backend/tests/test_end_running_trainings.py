"""scripts/end_running_trainings.py on a synthetic in-memory database (never a real one).

It lists trainings left "Ongoing" / "Live" (or "Started"), and ends exactly the ones named - and only
while they are still running: the live module is stopped (a Live Quiz scored first), the training is
stored ended the other system's way ("Session Completed", no module, quiz CLOSED - user 2026-10-17)
with its end time, the Execution Flow and activity log say it was an admin data fix."""

import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.models.logs_master import LogsMaster
from app.models.quiz import AssessmentResult, Question
from scripts import end_running_trainings as script


class EndRunningTrainingsTestCase(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        # The sequential-ID hook speaks MySQL; these synthetic rows don't need its IDs.
        uid_patch = patch("app.models.uid_events.next_uid", return_value=None)
        uid_patch.start()
        self.addCleanup(uid_patch.stop)
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)

        quiz = Question(assessmentSuiteUid="SUITE-Q", question="Q1", options="[]", correct_answer="a", points=1)
        self.db.add(quiz)
        self.db.add_all([
            Conference(conferenceUid="CONF-QUIZ", conferenceStatus="Ongoing", activeModuleId="LIVE_QUIZ",
                       liveQuizState="QUESTION_LIVE", sessionConfig=json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-Q"}}),
                       conferenceDate="2026-10-01", trainerEmployeeId="trainer1"),
            Conference(conferenceUid="CONF-IDLE", conferenceStatus="ongoing", conferenceDate="2026-09-20"),
            Conference(conferenceUid="CONF-STUCK", conferenceStatus="Ongoing", conferenceEndsOn="2026-09-15 06:00:00"),
            Conference(conferenceUid="CONF-OTHER", conferenceStatus="Live"),
            Conference(conferenceUid="CONF-DONE", conferenceStatus="Completed"),
            Conference(conferenceUid="CONF-LATER", conferenceStatus="Scheduled"),
            Attendance(conferenceUid="CONF-QUIZ", traineeUid="TRN1", status="Present"),
        ])
        self.db.commit()
        from app.models.quiz import Assessment
        self.db.add(Assessment(conferenceUid="CONF-QUIZ", traineeUid="TRN1", assessmentSuiteUid="SUITE-Q",
                               questionId=str(quiz.id), selectedOption="a", remarks="4000"))
        self.db.commit()

    def conference(self, uid) -> Conference:
        self.db.expire_all()
        return self.db.query(Conference).filter_by(conferenceUid=uid).one()

    def flow(self, uid) -> list[tuple]:
        rows = self.db.query(ConferenceActivityLog).filter_by(conferenceUid=uid).order_by(ConferenceActivityLog.id).all()
        return [(r.moduleId, r.action, r.performedBy, r.locationRemark) for r in rows]


class Listing(EndRunningTrainingsTestCase):
    def test_it_lists_every_running_training_in_any_letter_case(self):
        self.assertEqual([c.conferenceUid for c in script.running(self.db)], ["CONF-QUIZ", "CONF-IDLE", "CONF-STUCK", "CONF-OTHER"])

    def test_the_list_says_enough_to_tell_a_forgotten_training_apart(self):
        described = script.describe(self.db, self.conference("CONF-QUIZ"))
        self.assertEqual((described["activeModule"], described["participants"], described["trainer"]), ("LIVE_QUIZ", 1, "trainer1"))

    def test_listing_writes_nothing(self):
        script.running(self.db)
        self.assertEqual(self.conference("CONF-QUIZ").conferenceStatus, "Ongoing")
        self.assertEqual(self.db.query(ConferenceActivityLog).count(), 0)


class Ending(EndRunningTrainingsTestCase):
    def test_a_live_quiz_is_scored_then_the_training_completed(self):
        before, skipped = script.end_named(self.db, ["CONF-QUIZ"])
        conference = self.conference("CONF-QUIZ")
        self.assertEqual((conference.conferenceStatus, conference.activeModuleId, conference.liveQuizState),
                         ("Session Completed", "", "CLOSED"))
        self.assertIsNone(conference.conferenceEndsOn)                   # its planned last day - not an end time
        self.assertIsNotNone(conference.actualEndedAt)
        result = self.db.query(AssessmentResult).filter_by(conferenceUid="CONF-QUIZ", traineeUid="TRN1").one()
        self.assertEqual((result.status, float(result.totalScore)), ("Completed", 1))
        self.assertEqual(self.flow("CONF-QUIZ"), [                         # the other system's log format
            ("Quiz_SUITE-Q", "STOPPED", script.PERFORMED_BY, None),
            ("", "STOPPED", script.PERFORMED_BY, None),
        ])
        self.assertEqual(before, [{"conferenceUid": "CONF-QUIZ", "conferenceStatus": "Ongoing", "conferenceEndsOn": None,
                                   "actualEndedAt": None, "activeModuleId": "LIVE_QUIZ", "liveQuizState": "QUESTION_LIVE"}])
        self.assertEqual(skipped, [])

    def test_a_training_with_nothing_live_just_ends(self):
        script.end_named(self.db, ["CONF-IDLE"])
        self.assertEqual(self.conference("CONF-IDLE").conferenceStatus, "Session Completed")
        self.assertEqual(self.flow("CONF-IDLE"), [("", "STOPPED", script.PERFORMED_BY, None)])

    def test_one_already_stamped_as_ended_keeps_its_end_time(self):
        script.end_named(self.db, ["CONF-STUCK"])
        conference = self.conference("CONF-STUCK")
        self.assertEqual((conference.conferenceStatus, conference.conferenceEndsOn), ("Session Completed", "2026-09-15 06:00:00"))

    def test_only_the_named_ones_and_only_while_still_running(self):
        _, skipped = script.end_named(self.db, ["CONF-IDLE", "CONF-DONE", "CONF-LATER", "CONF-NOPE"])
        self.assertEqual(skipped, ["CONF-DONE", "CONF-LATER", "CONF-NOPE"])
        self.assertEqual(self.conference("CONF-OTHER").conferenceStatus, "Live")          # running, not named
        self.assertEqual(self.conference("CONF-LATER").conferenceStatus, "Scheduled")
        self.assertEqual(self.flow("CONF-DONE"), [])

    def test_ending_is_in_the_activity_log(self):
        script.end_named(self.db, ["CONF-IDLE"])
        entry = self.db.query(LogsMaster).filter_by(action="END_SESSION").one()
        self.assertEqual(entry.username, script.PERFORMED_BY)
        self.assertIn("CONF-IDLE", entry.remarks)


if __name__ == "__main__":
    unittest.main()
