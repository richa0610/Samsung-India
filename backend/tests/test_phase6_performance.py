"""Phase 6 - query-shape optimizations must return exactly what the original queries returned.

1. The trainer's Trainee List condition in its listing form (IN derived UNION) selects the same
   trainees as the row-check form (assigned OR EXISTS on-their-roster) - randomized data.
2. The Attendance List's deferred join: without a search or a trainee-column sort, the count and the
   sort/limit run without the trainee join, and the rows are joined in the same statement.
"""

import random
import unittest

from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import attendance_repository, conference_repository, keyset, trainee_repository

TRAINERS = ["t1", "t2", "t3", "", None]


class Database(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.addCleanup(self.db.close)

    def seed(self, seed):
        rng = random.Random(seed)
        for c in range(25):
            self.db.add(Conference(conferenceUid=f"C{c}", trainerEmployeeId=rng.choice(TRAINERS), company="Samsung India",
                                   conferenceDate=f"2026-09-{c % 28 + 1:02d}"))
        for n in range(120):
            self.db.add(Trainee(traineeUid=f"TR{n}", name=f"Name {n}", email=f"t{n}@example.test", phone=9_000_000_000 + n,
                                trainerEmployeeId=rng.choice(TRAINERS)))
        for n in range(300):
            self.db.add(Attendance(attendanceUid=f"A{n}", conferenceUid=f"C{rng.randrange(25)}", traineeUid=f"TR{rng.randrange(130)}",
                                   status=rng.choice(["Present", "Pending", "Joined", "Absent", None])))
        self.db.commit()


class TrainerOwnedListForm(Database):
    def uids(self, condition):
        return set(self.db.scalars(select(Trainee.traineeUid).where(condition)))

    def test_same_trainees_as_the_row_check_form(self):
        for seed in range(5):
            with self.subTest(seed=seed):
                for model in (Attendance, Trainee, Conference):
                    self.db.query(model).delete()
                self.db.commit()
                self.seed(seed)
                for trainer in ("t1", "t2", "t3", "nobody", "", None):
                    self.assertEqual(
                        self.uids(trainee_repository.trainer_owned_list_condition(trainer)),
                        self.uids(trainee_repository.trainer_owned_condition(trainer)),
                        trainer,
                    )

    def test_a_blank_trainer_owns_nothing(self):
        self.seed(1)
        self.assertEqual(self.uids(trainee_repository.trainer_owned_list_condition("")), set())
        self.assertEqual(self.uids(trainee_repository.trainer_owned_list_condition(None)), set())

    def test_it_compiles_to_a_derived_table_on_mysql(self):
        sql = str(select(Trainee.id).where(trainee_repository.trainer_owned_list_condition("t1")).compile(dialect=mysql.dialect()))
        self.assertIn("UNION", sql)
        self.assertIn("AS owned_trainees", sql)


class AttendanceDeferredJoin(Database):
    def statements(self, **kwargs):
        seen = []
        listener = lambda conn, cursor, statement, *a: seen.append(" ".join(statement.split()))
        event.listen(self.engine, "before_cursor_execute", listener)
        try:
            page = attendance_repository.list_page(self.db, [conference_repository.trainer_condition("t1")], **kwargs)
        finally:
            event.remove(self.engine, "before_cursor_execute", listener)
        return page, seen

    def test_no_trainee_join_in_the_count_or_the_sort_without_search(self):
        self.seed(2)
        page, statements = self.statements(limit=5)
        count, rows = statements
        self.assertNotIn("trainee", count.lower().replace("traineeuid", ""))
        self.assertIn("page_rows", rows)
        self.assertEqual(len(statements), 2)                         # still one count + one page statement
        self.assertLessEqual(len(page.rows), 5)

    def test_a_search_or_trainee_sort_keeps_the_join(self):
        self.seed(2)
        for kwargs in ({"search": "name"}, {"sort": "participantName"}, {"sort": "phone"}):
            with self.subTest(**kwargs):
                _page, statements = self.statements(limit=5, **kwargs)
                self.assertNotIn("page_rows", statements[-1])
                self.assertIn("LEFT OUTER JOIN trainee", statements[0])

    def test_deferred_rows_equal_the_full_join_rows(self):
        self.seed(3)
        conditions = [conference_repository.trainer_condition("t1")]
        for sort in ("markedAt", "conferenceDate", "attendanceStatus", "checkOut", "attendanceId"):
            for descending in (True, False):
                with self.subTest(sort=sort, descending=descending):
                    fast = attendance_repository.list_page(self.db, conditions, sort=sort, descending=descending, limit=200, page=1)
                    # A search that matches every row forces the original single-statement form.
                    full = attendance_repository.list_page(self.db, conditions, search="c", sort=sort, descending=descending,
                                                           limit=200, page=1)
                    self.assertEqual([tuple(r) for r in fast.rows], [tuple(r) for r in full.rows])
                    self.assertEqual(fast.total, full.total)

    def test_a_deferred_join_needs_a_single_expression_order(self):
        order = keyset.SortOrder.fixed("grouped", [Attendance.status], Attendance.id)
        with self.assertRaises(ValueError):
            keyset.paginate(self.db, select(Attendance.id.label("id"), Attendance.status.label("sort_value")), order,
                            cursor=None, limit=5, page=1, entities=False, enrich=lambda page_rows: select(page_rows))

    def test_the_deferred_page_compiles_for_mysql(self):
        seen = []
        original = self.db.execute

        def capture(statement, *args, **kwargs):
            seen.append(str(statement.compile(dialect=mysql.dialect())))
            return original(statement, *args, **kwargs)

        self.seed(4)
        self.db.execute = capture
        attendance_repository.list_page(self.db, [conference_repository.trainer_condition("t1")], limit=5)
        self.assertTrue(any("LIMIT" in s and "page_rows" in s for s in seen))


if __name__ == "__main__":
    unittest.main()
