"""Phase 3 follow-up:

1. The trainer Home dashboard counts in SQL (dashboard_repository.trainer_summary_counts) and must
   give exactly the numbers the old Python counting gave (tests/_legacy_trainer_agenda.py) - checked
   on randomized, messy data (mixed-case / blank / NULL statuses, NULL dates, several trainers).
2. A list's total is counted fresh on every numbered page (no cache - Phase 5), so it is never stale.
"""

import random
import unittest
from datetime import date, timedelta

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


class CountIsAlwaysFresh(unittest.TestCase):
    """Phase 5: a numbered page's total is counted on every request - never cached, because other
    servers and systems write to the same database. A cursor continuation still skips the count."""

    def setUp(self):
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

    def page(self, number=1, cursor=None):
        stmt = select(Conference).where(Conference.trainerEmployeeId == "t1")
        return keyset.paginate(self.db, stmt, self.order, cursor=cursor, limit=10, page=None if cursor else number)

    def test_every_numbered_page_counts(self):
        self.assertEqual([self.page(n).total for n in (1, 2, 3)], [30, 30, 30])
        self.assertEqual(self.counts, 3)

    def test_a_write_from_anywhere_shows_in_the_next_total(self):
        self.assertEqual(self.page().total, 30)
        with self.engine.begin() as conn:  # another connection, as another server or system would
            conn.execute(text("INSERT INTO conference (conferenceUid, trainerEmployeeId) VALUES ('RAW', 't1')"))
        self.assertEqual(self.page(2).total, 31)

    def test_a_cursor_continuation_does_not_count(self):
        first = self.page()
        self.counts = 0
        self.page(cursor=first.next_cursor)
        self.assertEqual(self.counts, 0)


if __name__ == "__main__":
    unittest.main()
