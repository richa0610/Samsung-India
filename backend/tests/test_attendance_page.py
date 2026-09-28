"""Admin attendance list, server-side paging (training_service.list_attendance_page).

The oracle is `tests/_legacy_attendance.py` - a verbatim copy of the original
`list_attendance`, which loads everything and builds every row in Python. The new
paged version must return exactly the same rows and field values for every mode
and filter, in a well-defined order, with no row skipped or repeated while paging.

SQLite, in-memory, never imports app.main."""

import random
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.dependencies.filters import ConferenceFilters
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.models.trainee import Trainee
from app.services import training_service
from tests._legacy_attendance import legacy_list_attendance

EPOCH = datetime(1970, 1, 1)
ZONES = ["North Zone", "South Zone", " east zone "]
COMPANIES = ["Samsung India", "samsung india ", "Other Co"]
CONF_STATUS = ["Scheduled", "Ongoing", "Completed", "Cancelled"]
STATUSES = ["Present", "Present", "Pending", "Joined", "Absent"]
NAMES = ["Asha", "Ravi", "Meera_", "50% Off", "Kumar", "Zoya"]
TRAINING_TYPES = ["Webinar", "Classroom Training", None, "Product Training"]


class AttendancePageTestCase(unittest.TestCase):
    def setUp(self):
        # The models fill a missing UID with a MySQL-only statement; leave it empty
        # instead, so some fixture attendance rows really have no attendanceUid
        # (the list then shows the row id).
        stub = patch("app.models.uid_events.next_uid", lambda connection, prefix: None)
        stub.start()
        self.addCleanup(stub.stop)
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(bind=self.engine)
        self.db = sessionmaker(bind=self.engine)()
        rng = random.Random(21)
        base = datetime(2026, 1, 1)

        conferences = []
        for n in range(48):
            uid = f"conf{n:03d}"
            conferences.append(uid)
            self.db.add(
                Conference(
                    conferenceUid=uid,
                    zone=rng.choice(ZONES),
                    region=rng.choice(["North 1", "South 2", None]),
                    company=rng.choice(COMPANIES),
                    trainerEmployeeId=rng.choice(["t1", "t2", "t3"]),
                    trainerName=rng.choice(NAMES + [None]),
                    conferenceDate=(date(2026, 9, 1) + timedelta(days=rng.randint(0, 6))).isoformat(),
                    conferenceStatus=rng.choice(CONF_STATUS),
                    status="Approved",
                    sessionType=rng.choice(["Online", "Offline", None]),
                    audience=rng.choice(["Retail", None]),
                    trainingType=rng.choice(TRAINING_TYPES),
                    state=rng.choice(["Delhi", "UP", None]),
                    district=rng.choice(["Noida", None, "Agra"]),
                    postAssessmentUid=rng.choice(["s_post", "s_post", None]),
                )
            )
        trainees = []
        for n in range(30):
            uid = f"tr{n:03d}"
            trainees.append(uid)
            self.db.add(
                Trainee(
                    traineeUid=uid,
                    name=rng.choice(NAMES) + f" {n}",
                    email=f"user{n}@example.com",
                    phone=9_100_000_000 + n,
                    employee_id=rng.choice([f"HO{n}", None]),
                    supervisorName=rng.choice(["Sup A", None]),
                    username=f"user{n}",
                )
            )
        self.db.commit()

        seen = set()
        n = 0
        while len(seen) < 420:
            pair = (rng.choice(conferences), rng.choice(trainees + ["ghost1", "ghost2"]))  # ghosts have no trainee row
            if pair in seen:
                continue
            seen.add(pair)
            self.db.add(
                Attendance(
                    attendanceUid=rng.choice([f"att-{n}", None]),
                    conferenceUid=pair[0],
                    traineeUid=pair[1],
                    phone=rng.choice([None, 0, 9_200_000_000 + n]),
                    markedOn=rng.choice(["09:10", None]),
                    timestamp=base + timedelta(minutes=rng.randint(0, 25)),  # many ties
                    checkOutTime=rng.choice([None, base + timedelta(hours=rng.randint(1, 5))]),
                    updatedBy=rng.choice(["admin", None]),
                    status=rng.choice(STATUSES),
                )
            )
            n += 1
        self.db.commit()

        conf_post = {c.conferenceUid: c.postAssessmentUid for c in self.db.query(Conference)}
        for pair in list(seen):
            for attempt in range(1, rng.randint(1, 3) + 1):
                if rng.random() < 0.55:
                    self.db.add(
                        AssessmentResult(
                            resultUid=f"r{len(self.db.new)}-{pair}-{attempt}",
                            conferenceUid=pair[0],
                            traineeUid=pair[1],
                            assessmentSuiteUid=rng.choice([conf_post[pair[0]], "s_other"]) or "s_other",
                            attemptNumber=attempt,
                            totalScore=rng.randint(0, 10),
                            maxScore=10,
                            percentage=rng.choice([0, 25.5, 60, 100]),
                            status=rng.choice(["Submitted", "Submitted", "Started"]),
                        )
                    )
        self.db.commit()
        self.raw = {(a.attendanceUid or str(a.id)): a for a in self.db.query(Attendance)}

    # ---- helpers -------------------------------------------------------------
    def oracle(self, filters, mode="all"):
        items = legacy_list_attendance(self.db, None, True, filters)
        if mode == "pending":
            items = [i for i in items if not i.marked]
        elif mode == "confirmed":
            items = [i for i in items if i.marked]
        return items

    def page_call(self, filters, mode="all", search=None, sort="markedAt", descending=True, cursor=None, limit=10, page=None):
        # admin=None: this file tests query equivalence, not authorization (no admin_access
        # fixture here) - it deliberately skips scope resolution, the same way
        # test_org_training_list.py's direct call to list_trainings_page does.
        return training_service.list_attendance_page(self.db, None, filters, mode, search, sort, descending, cursor, limit, page)

    def walk(self, filters, mode="all", search=None, sort="markedAt", descending=True, limit=10, by="page"):
        items, cursor, page, total = [], None, 1, None
        for step in range(1000):
            response = self.page_call(filters, mode, search, sort, descending, cursor if by == "cursor" else None, limit, page if by == "page" else None)
            if step == 0:
                total = response.total
            else:
                self.assertIsNone(response.total, "total must only be sent with the first page")
            items += response.items
            self.assertLessEqual(len(response.items), limit)
            if by == "cursor":
                cursor = response.nextCursor
                if cursor is None:
                    return items, total
            else:
                if not response.items:
                    return items, total
                page += 1
        self.fail("paging never finished")


