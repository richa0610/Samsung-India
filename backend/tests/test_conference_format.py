"""app/utils/conference_format.py - a training stored the other system's way (user, 2026-10-17), read
in this app's words and written back. The samples are the user's own: their sessionConfig, their
masterRemarks, their status / module / quiz-state / clock values. Rows this app wrote before must
keep reading exactly as they did.

The SQL twins (status_sql, dashboard_repository.live_quiz_suite_is) are checked against their Python
rules on an in-memory SQLite database (never a real one)."""

import json
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import Column, Integer, String, Text, create_engine, select
from sqlalchemy.orm import declarative_base

from app.repositories.dashboard_repository import live_quiz_suite_is
from app.utils import conference_format as fmt
from app.utils.date_utils import IST, parse_module_start, to_stored_time, to_venue_time

# The sessionConfig the user pasted from the other system (2026-10-17), verbatim.
THEIR_SESSION_CONFIG = (
    '[{"type":"Attendance","config":{"date":"2026-06-11","checkInTime":"09:00","checkOutTime":"20:00","geoFencing":"1"}},'
    '{"type":"Assessment","linkedUid":"AS2694620","questionCount":"5","config":{"date":"2026-06-11","startTime":"14:00","endTime":"","checkInRequired":"1","unlockCondition":"Manual"}},'
    '{"type":"Survey","linkedUid":"AS2684628","questionCount":"3","config":{"date":"2026-06-11","startTime":"14:57","endTime":"","checkInRequired":"1","unlockCondition":"Manual"}},'
    '{"type":"Assessment","linkedUid":"AS2684628","questionCount":"3","config":{"date":"2026-06-11","startTime":"18:54","endTime":"","unlockCondition":"Manual"}}]'
)


def conference(**columns):
    defaults = {
        "conferenceStatus": None, "activeModuleId": None, "liveQuizState": None, "liveTimerEndsAt": None,
        "sessionConfig": None, "postAssessmentUid": None, "surveyUid": None, "conferenceType": None,
        "state": None, "district": None, "enableCheckIn": 0,
    }
    return SimpleNamespace(**{**defaults, **columns})


class SessionStatus(unittest.TestCase):
    def test_their_words_and_ours_read_the_same(self):
        for stored, word in (("Started", "Ongoing"), ("ongoing", "Ongoing"), ("Live", "Ongoing"),
                             ("Session Completed", "Completed"), ("completed", "Completed"),
                             ("Scheduled", "Scheduled"), ("cancelled", "Cancelled")):
            with self.subTest(stored=stored):
                self.assertEqual(fmt.session_status(stored), word)

    def test_what_is_stored(self):
        self.assertEqual([fmt.stored_status(s) for s in ("Ongoing", "Completed", "Scheduled", "Cancelled")],
                         ["Started", "Session Completed", "Scheduled", "Cancelled"])

    def test_the_checks(self):
        self.assertTrue(fmt.is_running(conference(conferenceStatus="Started")))
        self.assertTrue(fmt.is_running(conference(conferenceStatus="Ongoing")))
        self.assertTrue(fmt.is_completed(conference(conferenceStatus="Session Completed")))
        self.assertFalse(fmt.is_running(conference(conferenceStatus="Scheduled")))


class ActiveModule(unittest.TestCase):
    def test_their_module_ids_and_our_old_keys(self):
        for stored, key in (("Attendance_0", "ATTENDANCE"), ("Assessment_AS2694620", "STANDARD_TEST"),
                            ("Quiz_AS2684628", "LIVE_QUIZ"), ("Survey_AS2684628", "SURVEY"),
                            ("LIVE_QUIZ", "LIVE_QUIZ"), ("STANDARD_TEST", "STANDARD_TEST"), ("", None), (None, None)):
            with self.subTest(stored=stored):
                self.assertEqual(fmt.active_module(conference(activeModuleId=stored)), key)

    def test_what_is_stored_while_a_module_runs(self):
        quiz_flow = json.dumps([{"type": "Quiz", "linkedUid": "AS2638835", "config": {}}])
        row = conference(postAssessmentUid="AS2694620", surveyUid="AS2684628", sessionConfig=quiz_flow)
        self.assertEqual(
            [fmt.module_id(row, key) for key in ("ATTENDANCE", "STANDARD_TEST", "LIVE_QUIZ", "SURVEY", None)],
            ["Attendance_0", "Assessment_AS2694620", "Quiz_AS2638835", "Survey_AS2684628", None],
        )


