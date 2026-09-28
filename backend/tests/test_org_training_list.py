"""The admin Training / Pending lists are now filtered in the database
(conference_repository.list_filtered) instead of loading every row and
filtering in Python. This checks the SQL version returns exactly the rows, in
exactly the order, the old Python version did - and that API responses are
gzip-compressed (but /media is left alone)."""

import random
import unittest
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.dependencies.filters import ConferenceFilters
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.conference import Conference
from app.repositories import conference_repository, dashboard_repository
from app.utils.status import title_status

ZONES = ["North Zone", "South Zone", " east zone "]
TYPES = ["Webinar", "Classroom Training", None, "Product Training"]
STATUS = ["Scheduled", "Ongoing", "Completed", "Cancelled", "completed"]
APPROVAL = ["Approved", "Pending", "Rejected", "pending", None]
TRAINERS = ["t1", "t2", "t3"]
COMPANIES = ["Samsung India", "samsung india ", "Other Co"]


class OrgTrainingListTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        rng = random.Random(3)
        base = datetime(2026, 1, 1)
        for n in range(400):
            self.db.add(
                Conference(
                    conferenceUid=f"c{n}",
                    zone=rng.choice(ZONES),
                    company=rng.choice(COMPANIES),
                    trainerEmployeeId=rng.choice(TRAINERS),
                    conferenceDate=(date(2026, 8, 1) + timedelta(days=rng.randint(0, 60))).isoformat(),
                    conferenceStatus=rng.choice(STATUS),
                    status=rng.choice(APPROVAL),
                    trainingType=rng.choice(TYPES),
                    timestamp=base + timedelta(minutes=n),  # distinct, so the order is unambiguous
                )
            )
        self.db.commit()

    def _old(self, filters, approval):
        rows = sorted(
            [c for c in self.db.query(Conference).all() if filters is None or filters.matches(c)],
            key=lambda c: c.timestamp or datetime.min,
            reverse=True,
        )
        if approval == "pending":
            rows = [c for c in rows if title_status(c.status) == "Pending"]
        elif approval == "reviewed":
            rows = [c for c in rows if title_status(c.status) != "Pending"]
        return [c.conferenceUid for c in rows]

    def _new(self, filters, approval):
        conditions = dashboard_repository.conference_conditions(filters, include_cancelled=True)
        return [c.conferenceUid for c in conference_repository.list_filtered(self.db, conditions, approval)]

    def test_same_rows_in_same_order(self):
        cases = [
            ConferenceFilters(),
            ConferenceFilters(start="2026-08-15", end="2026-09-10"),
            ConferenceFilters(zones=["east zone"], training_types=["webinar"]),
            ConferenceFilters(trainers=["t1", "t3"], company="Samsung India"),
            ConferenceFilters(zones=["mars"]),
        ]
        for filters in cases:
            for approval in (None, "pending", "reviewed"):
                with self.subTest(filters=filters, approval=approval):
                    self.assertEqual(self._old(filters, approval), self._new(filters, approval))

    def test_cancelled_trainings_stay_in_the_list(self):
        self.assertTrue(any(title_status(c.conferenceStatus) == "Cancelled" for c in self.db.query(Conference)))
        uids = self._new(ConferenceFilters(), None)
        self.assertEqual(len(uids), 400)


