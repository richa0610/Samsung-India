"""Session Dashboard Stage column (services/participant_stage.py).

1. The pin line reads "Attendance" once the participant is Present through their OWN check-in -
   else "Not Started", including when only the trainer marked them Present by hand.
2. Each activity after Attendance gets a chip, named Test / Quiz / Survey, in the flow's run order:
   done = a Submitted result for its question set in THIS training (the Training Detail rule).
3. One query for every activity's submissions, however many participants.
4. The dashboard's participant rows carry it.
"""

import json
import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.services.participant_stage import ATTENDED, NOT_STARTED, participant_stages
from tests.tenant_fixtures import uid
from tests.test_trainer_authorization import TrainerWorldTestCase

CONF = "CONF-STAGE"
# Survey is planned before the Live Quiz, so the run order is Attendance, Test, Survey, Quiz.
SESSION_CONFIG = json.dumps({
    "attendance": {"checkInOpens": "10:00 AM"},
    "standardTest": {"startTime": "10:15 AM"},
    "survey": {"startTime": "10:30 AM"},
    "liveQuiz": {"startTime": "11:00 AM", "assessmentSuiteUid": "QUIZ"},
})
SUITES = {"STANDARD_TEST": "TEST", "SURVEY": "SURVEY", "LIVE_QUIZ": "QUIZ"}


