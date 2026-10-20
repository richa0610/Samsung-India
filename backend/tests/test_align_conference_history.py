"""scripts/align_conference_history.py - brings what this app saved before 2026-10-17 into the other
system's format where it can't be read either way (user): UTC start / end times -> India time, and
older Execution Flow rows -> module IDs, STARTED / STOPPED for the session, India time. A time is only
moved when the training's own log shows it was saved in UTC; rows already in the new format are left
alone, so a second run changes nothing; what it can't check is reported, never changed. It keeps an
undo file.

In-memory SQLite only."""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog as Log
from scripts import align_conference_history as script

UTC_START = datetime(2026, 10, 12, 4, 0, 5)   # 09:30:05 in India
UTC_END = datetime(2026, 10, 12, 6, 30, 40)
INDIA = timedelta(hours=5, minutes=30)
QUIZ_FLOW = json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-Q"}})


class AlignConferenceHistory(unittest.TestCase):
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

        # Run by this app before the change: UTC times, its own log format.
        self.db.add(Conference(conferenceUid="CONF-OLD", actualStartedAt=UTC_START, actualEndedAt=UTC_END,
                               sessionConfig=QUIZ_FLOW, postAssessmentUid="SUITE-T"))
        self.log("CONF-OLD", None, "SESSION_STARTED", UTC_START - timedelta(seconds=2), "trainer1", lat=28.5)
        self.log("CONF-OLD", "LIVE_QUIZ", "STARTED", UTC_START + timedelta(minutes=5), "trainer1")
        self.log("CONF-OLD", "LIVE_QUIZ", "STOPPED", UTC_START + timedelta(minutes=20), "trainer1")
        self.log("CONF-OLD", None, "SCHEDULE_OVERRIDE", UTC_START, "trainer1", remark="Traffic")
        self.log("CONF-OLD", None, "SESSION_ENDED", UTC_END, "trainer1")
        # Run since the change (or by the other system): India times, their format.
        self.db.add(Conference(conferenceUid="CONF-NEW", actualStartedAt=UTC_START + INDIA, sessionConfig=QUIZ_FLOW))
        self.log("CONF-NEW", "", "STARTED", UTC_START + INDIA, "Arun")
        self.log("CONF-NEW", "Quiz_SUITE-Q", "STARTED", UTC_START + INDIA + timedelta(minutes=5), "Arun")
        # Nothing to check against; a log row whose training is gone.
        self.db.add(Conference(conferenceUid="CONF-NOLOG", actualStartedAt=UTC_START))
        self.log("CONF-GONE", "ATTENDANCE", "STARTED", UTC_START, "trainer9")
        self.db.commit()

    def log(self, uid, module, action, when, who, lat=None, remark=None):
        self.db.add(Log(conferenceUid=uid, moduleId=module, action=action, timestamp=when, performedBy=who,
                        trainerLat=lat, locationRemark=remark))

    def conference(self, uid):
        self.db.expire_all()
        return self.db.query(Conference).filter_by(conferenceUid=uid).one()

    def rows(self, uid):
        self.db.expire_all()
        return [(r.moduleId, r.action, r.timestamp, r.performedBy, r.trainerLat and float(r.trainerLat), r.locationRemark)
                for r in self.db.query(Log).filter_by(conferenceUid=uid).order_by(Log.id)]

    def test_the_preview_finds_only_what_was_written_the_older_way_and_writes_nothing(self):
        plan = script.make_plan(self.db)
        self.assertEqual({(c.table, c.column) for c in plan.changes if c.table == "conference"}, {("conference", "actualStartedAt"), ("conference", "actualEndedAt")})
        self.assertEqual(plan.log_rows, 6)                                       # CONF-OLD's five + CONF-GONE's one
        self.assertEqual(plan.already_india, 1)                                  # CONF-NEW's start
        self.assertEqual(len(plan.left_alone), 1)
        self.assertIn("CONF-NOLOG", plan.left_alone[0])
        self.assertEqual(self.conference("CONF-OLD").actualStartedAt, UTC_START)

    def test_apply_converts_them_and_a_second_run_changes_nothing(self):
        script.apply(self.db, script.make_plan(self.db), "alpha")
        old = self.conference("CONF-OLD")
        self.assertEqual((old.actualStartedAt, old.actualEndedAt), (UTC_START + INDIA, UTC_END + INDIA))
        self.assertEqual(self.rows("CONF-OLD"), [
            ("", "STARTED", UTC_START - timedelta(seconds=2) + INDIA, "trainer1", 28.5, None),   # who / where kept
            ("Quiz_SUITE-Q", "STARTED", UTC_START + timedelta(minutes=5) + INDIA, "trainer1", None, None),
            ("Quiz_SUITE-Q", "STOPPED", UTC_START + timedelta(minutes=20) + INDIA, "trainer1", None, None),
            ("", "SCHEDULE_OVERRIDE", UTC_START + INDIA, "trainer1", None, "Traffic"),
            ("", "STOPPED", UTC_END + INDIA, "trainer1", None, None),
        ])
        self.assertEqual(self.rows("CONF-GONE"), [("Attendance_0", "STARTED", UTC_START + INDIA, "trainer9", None, None)])
        self.assertEqual(self.conference("CONF-NEW").actualStartedAt, UTC_START + INDIA)          # untouched
        again = script.make_plan(self.db)
        self.assertEqual((again.changes, again.log_rows, again.already_india), ([], 0, 3))

    def test_undo_puts_back_exactly_what_it_changed(self):
        before = {uid: self.rows(uid) for uid in ("CONF-OLD", "CONF-GONE", "CONF-NEW")}
        plan = script.make_plan(self.db)
        _, backup = script.apply(self.db, plan, "alpha")
        self.assertEqual(script.undo(self.db, backup, "alpha"), (len(plan.changes), len(plan.changes)))
        self.assertEqual({uid: self.rows(uid) for uid in before}, before)
        self.assertEqual(self.conference("CONF-OLD").actualStartedAt, UTC_START)

    def test_undo_leaves_a_value_changed_since(self):
        plan = script.make_plan(self.db)
        _, backup = script.apply(self.db, plan, "alpha")
        self.db.query(Conference).filter_by(conferenceUid="CONF-OLD").update({"actualEndedAt": datetime(2026, 10, 13)})
        self.db.commit()
        self.assertEqual(script.undo(self.db, backup, "alpha"), (len(plan.changes) - 1, len(plan.changes)))
        self.assertEqual(self.conference("CONF-OLD").actualEndedAt, datetime(2026, 10, 13))

    def test_undo_refuses_another_tenants_file(self):
        _, backup = script.apply(self.db, script.make_plan(self.db), "alpha")
        with self.assertRaises(SystemExit):
            script.undo(self.db, backup, "beta")