class QuizStateAndClock(unittest.TestCase):
    def test_their_states_read_as_ours(self):
        for stored, state in (("IDLE", "IDLE"), ("WAITING", "IDLE"), (None, "IDLE"), ("QUESTION_LIVE", "QUESTION_LIVE"),
                              ("LEADERBOARD", "LEADERBOARD"), ("CLOSED", "FINISHED"), ("FINISHED", "FINISHED")):
            with self.subTest(stored=stored):
                self.assertEqual(fmt.quiz_state(conference(liveQuizState=stored)), state)

    def test_the_lobby_is_stored_waiting_and_a_finished_quiz_closed(self):
        row = conference()
        stored = []
        for state in ("IDLE", "QUESTION_LIVE", "LEADERBOARD", "FINISHED"):
            fmt.set_quiz_state(row, state)
            stored.append(row.liveQuizState)
        self.assertEqual(stored, ["WAITING", "QUESTION_LIVE", "LEADERBOARD", "CLOSED"])

    def test_the_clock_is_stored_as_the_india_date_time(self):
        ends = datetime(2026, 5, 5, 12, 2, 1, tzinfo=IST)
        row = conference()
        fmt.set_timer_ends(row, int(ends.timestamp() * 1000))
        self.assertEqual(row.liveTimerEndsAt, 20260505120201)              # as in their row 10
        self.assertEqual(fmt.timer_ends_ms(row), int(ends.timestamp() * 1000))

    def test_an_older_epoch_millisecond_clock_still_reads(self):
        self.assertEqual(fmt.timer_ends_ms(conference(liveTimerEndsAt=1_800_000_030_000)), 1_800_000_030_000)
        self.assertIsNone(fmt.timer_ends_ms(conference(liveTimerEndsAt=0)))
        self.assertIsNone(fmt.timer_ends_ms(conference(liveTimerEndsAt=None)))