FILTERS = {
    "no filter": ConferenceFilters(),
    "company": ConferenceFilters(company="Samsung India"),
    "other company": ConferenceFilters(company="Other Co"),
    "zone": ConferenceFilters(zones=["north zone", "east zone"]),
    "dates + trainer": ConferenceFilters(start="2026-09-02", end="2026-09-05", trainers=["t1", "t2"]),
    "type + region": ConferenceFilters(training_types=["webinar"], regions=["north 1"]),
    "nothing matches": ConferenceFilters(zones=["mars"]),
}


class EquivalenceTests(AttendancePageTestCase):
    def test_same_rows_and_field_values_as_the_original_for_every_mode_and_filter(self):
        for name, filters in FILTERS.items():
            for mode in ("all", "pending", "confirmed"):
                for limit in (7, 50):
                    with self.subTest(filters=name, mode=mode, limit=limit):
                        expected = {i.attendanceId: i.model_dump() for i in self.oracle(filters, mode)}
                        items, total = self.walk(filters, mode, limit=limit)
                        got = {i.attendanceId: i.model_dump() for i in items}
                        self.assertEqual(len(items), len(got), "a row was repeated")
                        self.assertEqual(got, expected)
                        self.assertEqual(total, len(expected))

    def test_company_scope_never_leaks_other_companies(self):
        conf_company = {c.conferenceUid: (c.company or "").strip().lower() for c in self.db.query(Conference)}
        items, _ = self.walk(ConferenceFilters(company="Samsung India"), "all", limit=25)
        self.assertTrue(items)
        self.assertEqual({conf_company[i.conferenceId] for i in items}, {"samsung india"})

    def test_cancelled_trainings_are_included_like_the_original(self):
        cancelled = {c.conferenceUid for c in self.db.query(Conference) if c.conferenceStatus == "Cancelled"}
        items, _ = self.walk(ConferenceFilters(), "all", limit=50)
        self.assertTrue(cancelled & {i.conferenceId for i in items})

    def test_missing_trainee_shows_unknown_trainee(self):
        items, _ = self.walk(ConferenceFilters(), "all", limit=50)
        ghosts = [i for i in items if i.participantName == "Unknown Trainee"]
        self.assertTrue(ghosts)
        self.assertTrue(all(i.participantHoId is None and i.reportingManagerOfPromoter is None for i in ghosts))