class PagedListTests(unittest.TestCase):
    """Walks the keyset-paged list page by page and checks the concatenated
    result is exactly the full sorted list - no row skipped, none repeated -
    for every sort column / direction, with search, and with many tied and
    blank sort values (the hard case for keyset paging)."""

    SORTS = {
        "timestamp": "timestamp",
        "conferenceDate": "conferenceDate",
        "trainerName": "trainerName",
        "zone": "zone",
        "trainingType": "trainingType",
        "conferenceStatus": "conferenceStatus",
    }

    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(bind=engine)
        self.db = sessionmaker(bind=engine)()
        rng = random.Random(11)
        base = datetime(2026, 1, 1)
        for n in range(230):
            self.db.add(
                Conference(
                    conferenceUid=f"c{n:04d}",
                    zone=rng.choice(ZONES + [None]),
                    company="Samsung India",
                    trainerName=rng.choice(["Asha", "Ravi", None, "Meera_", "50% Off"]),
                    trainerEmployeeId=rng.choice(TRAINERS),
                    conferenceDate=rng.choice(["2026-09-01", "2026-09-02", "2026-09-03", None]),
                    conferenceStatus=rng.choice(STATUS),
                    status=rng.choice(APPROVAL),
                    trainingType=rng.choice(TYPES),
                    timestamp=base + timedelta(minutes=rng.randint(0, 40)),  # lots of ties
                )
            )
        self.db.commit()

    def _walk(self, sort, descending, limit, search=None, approval=None):
        conditions = dashboard_repository.conference_conditions(ConferenceFilters(company="Samsung India"), include_cancelled=True)
        seen, cursor, pages, first_total = [], None, 0, None
        while True:
            rows, cursor, total = conference_repository.list_page(
                self.db, conditions, approval, search, sort, descending, cursor, limit
            )
            if pages == 0:
                first_total = total
            else:
                self.assertIsNone(total)  # total is only sent with the first page
            pages += 1
            seen += [c.conferenceUid for c in rows]
            self.assertLessEqual(len(rows), limit)
            if cursor is None:
                return seen, first_total
            self.assertLess(pages, 1000)

    def _expected(self, sort, descending, search=None, approval=None):
        column = self.SORTS[sort]
        rows = [c for c in self.db.query(Conference).all()]
        if approval == "pending":
            rows = [c for c in rows if title_status(c.status) == "Pending"]
        elif approval == "reviewed":
            rows = [c for c in rows if title_status(c.status) != "Pending"]
        if search:
            fields = (
                "conferenceUid trainerName trainerEmployeeId zone region sessionType trainingType trainingHub "
                "state district conferenceDate conferenceStatus status suiteTitle"
            ).split()
            rows = [c for c in rows if any(search.lower() in (getattr(c, f) or "").lower() for f in fields)]

        def key(c):
            value = getattr(c, column)
            return (value if column == "timestamp" else (value or ""), c.id)

        return [c.conferenceUid for c in sorted(rows, key=key, reverse=descending)]

    def test_every_sort_and_direction_returns_each_row_exactly_once_in_order(self):
        for sort in self.SORTS:
            for descending in (True, False):
                for limit in (1, 7, 50, 200):
                    with self.subTest(sort=sort, descending=descending, limit=limit):
                        seen, total = self._walk(sort, descending, limit)
                        self.assertEqual(seen, self._expected(sort, descending))
                        self.assertEqual(total, len(seen))
                        self.assertEqual(len(seen), len(set(seen)))

    def test_page_numbers_match_the_full_sorted_list(self):
        conditions = dashboard_repository.conference_conditions(ConferenceFilters(company="Samsung India"), include_cancelled=True)
        for sort in ("timestamp", "trainerName"):
            for descending in (True, False):
                for limit in (10, 25):
                    with self.subTest(sort=sort, descending=descending, limit=limit):
                        expected = self._expected(sort, descending)
                        seen, page, total = [], 1, None
                        while True:
                            rows, _next, page_total = conference_repository.list_page(
                                self.db, conditions, None, None, sort, descending, None, limit, page
                            )
                            if page == 1:
                                total = page_total
                            else:
                                self.assertIsNone(page_total)  # total only comes with page 1
                            if not rows:
                                break
                            seen += [c.conferenceUid for c in rows]
                            page += 1
                        self.assertEqual(seen, expected)
                        self.assertEqual(total, len(expected))
                        # jumping straight to the last page returns the tail of the list
                        last_page = (len(expected) + limit - 1) // limit
                        rows, _next, _t = conference_repository.list_page(
                            self.db, conditions, None, None, sort, descending, None, limit, last_page
                        )
                        self.assertEqual([c.conferenceUid for c in rows], expected[(last_page - 1) * limit:])

    def test_search_and_approval_split(self):
        for search in ("asha", "webinar", "2026-09-02", "east", "50%", "meera_", "no such text"):
            for approval in (None, "pending", "reviewed"):
                with self.subTest(search=search, approval=approval):
                    seen, total = self._walk("conferenceDate", False, 13, search, approval)
                    self.assertEqual(seen, self._expected("conferenceDate", False, search, approval))
                    self.assertEqual(total, len(seen))

    def test_bad_cursor_is_rejected_cleanly(self):
        from fastapi import HTTPException

        from app.services import training_service

        with self.assertRaises(HTTPException) as caught:
            # admin=None, common_db=None (defaults): resolves to a deny-everything scope
            # (access_scope_conditions), not "no restriction" - irrelevant to this test since
            # the bad cursor is rejected before the query ever runs.
            training_service.list_trainings_page(self.db, None, None, None, None, "timestamp", True, "not-a-cursor", 50)
        self.assertEqual(caught.exception.status_code, 400)


class GzipTests(unittest.TestCase):
    def test_api_json_is_compressed_and_media_is_not(self):
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        # The root route is tiny, so add a large response to prove compression.
        big = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})
        if big.status_code == 200 and len(big.content) > 1024:
            self.assertEqual(big.headers.get("content-encoding"), "gzip")
        media = client.get("/media/anything", headers={"Accept-Encoding": "gzip"})
        self.assertNotEqual(media.headers.get("content-encoding"), "gzip")


if __name__ == "__main__":
    unittest.main()
