"""Trainer Flow Phase 2 - every trainer-facing list is authorized in SQL before it is counted,
filtered, searched, sorted or paged.

Same synthetic TenantWorld as test_trainer_authorization (in-memory SQLite only). trainer1 owns
S_N1, S_DEL, S_N1V (ALPHA / Samsung India); trainer2 owns S_S1, S_BLANK; trainer3 (Other Co)
owns O_N1; B_N1 lives in BETA.
"""

import base64
import json

from app.models.admin import Admin
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentSuite
from app.models.trainee import Trainee
from app.core.security import hash_password
from app.services.access_service import norm
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

TRAINER1_TRAININGS = {"S_N1", "S_DEL", "S_N1V"}
TRAINER1_TRAINEES = {
    "TR-S_N1-0", "TR-S_N1-1", "TR-S_DEL-0", "TR-S_DEL-1", "TR-S_N1V-0", "TR-S_N1V-1",
    "TR-ASSIGNED-ONLY",  # assigned by column
    "TR-ROSTER-ONLY",    # on trainer1's roster, assigned to trainer2
}
BYPASS_SEARCHES = ("trainer2", "trainer3", "CONF-S_S1", "South", "Other Co", "TR-OTHER", "%", "_", "' OR '1'='1")


def forged_cursor(value, row_id=10**9, **extra):
    return base64.urlsafe_b64encode(json.dumps({"v": value, "id": row_id, **extra}).encode()).decode()


class ListTestCase(TrainerWorldTestCase):
    def page(self, who, path, tenant=ALPHA, **headers):
        response = self.get(who, path, tenant, **headers)
        self.assertEqual(response.status_code, 200, f"{who} {path} -> {response.text[:200]}")
        return response.json()

    def walk(self, who, path):
        """Every row of a paged list, following nextCursor two rows at a time."""
        rows, cursor = [], None
        while True:
            body = self.page(who, f"{path}&limit=2" + (f"&cursor={cursor}" if cursor else ""))
            rows += body["items"]
            cursor = body["nextCursor"]
            if not cursor:
                return rows

    def set_approval(self, key, status):
        self.alpha.query(Conference).filter(Conference.conferenceUid == uid(key)).update({"status": status})
        self.alpha.commit()