class OrderingAndPagingTests(AttendancePageTestCase):
    def sort_key(self, sort):
        def key(item):
            att = self.raw[item.attendanceId]
            values = {
                "markedAt": att.timestamp,
                "conferenceDate": item.conferenceDate or "",
                "region": item.region or "",
                "participantName": item.participantName,
                "trainerName": item.trainerName or "",
                "attendanceStatus": item.attendanceStatus,
                "phone": item.phone or "",
                "attendanceId": item.attendanceId,
                "checkOut": att.checkOutTime or EPOCH,
            }
            return (values[sort], att.id)

        return key

    def test_sorting_both_directions_with_ties_and_blanks(self):
        oracle = self.oracle(ConferenceFilters())
        for sort in ("markedAt", "conferenceDate", "region", "participantName", "trainerName", "attendanceStatus", "phone", "attendanceId", "checkOut"):
            for descending in (True, False):
                with self.subTest(sort=sort, descending=descending):
                    expected = [i.attendanceId for i in sorted(oracle, key=self.sort_key(sort), reverse=descending)]
                    for by in ("page", "cursor"):
                        items, _ = self.walk(ConferenceFilters(), "all", sort=sort, descending=descending, limit=13, by=by)
                        self.assertEqual([i.attendanceId for i in items], expected, by)

    def test_default_order_is_newest_first_like_the_original(self):
        items, _ = self.walk(ConferenceFilters(), "all", limit=25)
        keys = [self.sort_key("markedAt")(i) for i in items]
        self.assertEqual(keys, sorted(keys, reverse=True))

    def test_page_and_cursor_walks_agree_and_cover_every_row_once(self):
        for limit in (1, 9, 50, 200):
            by_page, total_a = self.walk(ConferenceFilters(), "all", limit=limit, by="page")
            by_cursor, total_b = self.walk(ConferenceFilters(), "all", limit=limit, by="cursor")
            self.assertEqual([i.attendanceId for i in by_page], [i.attendanceId for i in by_cursor])
            self.assertEqual(total_a, total_b)
            self.assertEqual(len({i.attendanceId for i in by_page}), total_a)

    def test_jumping_to_the_last_page(self):
        expected = [i.attendanceId for i in self.walk(ConferenceFilters(), "all", limit=10)[0]]
        last = (len(expected) + 9) // 10
        response = self.page_call(ConferenceFilters(), limit=10, page=last)
        self.assertEqual([i.attendanceId for i in response.items], expected[(last - 1) * 10:])
        self.assertIsNone(response.total)

    def test_invalid_cursors_return_400(self):
        good = self.page_call(ConferenceFilters(), limit=5).nextCursor
        for bad in ("not-a-cursor", "e30=", good[:-4], "!!!"):
            with self.subTest(cursor=bad):
                with self.assertRaises(HTTPException) as caught:
                    self.page_call(ConferenceFilters(), cursor=bad)
                self.assertEqual(caught.exception.status_code, 400)
        with self.assertRaises(HTTPException) as caught:  # a cursor from another sort order
            self.page_call(ConferenceFilters(), sort="region", cursor=good)
        self.assertEqual(caught.exception.status_code, 400)