class SessionConfig(unittest.TestCase):
    def test_their_config_reads_one_module_of_each_kind(self):
        flow = fmt.read_session_config(THEIR_SESSION_CONFIG)
        self.assertEqual(flow, {
            "attendance": {"checkInOpens": "09:00 AM", "checkOutCloses": "08:00 PM", "geoFencing": True},
            "standardTest": {"assessmentSuiteUid": "AS2694620", "questionCount": 5, "startTime": "02:00 PM",
                             "unlockCondition": "Manual Broadcast", "checkIn": True},
            "survey": {"assessmentSuiteUid": "AS2684628", "questionCount": 3, "startTime": "02:57 PM",
                       "unlockCondition": "Manual Broadcast", "checkIn": True},
        })

    def test_a_flow_is_stored_in_their_shape_in_run_order(self):
        flow = {
            "survey": {"assessmentSuiteUid": "AS2684628", "questionCount": 3, "startTime": "02:57 PM", "checkIn": True,
                       "unlockCondition": "Manual Broadcast", "category": "Survey"},
            "attendance": {"checkInOpens": "09:00 AM", "checkOutCloses": "08:00 PM", "geoFencing": True, "geoRadius": 150},
            "standardTest": {"assessmentSuiteUid": "AS2694620", "questionCount": 5, "startTime": "02:00 PM",
                             "endTime": "02:30 PM", "checkIn": True, "unlockCondition": "Automatic"},
            "liveQuiz": {"assessmentSuiteUid": "AS2638835", "questionCount": 4, "startTime": "06:54 PM", "checkIn": False},
        }
        self.assertEqual(json.loads(fmt.write_session_config(flow, "2026-06-11")), [
            {"type": "Attendance", "config": {"date": "2026-06-11", "checkInTime": "09:00", "checkOutTime": "20:00", "geoFencing": "1"}},
            {"type": "Assessment", "linkedUid": "AS2694620", "questionCount": "5",
             "config": {"date": "2026-06-11", "startTime": "14:00", "endTime": "14:30", "checkInRequired": "1", "unlockCondition": "Automatic"}},
            {"type": "Survey", "linkedUid": "AS2684628", "questionCount": "3",
             "config": {"date": "2026-06-11", "startTime": "14:57", "endTime": "", "checkInRequired": "1", "unlockCondition": "Manual"}},
            {"type": "Quiz", "linkedUid": "AS2638835", "questionCount": "4",
             "config": {"date": "2026-06-11", "startTime": "18:54", "endTime": "", "unlockCondition": "Manual"}},
        ])

    def test_compact_like_theirs(self):
        stored = fmt.write_session_config({"attendance": {"checkInOpens": "09:00 AM", "geoFencing": False}}, "2026-06-11")
        self.assertEqual(stored, '[{"type":"Attendance","config":{"date":"2026-06-11","checkInTime":"09:00","checkOutTime":"","geoFencing":"0"}}]')

    def test_what_is_written_reads_back(self):
        flow = {
            "attendance": {"checkInOpens": "09:00 AM", "checkOutCloses": "10:00 AM", "geoFencing": True},
            "liveQuiz": {"assessmentSuiteUid": "AS1", "questionCount": 2, "startTime": "11:00 AM", "endTime": "11:30 AM",
                         "unlockCondition": "Automatic", "checkIn": False},
        }
        self.assertEqual(fmt.read_session_config(fmt.write_session_config(flow, "2026-06-11")), flow)

    def test_no_module_stores_nothing(self):
        self.assertIsNone(fmt.write_session_config({}, "2026-06-11"))

    def test_an_older_dict_reads_as_it_is(self):
        older = {"liveQuiz": {"assessmentSuiteUid": "AS1", "startTime": "10:00 AM"}, "trainingEndDate": "2026-06-13"}
        self.assertEqual(fmt.read_session_config(json.dumps(older)), older)

    def test_unreadable_values_read_as_no_flow(self):
        for stored in (None, "", "not json", "42", '["x"]'):
            with self.subTest(stored=stored):
                self.assertEqual(fmt.read_session_config(stored), {})

    def test_the_live_quiz_sets(self):
        two_quizzes = json.dumps([{"type": "Quiz", "linkedUid": "AS1"}, {"type": "Quiz", "linkedUid": "AS2"},
                                  {"type": "Quiz", "linkedUid": 7}, {"type": "Survey", "linkedUid": "AS3"}])
        self.assertEqual(fmt.live_quiz_suite_uid(conference(sessionConfig=two_quizzes)), "AS1")   # the one that runs
        self.assertEqual(fmt.quiz_suite_uids(conference(sessionConfig=two_quizzes)), {"AS1", "AS2"})
        self.assertEqual(fmt.quiz_suite_uids(conference(sessionConfig='{"liveQuiz": {"assessmentSuiteUid": "AS9"}}')), {"AS9"})
        self.assertEqual(fmt.quiz_suite_uids(conference(sessionConfig=THEIR_SESSION_CONFIG)), set())


class LiveQuizSuiteSqlTwin(unittest.TestCase):
    """dashboard_repository.live_quiz_suite_is (SQLite) answers exactly as quiz_suite_uids."""

    CONFIGS = (
        None, "", "not json", "[]", '["x", 1]', THEIR_SESSION_CONFIG,
        '{"liveQuiz": {"assessmentSuiteUid": "AS1"}}', '{"liveQuiz": {"assessmentSuiteUid": 1}}',
        json.dumps([{"type": "Quiz", "linkedUid": "AS1"}, {"type": "Quiz", "linkedUid": "AS2"}]),
        json.dumps([{"type": "quiz", "linkedUid": "AS1"}, {"type": "Quiz", "linkedUid": 1}, {"type": "Quiz", "linkedUid": ""}]),
        json.dumps([{"type": "Assessment", "linkedUid": "AS1"}]),
    )
    SUITES = ("AS1", "AS2", "AS2694620", "1", "")

    def test_sql_and_python_agree(self):
        base = declarative_base()

        class Row(base):
            __tablename__ = "rows"
            id = Column(Integer, primary_key=True)
            config = Column(Text)
            suite = Column(String(50))

        engine = create_engine("sqlite://")
        base.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(Row.__table__.insert(), [
                {"config": config, "suite": suite} for config in self.CONFIGS for suite in self.SUITES
            ])
            rows = conn.execute(select(Row.config, Row.suite, live_quiz_suite_is(Row.config, Row.suite))).all()
        self.assertEqual(len(rows), len(self.CONFIGS) * len(self.SUITES))
        for config, suite, matched in rows:
            with self.subTest(config=config, suite=suite):
                self.assertEqual(bool(matched), suite in fmt.quiz_suite_uids(conference(sessionConfig=config)))