class TrainingListAndPendingTrainingList(ListTestCase):
    PAGE = "/admin/trainings/page?limit=200"

    def test_only_the_trainers_own_trainings_are_listed_and_counted(self):
        body = self.page("trainer1", self.PAGE)
        self.assertEqual(self.w.conference_keys(body["items"]), TRAINER1_TRAININGS)
        self.assertEqual(body["total"], 3)

    def test_approved_and_pending_splits_stay_inside_the_trainers_own_trainings(self):
        self.set_approval("S_N1", "Approved")
        self.set_approval("S_S1", "Approved")  # someone else's approved training must not appear
        approved = self.page("trainer1", self.PAGE + "&approval=approved")
        pending = self.page("trainer1", self.PAGE + "&approval=pending")
        self.assertEqual((self.w.conference_keys(approved["items"]), approved["total"]), ({"S_N1"}, 1))
        self.assertEqual((self.w.conference_keys(pending["items"]), pending["total"]), ({"S_DEL", "S_N1V"}, 2))

    def test_an_admin_table_trainer_sees_only_their_own(self):
        self.assertEqual(self.w.conference_keys(self.page("adm_trainer", self.PAGE)["items"]), {"ADM"})

    def test_filters_search_and_cursors_cannot_widen_the_list(self):
        for query in ("&trainers=trainer2", "&zones=south%20zone", "&regions=south%201"):
            with self.subTest(query=query):
                body = self.page("trainer1", self.PAGE + query)
                self.assertEqual((body["items"], body["total"]), ([], 0))
        for text in BYPASS_SEARCHES:
            with self.subTest(search=text):
                body = self.page("trainer1", self.PAGE + f"&q={text}")
                self.assertLessEqual(self.w.conference_keys(body["items"]), TRAINER1_TRAININGS)
                self.assertEqual(body["total"], len(body["items"]))
        forged = self.page("trainer1", self.PAGE + f"&cursor={forged_cursor('2099-01-01T00:00:00')}")
        self.assertLessEqual(self.w.conference_keys(forged["items"]), TRAINER1_TRAININGS)
        self.assertIsNone(forged["total"])

    def test_every_page_walked_by_cursor_is_the_authorized_set_exactly_once(self):
        rows = self.walk("trainer1", "/admin/trainings/page?sort=conferenceUid&dir=asc")
        self.assertEqual(sorted(r["conferenceUid"] for r in rows), sorted(uid(k) for k in TRAINER1_TRAININGS))

    def test_another_tenant_never_appears_even_with_a_tenant_header(self):
        body = self.page("trainer1", self.PAGE, **{"X-Tenant-ID": BETA})
        self.assertEqual(self.w.conference_keys(body["items"]), TRAINER1_TRAININGS)

    def test_an_account_without_the_trainer_role_is_refused(self):
        self.set_agency_role("trainer1", None)
        self.assertEqual(self.get("trainer1", self.PAGE).status_code, 403)

    def test_admin_lists_are_unchanged(self):
        body = self.page("coadmin", self.PAGE)
        self.assertEqual(self.w.conference_keys(body["items"]), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V", "ADM"})


class SessionsAndHomeAgenda(ListTestCase):
    """GET /admin/trainings - the trainer Home and the Sessions screen (all / today / completed /
    upcoming / ongoing are client-side views over this same authorized set)."""

    def test_all_sessions_and_date_ranges_stay_inside_the_trainers_own_trainings(self):
        for query in ("all_sessions=true", "start=2026-01-01&end=2026-12-31", "start=2026-09-20&end=2026-09-20"):
            with self.subTest(query=query):
                body = self.page("trainer1", f"/admin/trainings?{query}")
                self.assertEqual(self.w.conference_keys(body["trainings"]), TRAINER1_TRAININGS)
                self.assertEqual(body["totalSessions"], 3)

    def test_counts_and_headcount_ignore_other_trainers_sessions(self):
        self.set_status(uid("S_S1"), "Completed")
        self.set_status(uid("S_N1"), "Completed")
        body = self.page("trainer1", "/admin/trainings?all_sessions=true")
        self.assertEqual(body["completed"], 1)
        self.assertEqual(self.w.conference_keys(body["recentCompleted"]), {"S_N1"})

    def test_admin_filter_params_cannot_widen_a_trainers_sessions(self):
        body = self.page("trainer1", "/admin/trainings?all_sessions=true&trainers=trainer2&zones=south%20zone")
        self.assertEqual(self.w.conference_keys(body["trainings"]), TRAINER1_TRAININGS)

    def test_the_org_wide_view_is_refused_to_trainers(self):
        self.assertEqual(self.get("trainer1", "/admin/trainings?org=true&all_sessions=true").status_code, 403)


class TraineeListAndPendingTraineeList(ListTestCase):
    PAGE = "/admin/trainees/page?limit=200"

    def keys(self, items):
        return {t["traineeUid"] for t in items}

    def test_only_assigned_and_rostered_trainees_are_listed_and_counted(self):
        body = self.page("trainer1", self.PAGE)
        self.assertEqual(self.keys(body["items"]), TRAINER1_TRAINEES)
        self.assertEqual(body["total"], len(TRAINER1_TRAINEES))

    def test_the_paged_list_matches_the_full_list_for_every_account(self):
        for who in ("trainer1", "trainer2", "adm_trainer", "coadmin", "coord", "super", "ungranted_trainer"):
            if who == "ungranted_trainer":
                self.set_agency_role("trainer3", "manager")
                who = "trainer3"
            with self.subTest(who=who):
                full = self.get(who, "/admin/trainees")
                paged = self.get(who, self.PAGE)
                if full.status_code != 200:
                    self.assertEqual(paged.status_code, full.status_code)
                    continue
                self.assertEqual(self.keys(paged.json()["items"]), self.keys(full.json()))

    def test_pending_mode_is_the_pending_subset_of_the_authorized_set(self):
        self.alpha.query(Trainee).filter(Trainee.traineeUid.in_(["TR-S_N1-0", "TR-OTHER-TRAINER"])).update(
            {"status": "Approved"}, synchronize_session=False
        )
        self.alpha.commit()
        body = self.page("trainer1", self.PAGE + "&mode=pending")
        self.assertEqual(self.keys(body["items"]), TRAINER1_TRAINEES - {"TR-S_N1-0"})
        self.assertEqual(body["total"], len(TRAINER1_TRAINEES) - 1)

    def test_search_sort_and_cursors_cannot_widen_the_list(self):
        for text in BYPASS_SEARCHES + ("Person S_S1", "HO-OT", "9100000003"):
            with self.subTest(search=text):
                body = self.page("trainer1", self.PAGE + f"&q={text}")
                self.assertLessEqual(self.keys(body["items"]), TRAINER1_TRAINEES)
                self.assertEqual(body["total"], len(body["items"]))
        for sort in ("name", "trainerName", "status", "district"):
            with self.subTest(sort=sort):
                rows = self.walk("trainer1", f"/admin/trainees/page?sort={sort}&dir=asc")
                self.assertEqual(sorted(r["traineeUid"] for r in rows), sorted(TRAINER1_TRAINEES))
        forged = self.page("trainer1", self.PAGE + f"&cursor={forged_cursor('2099-01-01T00:00:00')}")
        self.assertLessEqual(self.keys(forged["items"]), TRAINER1_TRAINEES)

    def test_a_malformed_cursor_is_a_clean_400(self):
        self.assertEqual(self.get("trainer1", self.PAGE + "&cursor=not-a-cursor").status_code, 400)

    def test_another_tenant_never_appears(self):
        body = self.page("trainer1", self.PAGE, **{"X-Tenant-ID": BETA})
        self.assertFalse(any(t.startswith("TR-B_") for t in self.keys(body["items"])))

    def test_admin_scope_is_unchanged(self):
        body = self.page("coord", self.PAGE)
        self.assertTrue(body["items"])
        self.assertTrue(all(norm(t["zone"]) == "north zone" and norm(t["company"]) == "samsung india" for t in body["items"]))


class AttendanceLists(ListTestCase):
    PAGE = "/admin/attendance/page?limit=200"

    def test_all_pending_and_confirmed_are_the_trainers_own_attendance(self):
        own_rows = self.alpha.query(Attendance).filter(Attendance.conferenceUid.in_([uid(k) for k in TRAINER1_TRAININGS]))
        present = sum(1 for a in own_rows if a.status == "Present")
        expected = {"all": own_rows.count(), "confirmed": present, "pending": own_rows.count() - present}
        for mode, total in expected.items():
            with self.subTest(mode=mode):
                body = self.page("trainer1", self.PAGE + f"&mode={mode}")
                self.assertEqual(self.w.conference_keys(body["items"]), TRAINER1_TRAININGS)
                self.assertEqual(body["total"], total)
                self.assertTrue(all(i["marked"] == (mode == "confirmed") for i in body["items"]) or mode == "all")

    def test_tallies_only_count_the_trainers_own_trainings(self):
        # TR-S_S1-0 attends trainer2's S_S1 (from the fixture) and now trainer1's S_N1 too.
        self.alpha.add(Attendance(attendanceUid="ATT-X", conferenceUid=uid("S_N1"), traineeUid="TR-S_S1-0", status="Present"))
        self.alpha.commit()
        rows = [i for i in self.page("trainer1", self.PAGE)["items"] if i["conferenceId"] == uid("S_N1")]
        crossover = next(i for i in rows if i["participantHoId"] == "HO-S_S1-0")
        self.assertEqual(crossover["trainerTrainingsTotal"], 1)

    def test_filters_search_and_cursors_cannot_widen_the_list(self):
        for query in ("&trainers=trainer2", "&zones=south%20zone"):
            with self.subTest(query=query):
                self.assertEqual(self.page("trainer1", self.PAGE + query)["total"], 0)
        for text in BYPASS_SEARCHES:
            with self.subTest(search=text):
                body = self.page("trainer1", self.PAGE + f"&q={text}")
                self.assertLessEqual(self.w.conference_keys(body["items"]), TRAINER1_TRAININGS)
                self.assertEqual(body["total"], len(body["items"]))
        cursor = forged_cursor("2099-01-01T00:00:00", s="markedAt")
        forged = self.page("trainer1", self.PAGE + f"&cursor={cursor}")
        self.assertLessEqual(self.w.conference_keys(forged["items"]), TRAINER1_TRAININGS)

    def test_another_tenant_never_appears(self):
        body = self.page("trainer1", self.PAGE, **{"X-Tenant-ID": BETA})
        self.assertEqual(self.w.conference_keys(body["items"]), TRAINER1_TRAININGS)

    def test_an_account_without_the_trainer_role_is_refused(self):
        self.set_agency_role("trainer1", "manager")
        self.assertEqual(self.get("trainer1", self.PAGE).status_code, 403)


class AssessmentsAndResults(ListTestCase):
    def test_question_banks_are_tenant_isolated(self):
        self.alpha.add(AssessmentSuite(assessmentSuiteUid="SUITE-A", examTitle="Alpha bank", status="Approved"))
        self.w.tenant_db[BETA].add(AssessmentSuite(assessmentSuiteUid="SUITE-B", examTitle="Beta bank", status="Approved"))
        self.alpha.commit()
        self.w.tenant_db[BETA].commit()
        suites = {s["assessmentSuiteUid"] for s in self.page("trainer1", "/admin/assessment-suites")}
        self.assertIn("SUITE-A", suites)
        self.assertNotIn("SUITE-B", suites)

    def test_results_only_surface_through_the_trainers_own_trainings(self):
        self.set_status(uid("S_S1"), "Completed")
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('S_S1')}/performers").status_code, 404)
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('S_S1')}/report").status_code, 404)
        scored = [i for i in self.page("trainer1", "/admin/attendance/page?limit=200")["items"] if i["postTestScore"]]
        self.assertEqual(self.w.conference_keys(scored), TRAINER1_TRAININGS)


