"""Phase 3 - standardized server-side pagination (repositories/keyset.py) across the trainer lists:
Training / Pending Training / Sessions, Trainee / Pending Trainee, Attendance x3.

Synthetic TenantWorld (in-memory SQLite) only. trainer1 gets 25 extra trainings (and a trainee on
each) so every list spans several pages.
"""

import re
from datetime import datetime

from sqlalchemy import event, select

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import keyset
from tests.tenant_fixtures import ALPHA, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

EXTRA = 25
TRAINER1_BASE = {"S_N1", "S_DEL", "S_N1V"}


class PagingTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        for n in range(EXTRA):
            key = f"P{n:02d}"
            self.alpha.add(Conference(
                conferenceUid=uid(key), company="Samsung India", zone="North Zone", region="North 1",
                trainerEmployeeId="trainer1", trainerName="Trainer1", conferenceDate=f"2026-10-{(n % 28) + 1:02d}",
                conferenceTime="10:00 AM", conferenceStatus="Scheduled", status="Approved",
                trainingHub="Hub A" if n % 2 else "Hub B", trainingType="Webinar" if n % 3 else "Classroom",
                suiteTitle=f"Paged {key}", timestamp=datetime(2026, 9, 1, 8, n),
            ))
            tuid = f"TR-PG-{n:02d}"
            self.alpha.add(Trainee(traineeUid=tuid, name=f"Paged Person {n:02d}", email=f"pg{n}@example.test",
                                   phone=9_200_000_000 + n, username=f"pg{n}", company="Samsung India",
                                   zone="North Zone", region="North 1", trainerEmployeeId="trainer1"))
            self.alpha.add(Attendance(attendanceUid=f"ATT-PG-{n:02d}", conferenceUid=uid(key), traineeUid=tuid,
                                      status="Present" if n % 2 else "Pending", timestamp=datetime(2026, 9, 2, 8, n)))
        self.alpha.commit()

    def get_page(self, who, path):
        response = self.get(who, path)
        self.assertEqual(response.status_code, 200, f"{path} -> {response.text[:200]}")
        return response.json()

    def walk_pages(self, who, path, key, limit):
        """Every numbered page; checks the metadata on each and returns the item keys in order."""
        first = self.get_page(who, f"{path}&limit={limit}&page=1")
        total, total_pages = first["total"], first["totalPages"]
        self.assertEqual(total_pages, -(-total // limit))
        keys = [item[key] for item in first["items"]]
        for number in range(2, total_pages + 1):
            body = self.get_page(who, f"{path}&limit={limit}&page={number}")
            self.assertEqual((body["page"], body["pageSize"], body["total"], body["totalPages"]), (number, limit, total, total_pages))
            self.assertLessEqual(len(body["items"]), limit)
            keys += [item[key] for item in body["items"]]
        self.assertEqual(len(keys), total)
        self.assertEqual(len(keys), len(set(keys)), "a row appeared on two pages")
        return keys


LISTS = {
    "trainings": ("/admin/trainings/page?sort=conferenceUid&dir=asc", "conferenceUid"),
    "trainees": ("/admin/trainees/page?sort=traineeUid&dir=asc", "traineeUid"),
    "attendance": ("/admin/attendance/page?sort=attendanceId&dir=asc", "attendanceId"),
}


class EveryListPagesCorrectly(PagingTestCase):
    def test_pages_are_ordered_complete_and_never_overlap(self):
        for name, (path, key) in LISTS.items():
            with self.subTest(list=name):
                keys = self.walk_pages("trainer1", path, key, limit=7)
                self.assertEqual(keys, sorted(keys))
                self.assertGreater(len(keys), 7 * 3)

    def test_page_one_and_two_are_the_first_two_slices_of_the_full_order(self):
        for name, (path, key) in LISTS.items():
            with self.subTest(list=name):
                everything = [i[key] for i in self.get_page("trainer1", f"{path}&limit=200")["items"]]
                page1 = [i[key] for i in self.get_page("trainer1", f"{path}&limit=5&page=1")["items"]]
                page2 = [i[key] for i in self.get_page("trainer1", f"{path}&limit=5&page=2")["items"]]
                self.assertEqual(page1 + page2, everything[:10])

    def test_totals_are_the_authorized_count_on_every_page(self):
        # trainer1: own 3 fixture trainings + the 25 added; trainer2 sees none of the added ones.
        self.assertEqual(self.get_page("trainer1", LISTS["trainings"][0] + "&limit=5&page=3")["total"], len(TRAINER1_BASE) + EXTRA)
        trainer2 = self.get_page("trainer2", LISTS["trainings"][0] + "&limit=5")
        self.assertFalse(any(i["conferenceUid"].startswith("CONF-P") for i in trainer2["items"]))
        self.assertEqual(trainer2["total"], 2)

    def test_search_and_filters_hold_across_pages(self):
        path = "/admin/trainings/page?sort=conferenceUid&dir=asc&q=paged&training_types=webinar"
        keys = self.walk_pages("trainer1", path, "conferenceUid", limit=4)
        expected = sorted(uid(f"P{n:02d}") for n in range(EXTRA) if n % 3)
        self.assertEqual(keys, expected)
        pending = self.walk_pages("trainer1", "/admin/attendance/page?mode=pending&sort=attendanceId&dir=asc", "attendanceId", limit=4)
        self.assertTrue(all(not item.startswith("ATT-PG-") or int(item[-2:]) % 2 == 0 for item in pending))

    def test_a_cursor_walk_matches_the_numbered_pages(self):
        path, key = LISTS["trainings"]
        numbered = self.walk_pages("trainer1", path, key, limit=6)
        walked, cursor = [], None
        while True:
            body = self.get_page("trainer1", f"{path}&limit=6" + (f"&cursor={cursor}" if cursor else ""))
            if cursor:
                self.assertIsNone(body["total"])  # continuations skip the count
            walked += [i[key] for i in body["items"]]
            cursor = body["nextCursor"]
            if not cursor:
                break
        self.assertEqual(walked, numbered)


class PageRequestValidation(PagingTestCase):
    def test_bad_page_numbers_and_sizes_are_422_everywhere(self):
        for name, (path, _) in LISTS.items():
            for query in ("&limit=0", "&limit=201", "&page=0", "&page=-1", "&page=100001", "&limit=abc"):
                with self.subTest(list=name, query=query):
                    self.assertEqual(self.get("trainer1", path + query).status_code, 422)

    def test_a_page_past_the_end_is_empty_but_still_reports_the_total(self):
        for name, (path, _) in LISTS.items():
            with self.subTest(list=name):
                body = self.get_page("trainer1", f"{path}&limit=10&page=999")
                self.assertEqual(body["items"], [])
                self.assertEqual(body["page"], 999)
                self.assertGreater(body["total"], 0)
                self.assertEqual(body["totalPages"], -(-body["total"] // 10))

    def test_an_empty_list_has_zero_pages(self):
        body = self.get_page("trainer1", "/admin/trainings/page?q=nothing-matches-this")
        self.assertEqual((body["items"], body["total"], body["totalPages"], body["nextCursor"]), ([], 0, 0, None))

    def test_a_cursor_only_works_with_the_sort_it_was_issued_for(self):
        body = self.get_page("trainer1", "/admin/trainings/page?sort=conferenceUid&dir=asc&limit=3")
        self.assertEqual(self.get("trainer1", f"/admin/trainings/page?sort=zone&limit=3&cursor={body['nextCursor']}").status_code, 400)


class DatabaseDoesThePaging(PagingTestCase):
    def statements(self, path):
        seen = []
        listener = lambda conn, cursor, statement, params, context, many: seen.append(statement)
        event.listen(self.w.alpha_engine, "before_cursor_execute", listener)
        try:
            self.get_page("trainer1", path)
        finally:
            event.remove(self.w.alpha_engine, "before_cursor_execute", listener)
        return seen

    def test_the_row_query_is_limited_and_offset_in_sql(self):
        for table, path in (("conference", "/admin/trainings/page?limit=5&page=3"),
                            ("trainee", "/admin/trainees/page?limit=5&page=3"),
                            ("attendance", "/admin/attendance/page?limit=5&page=3")):
            with self.subTest(table=table):
                row_queries = [s for s in self.statements(path)
                               if re.search(rf"FROM {table}\b", s) and "ORDER BY" in s and "count(" not in s.lower()]
                self.assertEqual(len(row_queries), 1, row_queries)
                self.assertRegex(row_queries[0], r"LIMIT \? OFFSET \?")

    def test_no_query_reads_a_table_without_a_limit_or_a_page_bound(self):
        # Every conference/trainee SELECT is the counted page query, a COUNT, or bounded by the
        # page's own ids (IN (...)) - never a full read of the table.
        for statement in self.statements("/admin/trainings/page?limit=5&page=2"):
            if not statement.lstrip().upper().startswith("SELECT") or not re.search(r"FROM (conference|trainee)\b", statement):
                continue
            with self.subTest(statement=statement[:120]):
                self.assertTrue("LIMIT" in statement or "count(" in statement.lower() or " IN (" in statement)

    def test_the_shared_helper_clamps_the_page_size_whatever_the_caller_asks(self):
        # The routes already refuse limit > 200 (422); the helper enforces it again for any caller.
        order = keyset.SortOrder.keyset("id", Conference.id, Conference.id, descending=False, cursor_value=lambda r: r.id)
        for asked, applied in ((10_000, keyset.MAX_PAGE_SIZE), (0, 1), (-5, 1)):
            with self.subTest(asked=asked):
                page = keyset.paginate(self.alpha, select(Conference), order, cursor=None, limit=asked, page=1)
                self.assertEqual(page.page_size, applied)
                self.assertLessEqual(len(page.rows), applied)


class SessionsScreen(PagingTestCase):
    """GET /admin/trainings/page?sort=session - the trainer Sessions screen, paged in SQL."""

    SESSIONS = [
        ("SES-LIVE", "2026-10-10", "02:00 PM", "Ongoing", "Hub Z", None),
        ("SES-UP1", "2026-10-09", "01:00 PM", "Scheduled", "Hub Z", None),
        ("SES-UP2", "2026-10-09", "09:00 AM", "Scheduled", None, "Kerala"),   # no hub: location = state
        ("SES-UP3", "2026-10-09", "10:00 AM", "Scheduled", "Hub Z", None),
        ("SES-NODATE", None, None, "Scheduled", "Hub Z", None),
        ("SES-DONE1", "2026-08-01", "10:00 AM", "Completed", "Hub Z", None),
        ("SES-DONE2", "2026-08-05", "09:00 AM", "Completed", "Hub Z", None),
    ]

    def setUp(self):
        super().setUp()
        for key, date, time, status, hub, state in self.SESSIONS:
            self.alpha.add(Conference(conferenceUid=key, company="Samsung India", trainerEmployeeId="trainer3",
                                      conferenceDate=date, conferenceTime=time, conferenceStatus=status,
                                      status="Approved", trainingHub=hub, state=state, trainingType="Workshop"))
        self.alpha.commit()

    def sessions(self, query="", who="trainer3", limit=50):
        return [i["conferenceUid"] for i in self.get_page(who, f"/admin/trainings/page?sort=session&limit={limit}{query}")["items"]]

    def test_live_then_upcoming_soonest_then_completed_newest(self):
        order = [k for k in self.sessions() if k.startswith("SES-")]
        self.assertEqual(order, ["SES-LIVE", "SES-UP2", "SES-UP3", "SES-UP1", "SES-NODATE", "SES-DONE2", "SES-DONE1"])

    def test_the_grouped_order_pages_without_gaps_or_repeats(self):
        everything = self.sessions()
        paged = []
        for number in range(1, 5):
            paged += self.sessions(f"&page={number}", limit=2)
        self.assertEqual(paged, everything[:8])

    def test_the_tabs_and_filters_are_applied_in_sql(self):
        self.assertEqual(self.sessions("&on_date=2026-10-09"), ["SES-UP2", "SES-UP3", "SES-UP1"])
        self.assertEqual(self.sessions("&status=completed"), ["SES-DONE2", "SES-DONE1"])
        self.assertEqual(self.sessions("&location=Kerala"), ["SES-UP2"])
        self.assertEqual(set(self.sessions("&location=Hub%20Z&status=completed")), {"SES-DONE1", "SES-DONE2"})
        self.assertEqual(self.get("trainer3", "/admin/trainings/page?sort=session&on_date=09-10-2026").status_code, 422)

    def test_the_grouped_order_refuses_a_cursor(self):
        self.assertEqual(self.get("trainer3", "/admin/trainings/page?sort=session&cursor=abc").status_code, 400)

    def test_another_trainer_never_sees_these_sessions(self):
        self.assertFalse(any(k.startswith("SES-") for k in self.sessions(who="trainer1", limit=200)))

    def test_filter_options_come_only_from_the_trainers_own_trainings(self):
        mine = self.get_page("trainer3", "/admin/trainings/facets")
        self.assertIn("Hub Z", mine["trainingHubs"])
        self.assertNotIn("Hub A", mine["trainingHubs"])  # trainer1's
        self.assertEqual(mine["trainingTypes"], ["Webinar", "Workshop"])  # O_N1 (fixture) + these sessions
        theirs = self.get_page("trainer1", "/admin/trainings/facets")
        self.assertNotIn("Hub Z", theirs["trainingHubs"])
        self.assertNotIn("Workshop", theirs["trainingTypes"])