class Times(unittest.TestCase):
    def test_stored_24_hour_shown_12_hour(self):
        self.assertEqual([to_stored_time(v) for v in ("02:00 PM", "14:00", "09:05 AM", "", None)], ["14:00", "14:00", "09:05", "", ""])
        self.assertEqual([to_venue_time(v) for v in ("14:00", "02:00 PM", "", None)], ["02:00 PM", "02:00 PM", None, None])

    def test_either_way_parses_to_the_same_moment(self):
        self.assertEqual(parse_module_start("2026-06-11", "14:00"), parse_module_start("2026-06-11", "02:00 PM"))
        self.assertEqual(parse_module_start("2026-06-11", "14:00"), datetime(2026, 6, 11, 14, 0))


class CreationValues(unittest.TestCase):
    def test_their_note_for_a_new_training(self):
        self.assertEqual(fmt.creation_note(False, "Arun", "AGT001", "CONF2675966"),
                         "New Non Residential Conference added by Arun (AGT001) | UID: CONF2675966")
        self.assertTrue(fmt.creation_note(True, "Arun", "AGT001", "CONF1").startswith("New Residential Conference"))

    def test_conference_type(self):
        self.assertEqual(fmt.conference_type(False), "Non-Residential Conference")
        self.assertEqual(fmt.conference_type(True), "Residential Conference")
        self.assertFalse(fmt.is_residential(conference(conferenceType="Non-Residential Conference")))
        self.assertFalse(fmt.is_residential(conference(conferenceType="Non Residential Conference")))
        self.assertTrue(fmt.is_residential(conference(conferenceType="Residential Conference")))

    def test_trainer_name(self):
        self.assertEqual(fmt.trainer_label("Demo Trainer", "demotrainer"), "Demo Trainer (demotrainer)")
        self.assertEqual(fmt.trainer_label("Jasodha", "Jasodha"), "Jasodha")
        self.assertEqual(fmt.trainer_label(None, "trainer1"), "trainer1")

    def test_not_assigned_and_no_file(self):
        self.assertEqual(fmt.stored_or_not_assigned(None), "Not Assigned")
        self.assertEqual(fmt.stored_or_not_assigned(" Delhi "), "Delhi")
        self.assertIsNone(fmt.assigned("Not Assigned"))
        self.assertIsNone(fmt.assigned("not assigned"))
        self.assertEqual(fmt.assigned("Delhi"), "Delhi")
        self.assertIsNone(fmt.uploaded("defaultfile.png"))
        self.assertEqual(fmt.uploaded("CONF1/Host_CHECKIN_START_20260611090000.jpg"), "CONF1/Host_CHECKIN_START_20260611090000.jpg")

    def test_places_stored_in_capitals_shown_as_words(self):
        self.assertEqual(fmt.stored_place("  new   delhi "), "NEW DELHI")
        self.assertIsNone(fmt.stored_place(""))
        self.assertEqual(fmt.location_label(conference(district="NEW DELHI", state="DELHI")), "New Delhi, Delhi")
        self.assertIsNone(fmt.location_label(conference()))

    def test_approval_notes_are_stored_as_html_and_read_as_text(self):
        self.assertEqual(fmt.stored_remark("Approved"), "<p>Approved</p>")
        self.assertEqual(fmt.stored_remark("ok <b>"), "<p>ok &lt;b&gt;</p>")
        self.assertIsNone(fmt.stored_remark("  "))
        self.assertEqual(fmt.remark_text("<p>Approved - 11 AM&nbsp;<br>Re Check</p>"), "Approved - 11 AM\nRe Check")
        self.assertEqual(fmt.remark_text("<p>Approved</p><p><br></p>"), "Approved")
        self.assertEqual(fmt.remark_text(fmt.stored_remark("ok <b>")), "ok <b>")
        self.assertEqual(fmt.remark_text("plain text from before"), "plain text from before")