class ParticipantStages(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(engine)
        self.engine = engine
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)
        self.conference = Conference(conferenceUid=CONF, enableCheckIn=1, postAssessmentUid="TEST", surveyUid="SURVEY",
                                     sessionConfig=SESSION_CONFIG, conferenceStatus="Ongoing")
        self.db.add(self.conference)
        self.attendance = {}
        self.results = 0

    def trainee(self, trainee_uid, attendance="Present", submitted=(), drafts=(), elsewhere=(), photo=None, marked_by=None):
        if attendance:
            row = Attendance(attendanceUid=f"A-{trainee_uid}", conferenceUid=CONF, traineeUid=trainee_uid, status=attendance,
                             checkInPhoto=photo, updatedBy=marked_by)
            self.db.add(row)
            self.attendance[trainee_uid] = row
        for conference_uid, modules, status in ((CONF, submitted, "Submitted"), (CONF, drafts, "Draft"), ("CONF-OTHER", elsewhere, "Submitted")):
            for module in modules:
                self.results += 1
                self.db.add(AssessmentResult(resultUid=f"R{self.results}", conferenceUid=conference_uid, traineeUid=trainee_uid,
                                             assessmentSuiteUid=SUITES[module], attemptNumber=1, totalScore=1, maxScore=1,
                                             percentage=100, status=status))

    def stages(self):
        self.db.commit()
        return participant_stages(self.db, self.conference, self.attendance, list(self.attendance) + ["NO-ATTENDANCE"])

    def test_the_pin_line_says_attendance_once_checked_in_and_not_started_before(self):
        self.trainee("PRESENT")
        self.trainee("FINISHED", submitted=["STANDARD_TEST", "SURVEY", "LIVE_QUIZ"])
        self.trainee("JOINED", attendance="Pending")
        self.trainee("WALK_IN", attendance="Pending", submitted=["STANDARD_TEST"])
        self.trainee("ABSENT", attendance="Absent")

        stages = {trainee: s.stage for trainee, s in self.stages().items()}

        self.assertEqual(stages, {
            "PRESENT": ATTENDED,
            "FINISHED": ATTENDED,        # finishing the rest doesn't change it
            "JOINED": NOT_STARTED,
            "WALK_IN": NOT_STARTED,      # a submission without attendance doesn't count as attending
            "ABSENT": NOT_STARTED,
            "NO-ATTENDANCE": NOT_STARTED,
        })
        self.assertEqual(ATTENDED, "Attendance")

    def test_only_the_trainees_own_check_in_counts_not_a_trainer_mark_alone(self):
        photo = "attendance_photos/x.jpg"
        self.trainee("SECURE_CHECK_IN", photo=photo)                           # the app's normal check-in
        self.trainee("PLAIN_CHECK_IN")                                         # no location captured: no photo, no trainer
        self.trainee("TRAINER_MARKED", marked_by="trainer1")                  # marked Present by hand only
        self.trainee("MARKED_THEN_CHECKED_IN", photo=photo, marked_by="trainer1")
        self.trainee("TRAINER_MARKED_TESTED", marked_by="trainer1", submitted=["STANDARD_TEST"])
        self.trainee("CHECKED_IN_THEN_ABSENT", attendance="Absent", photo=photo, marked_by="trainer1")

        stages = {trainee: s.stage for trainee, s in self.stages().items()}

        self.assertEqual(stages["SECURE_CHECK_IN"], ATTENDED)
        self.assertEqual(stages["PLAIN_CHECK_IN"], ATTENDED)
        self.assertEqual(stages["TRAINER_MARKED"], NOT_STARTED)
        self.assertEqual(stages["MARKED_THEN_CHECKED_IN"], ATTENDED)
        self.assertEqual(stages["TRAINER_MARKED_TESTED"], NOT_STARTED)  # the test chip still shows it done
        self.assertEqual(stages["CHECKED_IN_THEN_ABSENT"], NOT_STARTED)

    def test_each_activity_after_attendance_is_a_short_named_chip_in_run_order(self):
        self.trainee("TESTED", submitted=["STANDARD_TEST"])
        modules = self.stages()["TESTED"].modules
        self.assertEqual(
            [(m.key, m.label, m.done) for m in modules],
            [("STANDARD_TEST", "Test", True), ("SURVEY", "Survey", False), ("LIVE_QUIZ", "Quiz", False)],
        )

    def test_only_a_submitted_result_in_this_training_counts(self):
        self.trainee("DRAFT", drafts=["STANDARD_TEST"])
        self.trainee("OTHER_TRAINING", elsewhere=["STANDARD_TEST", "SURVEY", "LIVE_QUIZ"])
        stages = self.stages()
        for trainee in ("DRAFT", "OTHER_TRAINING"):
            with self.subTest(trainee=trainee):
                self.assertFalse(any(m.done for m in stages[trainee].modules))

    def test_without_the_attendance_activity_present_still_reads_attendance_0(self):
        self.conference.enableCheckIn = 0
        self.trainee("PRESENT")
        self.assertEqual(self.stages()["PRESENT"].stage, ATTENDED)

    def test_a_training_with_only_attendance_has_no_chips(self):
        self.conference.postAssessmentUid = None
        self.conference.surveyUid = None
        self.conference.sessionConfig = None
        self.trainee("PRESENT")
        self.assertEqual(self.stages()["PRESENT"], (ATTENDED, []))

    def test_one_query_however_many_participants(self):
        for n in range(40):
            self.trainee(f"T{n}", submitted=["STANDARD_TEST"] if n % 2 else [])
        self.db.commit()
        # Loaded the way the dashboard hands them over: fresh rows, not expired ones.
        conference = self.db.query(Conference).filter_by(conferenceUid=CONF).one()
        attendance = {a.traineeUid: a for a in self.db.query(Attendance).filter_by(conferenceUid=CONF)}
        seen = []
        listener = lambda conn, cursor, statement, params, context, many: seen.append(statement)
        event.listen(self.engine, "before_cursor_execute", listener)
        try:
            stages = participant_stages(self.db, conference, attendance, list(attendance))
        finally:
            event.remove(self.engine, "before_cursor_execute", listener)
        self.assertEqual(len(seen), 1)
        self.assertEqual(sum(s.modules[0].done for s in stages.values()), 20)


class TheDashboardRowsCarryTheStage(TrainerWorldTestCase):
    def test_participant_rows_have_their_stage_and_activities(self):
        response = self.get("trainer1", f"/admin/trainings/{uid('S_N1')}")
        self.assertEqual(response.status_code, 200, response.text)
        row = next(t for t in response.json()["trainees"] if t["traineeUid"] == "TR-S_N1-0")
        # Present, with a Submitted result for the training's only test (SUITE-1).
        self.assertEqual(row["stage"], "Attendance")
        self.assertEqual(row["stageModules"], [{"key": "STANDARD_TEST", "label": "Test", "done": True}])

    def test_a_trainee_the_trainer_marks_present_by_hand_reads_not_started(self):
        self.set_status(uid("S_N1"), "Ongoing")
        marked = self.post("trainer1", f"/admin/trainings/{uid('S_N1')}/attendance/TR-S_N1-1",
                           {"status": "Present", "reason": "Arrived late, phone off"})
        self.assertEqual(marked.status_code, 200, marked.text)
        row = next(t for t in marked.json()["trainees"] if t["traineeUid"] == "TR-S_N1-1")
        self.assertEqual((row["status"], row["stage"]), ("Present", "Not Started"))


if __name__ == "__main__":
    unittest.main()