class TrainerDropdowns(ListTestCase):
    def setUp(self):
        super().setUp()
        # An admin-table trainer who belongs to BETA only - the shared admin table must not leak them into ALPHA.
        beta_trainer = Admin(adminUid="a-beta_trainer", username="beta_trainer", name="Beta Trainer",
                             password=hash_password(PASSWORD), role="trainer", company="Samsung India")
        self.w.common.add(beta_trainer)
        self.w.common.flush()
        self.w.grant(beta_trainer, "trainer", BETA)
        self.w.common.commit()

    def options(self, who, query=""):
        return {o["value"] for o in self.page(who, f"/admin/trainers{query}")}

    def test_a_trainer_sees_only_their_own_companys_trainers(self):
        self.assertEqual(self.options("trainer1"), {"trainer1", "trainer2"})
        self.assertEqual(self.options("trainer3"), {"trainer3"})
        self.assertEqual(self.options("trainer1", "?company=Other%20Co"), set())

    def test_a_trainer_without_a_company_sees_only_themselves(self):
        self.assertEqual(self.options("adm_trainer"), {"adm_trainer"})

    def test_an_admin_sees_this_tenants_trainers_only(self):
        self.assertEqual(self.options("super"), {"adm_trainer", "trainer1", "trainer2", "trainer3"})

    def test_a_non_trainer_account_is_refused(self):
        self.set_agency_role("trainer1", "manager")
        self.assertEqual(self.get("trainer1", "/admin/trainers").status_code, 403)

    def test_trainer_name_lookup_is_tenant_bound(self):
        self.assertEqual(self.get("super", "/admin/trainers/beta_trainer").status_code, 404)
        self.assertEqual(self.get("super", "/admin/trainers/adm_trainer").status_code, 200)