class ExecutionFlowLog(unittest.TestCase):
    """conference_activity_log rows stored the other system's way; rows written before read the same."""

    QUIZ = json.dumps([{"type": "Quiz", "linkedUid": "AS2638835", "config": {}}])

    def row(self, module, action, when=datetime(2026, 10, 17, 10, 0)):
        return SimpleNamespace(moduleId=module, action=action, timestamp=when)

    def test_what_is_stored_for_each_entry(self):
        row = conference(sessionConfig=self.QUIZ, postAssessmentUid="AS2694620")
        self.assertEqual(fmt.log_columns(row, None, "SESSION_STARTED"), {"moduleId": "", "action": "STARTED"})
        self.assertEqual(fmt.log_columns(row, None, "SESSION_ENDED"), {"moduleId": "", "action": "STOPPED"})
        self.assertEqual(fmt.log_columns(row, "LIVE_QUIZ", "STARTED"), {"moduleId": "Quiz_AS2638835", "action": "STARTED"})
        self.assertEqual(fmt.log_columns(row, "STANDARD_TEST", "STOPPED"), {"moduleId": "Assessment_AS2694620", "action": "STOPPED"})
        self.assertEqual(fmt.log_columns(row, None, "SCHEDULE_OVERRIDE"), {"moduleId": "", "action": "SCHEDULE_OVERRIDE"})

    def test_their_rows_and_ours_from_before_read_the_same(self):
        for stored, module, action in (
            (self.row("", "STARTED"), None, "SESSION_STARTED"),
            (self.row(None, "SESSION_STARTED"), None, "SESSION_STARTED"),
            (self.row("", "STOPPED"), None, "SESSION_ENDED"),
            (self.row(None, "SESSION_ENDED"), None, "SESSION_ENDED"),
            (self.row("Survey_AS2684628", "STARTED"), "SURVEY", "STARTED"),
            (self.row("SURVEY", "STARTED"), "SURVEY", "STARTED"),
            (self.row("", "SCHEDULE_OVERRIDE"), None, "SCHEDULE_OVERRIDE"),
        ):
            with self.subTest(moduleId=stored.moduleId, action=stored.action):
                self.assertEqual((fmt.log_module(stored), fmt.log_action(stored)), (module, action))

    def test_times_are_read_in_india_time(self):
        when = datetime(2026, 10, 17, 4, 30)
        self.assertEqual(fmt.log_time(self.row(None, "SESSION_STARTED", when)), when + timedelta(hours=5, minutes=30))
        self.assertEqual(fmt.log_time(self.row("LIVE_QUIZ", "STARTED", when)), when + timedelta(hours=5, minutes=30))
        self.assertEqual(fmt.log_time(self.row("", "STARTED", when)), when)
        self.assertEqual(fmt.log_time(self.row("Quiz_AS1", "STARTED", when)), when)

    def test_a_venue_override_remark(self):
        self.assertEqual(fmt.gps_override_remark(28.4967682, 77.161650), "GPS_OVERRIDE: 28.496768, 77.161650")

    def test_attendance_in_their_list_or_by_the_older_flag(self):
        self.assertTrue(fmt.has_attendance(conference(sessionConfig=THEIR_SESSION_CONFIG, enableCheckIn=0)))
        self.assertFalse(fmt.has_attendance(conference(sessionConfig=self.QUIZ, enableCheckIn=1)))
        self.assertTrue(fmt.has_attendance(conference(sessionConfig='{"attendance": {}}', enableCheckIn=1)))
        self.assertFalse(fmt.has_attendance(conference(sessionConfig='{"attendance": {}}', enableCheckIn=0)))
