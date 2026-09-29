"""Phase 3 follow-up:

1. The trainer Home dashboard counts in SQL (dashboard_repository.trainer_summary_counts) and must
   give exactly the numbers the old Python counting gave (tests/_legacy_trainer_agenda.py) - checked
   on randomized, messy data (mixed-case / blank / NULL statuses, NULL dates, several trainers).
2. A list's total is counted once and reused until the list data changes
   (database/change_tracking + repositories/keyset._count), then recounted - never stale.
"""

import random
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.repositories import dashboard_repository, keyset
from app.utils.date_utils import ist_now
from tests import _legacy_trainer_agenda as legacy

STATUSES = ["Scheduled", "Ongoing", "Completed", "Cancelled", "completed", "LIVE", "Live", "", None, "Not Started"]
APPROVALS = ["Approved", "approved", "Pending", "Rejected", "", None]
TRAINERS = ["t1", "t2", "t3"]


class HomeSummaryMatchesTheOldCounting(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        rng = random.Random(7)
        today = date.today()
        for n in range(400):
            offset = rng.randint(-40, 40)
            conference_date = None if rng.random() < 0.08 else (today + timedelta(days=offset)).isoformat()
            if rng.random() < 0.1:
                conference_date = today.isoformat()
            uid = f"C{n:04d}"
            self.db.add(Conference(conferenceUid=uid, trainerEmployeeId=rng.choice(TRAINERS), conferenceDate=conference_date,
                                   conferenceStatus=rng.choice(STATUSES), status=rng.choice(APPROVALS)))
            for k in range(rng.randint(0, 4)):
                trainee = f"T{rng.randint(0, 150)}"
                self.db.add(Attendance(attendanceUid=f"A{n}-{k}", conferenceUid=uid, traineeUid=trainee,
                                       status=rng.choice(["Present", "Pending", "Absent", "Joined"])))
                if rng.random() < 0.4:
                    self.db.add(AssessmentResult(resultUid=f"R{n}-{k}", conferenceUid=uid, traineeUid=trainee,
                                                 assessmentSuiteUid="S", attemptNumber=1, totalScore=1, maxScore=2,
                                                 percentage=50, status=rng.choice(["Submitted", "Draft"])))
        self.db.commit()
        self.today = today

    def sql(self, trainer, start, end):
        counts = dashboard_repository.trainer_summary_counts(
            self.db, trainer, start, end, today=date.today().isoformat(), today_ist=ist_now().date().isoformat()
        )
        total = counts["totalSessions"]
        counts["executedPercentage"] = round(counts["completed"] / total * 100) if total else 0
        counts["pendingPercentage"] = round(counts["pending"] / total * 100) if total else 0
        return counts

    def test_same_numbers_for_every_trainer_and_range(self):
        ranges = [
            (None, None),                                                        # the default "today" view
            ((self.today - timedelta(days=30)).isoformat(), self.today.isoformat()),
            (self.today.isoformat(), (self.today + timedelta(days=30)).isoformat()),
            ((self.today - timedelta(days=7)).isoformat(), (self.today + timedelta(days=7)).isoformat()),
            ("2000-01-01", "2099-12-31"),
            ("2099-01-01", "2099-12-31"),                                        # nothing in range
        ]
        for trainer in TRAINERS + ["nobody"]:
            for start, end in ranges:
                with self.subTest(trainer=trainer, start=start, end=end):
                    self.assertEqual(self.sql(trainer, start, end), legacy.trainer_counts(self.db, trainer, start, end))

    def test_the_counts_take_two_statements_whatever_the_history(self):
        seen = []
        listener = lambda conn, cursor, statement, params, context, many: seen.append(statement)
        event.listen(self.db.get_bind(), "before_cursor_execute", listener)
        try:
            self.sql("t1", None, None)
        finally:
            event.remove(self.db.get_bind(), "before_cursor_execute", listener)
        self.assertEqual(len(seen), 2)


class CountIsReusedUntilTheDataChanges(unittest.TestCase):
    def setUp(self):
        keyset.clear_count_cache()
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        for n in range(30):
            self.db.add(Conference(conferenceUid=f"C{n:02d}", trainerEmployeeId="t1", conferenceDate="2026-10-01"))
        self.db.commit()
        self.order = keyset.SortOrder.keyset("id", Conference.id, Conference.id, descending=False, cursor_value=lambda r: r.id)
        self.counts = 0

        def listener(conn, cursor, statement, params, context, many):
            if "count(" in statement.lower():
                self.counts += 1

        event.listen(self.engine, "before_cursor_execute", listener)
        self.addCleanup(event.remove, self.engine, "before_cursor_execute", listener)

    def page(self, number=1, where=()):
        stmt = select(Conference).where(Conference.trainerEmployeeId == "t1", *where)
        return keyset.paginate(self.db, stmt, self.order, cursor=None, limit=10, page=number)

    def test_paging_through_an_unchanged_list_counts_once(self):
        totals = [self.page(n).total for n in (1, 2, 3, 1)]
        self.assertEqual(totals, [30, 30, 30, 30])
        self.assertEqual(self.counts, 1)

    def test_an_insert_a_delete_and_an_edit_each_trigger_a_fresh_count(self):
        self.assertEqual(self.page().total, 30)
        self.db.add(Conference(conferenceUid="NEW", trainerEmployeeId="t1"))
        self.db.commit()
        self.assertEqual(self.page(2).total, 31)                                  # added
        self.db.query(Conference).filter(Conference.conferenceUid == "C00").delete()
        self.db.commit()
        self.assertEqual(self.page(3).total, 30)                                  # deleted (bulk delete)
        self.db.query(Conference).filter(Conference.conferenceUid == "C01").update({"trainerEmployeeId": "t2"})
        self.db.commit()
        self.assertEqual(self.page().total, 29)                                   # edited out of the list
        with self.engine.begin() as conn:                                         # a raw SQL write
            conn.execute(text("UPDATE conference SET trainerEmployeeId = 't1' WHERE conferenceUid = 'C01'"))
        self.assertEqual(self.page().total, 30)
        self.assertEqual(self.counts, 5)

    def test_a_rolled_back_write_does_not_force_a_recount(self):
        self.page()
        self.db.add(Conference(conferenceUid="GONE", trainerEmployeeId="t1"))
        self.db.flush()
        self.db.rollback()
        self.assertEqual(self.page(2).total, 30)
        self.assertEqual(self.counts, 1)

    def test_different_filters_are_counted_separately(self):
        self.assertEqual(self.page().total, 30)
        self.assertEqual(self.page(where=[Conference.conferenceUid.like("C0%")]).total, 10)
        self.assertEqual(self.counts, 2)

    def test_writes_to_unrelated_tables_keep_the_count(self):
        self.page()
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO logsmaster (username, action, status) VALUES ('x', 'LOGIN', 'Success')"))
        self.page(2)
        self.assertEqual(self.counts, 1)

    def test_an_expired_count_is_recounted(self):
        self.page()
        with patch.object(keyset._count_cache, "get", return_value=None):  # as if the TTL passed
            self.page(2)
        self.assertEqual(self.counts, 2)


if __name__ == "__main__":
    unittest.main()