class SearchTests(AttendancePageTestCase):
    FIELDS = (
        "participantHoId", "phone", "trainerName", "trainerHoId", "region", "product", "session",
        "audienceType", "state", "district", "conferenceId", "attendanceId", "attendanceStatus", "conferenceDate",
    )

    def expected_uids(self, term, mode):
        out = []
        for i in self.oracle(ConferenceFilters(), mode):
            fields = [getattr(i, f) or "" for f in self.FIELDS]
            if i.participantName != "Unknown Trainee":
                fields.append(i.participantName)
            if any(term.lower() in f.lower() for f in fields):
                out.append(i.attendanceId)
        return sorted(out)

    def test_search_matches_the_listed_fields_and_treats_wildcards_literally(self):
        for term in ("asha", "50%", "meera_", "%", "_", "north", "present", "2026-09-0", "webinar", "delhi", "zzz-nothing"):
            for mode in ("all", "pending", "confirmed"):
                with self.subTest(term=term, mode=mode):
                    items, total = self.walk(ConferenceFilters(), mode, search=term, limit=11)
                    self.assertEqual(sorted(i.attendanceId for i in items), self.expected_uids(term, mode))
                    self.assertEqual(total, len(items))

    def test_percent_and_underscore_are_not_wildcards(self):
        # "%" alone must match only values that really contain a percent sign.
        items, _ = self.walk(ConferenceFilters(), "all", search="%", limit=50)
        self.assertTrue(all("%" in " ".join(str(v) for v in i.model_dump().values()) for i in items))


class StatementBudgetTests(AttendancePageTestCase):
    def count_statements(self, **kwargs):
        seen = []

        def listener(conn, cursor, statement, params, context, executemany):
            seen.append(statement)

        event.listen(self.engine, "before_cursor_execute", listener)
        try:
            self.page_call(ConferenceFilters(company="Samsung India"), **kwargs)
        finally:
            event.remove(self.engine, "before_cursor_execute", listener)
        return len(seen)

    def test_at_most_four_statements_and_three_after_the_first_page(self):
        self.assertLessEqual(self.count_statements(limit=50), 4)
        self.assertLessEqual(self.count_statements(limit=50, page=2), 3)
        self.assertLessEqual(self.count_statements(limit=50, search="asha", mode="confirmed"), 4)

    def test_statements_do_not_grow_with_the_page_size(self):
        self.assertEqual(self.count_statements(limit=5), self.count_statements(limit=200))


class MySqlDialectTests(unittest.TestCase):
    """SQLite cannot show MySQL's collation rules, so pin the SQL MySQL receives.
    (Found on the real database: `coalesce(attendanceUid, CAST(id AS CHAR))` made
    MySQL reject the search and the paging comparison with "Illegal mix of
    collations", while SQLite accepted it.)"""

    def test_attendance_id_fallback_is_collation_safe_on_mysql(self):
        from sqlalchemy.dialects import mysql

        from app.repositories import attendance_repository as repo

        sql = str(repo._ATTENDANCE_ID.compile(dialect=mysql.dialect())).lower()
        self.assertIn("concat('', attendance.id)", sql)
        self.assertNotIn("cast(attendance.id", sql)

    def test_every_search_and_sort_expression_compiles_for_mysql(self):
        from sqlalchemy.dialects import mysql

        from app.repositories import attendance_repository as repo

        for expr in repo.SEARCH_EXPRESSIONS + tuple(e for e, _ in repo.SORT_COLUMNS.values()):
            self.assertTrue(str(expr.compile(dialect=mysql.dialect())))


class RouteAuthorizationTests(unittest.TestCase):
    def test_route_requires_an_admin_and_applies_the_scope_filters(self):
        from app.routers.training import router

        route = next(r for r in router.routes if getattr(r, "path", "") == "/admin/attendance/page")
        called = {d.call.__name__ for d in route.dependant.dependencies}
        self.assertIn("require_admin_role", called)
        self.assertIn("get_conference_filters", called)
        self.assertNotIn("get_current_admin", called)  # the org endpoint's weaker check
        params = {q.name: q for q in route.dependant.query_params}
        self.assertEqual(params["limit"].field_info.metadata[0].ge, 1)
        self.assertEqual(params["limit"].field_info.metadata[1].le, 200)
        self.assertEqual(params["q"].field_info.metadata[0].max_length, 100)


if __name__ == "__main__":
    unittest.main()