class AdminPendingApprovalsUseTheGrant(ListTestCase):
    """GET /admin/trainings/pending and the org views used the legacy company/zone columns, which
    showed everything when an admin's own `company` was blank. They now follow the grant."""

    def setUp(self):
        super().setUp()
        blank = Admin(adminUid="a-blankco", username="blankco", name="Blank Co", password=hash_password(PASSWORD),
                      role="admin", company=None)
        self.w.common.add(blank)
        self.w.common.flush()
        self.w.grant(blank, "coordinator", ALPHA, "Samsung India", zone="North Zone")
        self.w.common.commit()
        self.w.admins["blankco"] = blank

    def test_pending_approvals_follow_the_grant_not_the_company_column(self):
        keys = {i["conferenceUid"].removeprefix("CONF-") for i in self.page("blankco", "/admin/trainings/pending")}
        self.assertEqual(keys, {"S_N1", "S_DEL", "S_N1V"})

    def test_org_views_follow_the_grant(self):
        trainings = self.page("blankco", "/admin/trainings?org=true&all_sessions=true")["trainings"]
        self.assertEqual(self.w.conference_keys(trainings), {"S_N1", "S_DEL", "S_N1V", "ADM"})  # ADM: Samsung / North too
        attendance = self.page("blankco", "/admin/attendance?org=true")
        self.assertEqual(self.w.conference_keys(attendance), {"S_N1", "S_DEL", "S_N1V"})
