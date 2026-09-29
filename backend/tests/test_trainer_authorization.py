"""Trainer Flow Phase 1 - centralized trainer authorization.

Builds on the synthetic TenantWorld (tests/tenant_fixtures.py - in-memory SQLite only, never a real
database). The accounts that matter here:

    trainer1  agency trainer, ALPHA, Samsung India   owns S_N1, S_DEL, S_N1V
    trainer2  agency trainer, ALPHA, Samsung India   owns S_S1, S_BLANK
    trainer3  agency trainer, ALPHA, Other Co        owns O_N1
    adm_trainer  admin-table trainer with a trainer grant on ALPHA (owns ADM, added below)
    B_N1      a BETA conference - another tenant entirely
"""

import itertools
import unittest
from unittest.mock import patch

from app.models.admin_access import AdminAccess
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.logs_master import LogsMaster
from app.models.quiz import AssessmentResult
from app.repositories import conference_repository, dashboard_repository
from app.services import conference_access
from app.services.access_service import own_trainings_username, resolve_scope
from fastapi import HTTPException
from tests.tenant_fixtures import ALPHA, BETA, TenantWorld, uid

OWN, OTHERS = uid("S_N1"), uid("S_S1")
MARK = {"status": "Present", "reason": "Walked in late"}


class TrainerWorldTestCase(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.alpha = self.w.tenant_db[ALPHA]
        self.alpha.add(Conference(conferenceUid=uid("ADM"), company="Samsung India", zone="North Zone", region="North 1",
                                  trainerEmployeeId="adm_trainer", trainerName="Adm Trainer", conferenceDate="2026-09-20",
                                  conferenceStatus="Scheduled", status="Approved", postAssessmentUid="SUITE-1"))
        self.alpha.commit()

    def tearDown(self):
        self.w.close()

    def get(self, who, path, tenant=ALPHA, **headers):
        return self.w.client.get(path, headers={**self.w.headers(who, tenant), **headers})

    def post(self, who, path, json=None, tenant=ALPHA):
        return self.w.client.post(path, json=json, headers=self.w.headers(who, tenant))

    def set_agency_role(self, who, role):
        self.w.agency[who].role = role
        self.alpha.commit()

    def set_status(self, conference_uid, status):
        self.alpha.query(Conference).filter(Conference.conferenceUid == conference_uid).update({"conferenceStatus": status})
        self.alpha.commit()

    def own_list_keys(self, who):
        response = self.get(who, "/admin/trainings?all_sessions=true")
        self.assertEqual(response.status_code, 200, response.text)
        return self.w.conference_keys(response.json()["trainings"])


class AssignedTrainerAccess(TrainerWorldTestCase):
    def test_a_trainer_reaches_every_read_endpoint_of_their_own_training(self):
        self.set_status(OWN, "Completed")  # the report only exists once a session has ended
        for path in ("", "/performers", "/report", "/schedule-check"):
            with self.subTest(path=path):
                self.assertEqual(self.get("trainer1", f"/admin/trainings/{OWN}{path}").status_code, 200)

    def test_own_lists_contain_exactly_the_assigned_trainings(self):
        self.assertEqual(self.own_list_keys("trainer1"), {"S_N1", "S_DEL", "S_N1V"})
        attendance = self.get("trainer1", "/admin/attendance").json()
        self.assertEqual(self.w.conference_keys(attendance), {"S_N1", "S_DEL", "S_N1V"})

    def test_an_admin_table_trainer_follows_the_same_rule(self):
        self.assertEqual(self.get("adm_trainer", f"/admin/trainings/{uid('ADM')}").status_code, 200)
        self.assertEqual(self.get("adm_trainer", f"/admin/trainings/{OWN}").status_code, 404)
        self.assertEqual(self.own_list_keys("adm_trainer"), {"ADM"})

    def test_an_admin_table_trainer_can_join_their_own_live_room(self):
        # Previously denied: the room check sent every admin-table account through the company
        # scope, which a trainer grant never matches.
        found = conference_access.find_authorized_conference(
            self.alpha, self.w.admins["adm_trainer"], uid("ADM"), self.w.common, ALPHA
        )
        self.assertIsNotNone(found)


class UnassignedRecords(TrainerWorldTestCase):
    def test_another_trainers_training_is_404_on_every_endpoint(self):
        self.set_status(OTHERS, "Ongoing")
        cases = [
            ("GET", ""), ("GET", "/performers"), ("GET", "/report"), ("GET", "/schedule-check"),
            ("POST", "/advance-module"), ("POST", "/modules/stop-active"), ("POST", "/live-quiz/finish"),
            ("POST", "/live-quiz/lobby"), ("POST", f"/attendance/TR-S_S1-0"), ("DELETE", "/attendance/TR-S_S1-0"),
        ]
        for method, suffix in cases:
            with self.subTest(method=method, suffix=suffix):
                # Valid bodies, so the refusal tested is the authorization, not validation.
                body = (MARK if method == "POST" else {"reason": "x"}) if suffix.startswith("/attendance/") else None
                response = self.w.client.request(method, f"/admin/trainings/{OTHERS}{suffix}", json=body,
                                                 headers=self.w.headers("trainer1"))
                self.assertEqual(response.status_code, 404, response.text)
        # The refused DELETE really touched nothing.
        self.assertIsNotNone(
            self.alpha.query(Attendance).filter_by(conferenceUid=OTHERS, traineeUid="TR-S_S1-0").first()
        )

    def test_another_companys_training_is_404(self):
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('O_N1')}").status_code, 404)

    def test_a_nonexistent_training_looks_the_same_as_an_unassigned_one(self):
        missing = self.get("trainer1", "/admin/trainings/CONF-NOPE")
        unassigned = self.get("trainer1", f"/admin/trainings/{OTHERS}")
        self.assertEqual((missing.status_code, missing.json()), (unassigned.status_code, unassigned.json()))


class InactiveMembership(TrainerWorldTestCase):
    def test_an_agency_account_without_the_trainer_role_is_refused(self):
        # Phase 2.1: refused at authentication (get_current_admin), so every endpoint says 403.
        for role in (None, "", "manager"):
            with self.subTest(role=role):
                self.set_agency_role("trainer1", role)
                for path in (f"/admin/trainings/{OWN}", "/admin/trainings?all_sessions=true", "/admin/attendance",
                             "/admin/trainees", "/admin/profile"):
                    self.assertEqual(self.get("trainer1", path).status_code, 403, path)

    def test_a_revoked_trainer_grant_stops_the_admin_table_trainer_at_once(self):
        self.w.common.query(AdminAccess).filter(AdminAccess.admin_id == self.w.admins["adm_trainer"].id).update({"active": 0})
        self.w.common.commit()
        self.assertEqual(self.get("adm_trainer", f"/admin/trainings/{uid('ADM')}").status_code, 403)
        found = conference_access.find_authorized_conference(
            self.alpha, self.w.admins["adm_trainer"], uid("ADM"), self.w.common, ALPHA
        )
        self.assertIsNone(found)


class MissingContextFailsClosed(TrainerWorldTestCase):
    def test_no_tenant_denies_every_principal(self):
        for who in ("trainer1", "adm_trainer", "super"):
            with self.subTest(who=who):
                principal = self.w.principal(who)
                self.assertIsNone(conference_access.find_authorized_conference(self.alpha, principal, OWN, self.w.common, None))
                with self.assertRaises(HTTPException) as caught:
                    own_trainings_username(self.w.common, principal, "")
                self.assertEqual(caught.exception.status_code, 403)

    def test_no_common_database_denies_admin_table_accounts_instead_of_crashing(self):
        for who in ("adm_trainer", "super"):
            with self.subTest(who=who):
                self.assertFalse(resolve_scope(None, self.w.principal(who), ALPHA).allowed)
                self.assertIsNone(conference_access.find_authorized_conference(self.alpha, self.w.principal(who), OWN, None, ALPHA))

    def test_a_blank_trainer_username_never_matches_unassigned_trainings(self):
        self.alpha.add(Conference(conferenceUid=uid("UNASSIGNED"), company="Samsung India", trainerEmployeeId=None,
                                  conferenceDate="2026-09-20", conferenceStatus="Scheduled", status="Approved"))
        self.alpha.commit()
        for blank in (None, "", "   "):
            with self.subTest(blank=blank):
                self.assertEqual(conference_repository.list_all_for_trainer(self.alpha, blank), [])


class CrossTenantAccess(TrainerWorldTestCase):
    def test_another_tenants_training_is_404(self):
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('B_N1')}").status_code, 404)

    def test_a_tenant_header_cannot_redirect_a_trainer_token(self):
        response = self.get("trainer1", f"/admin/trainings/{uid('B_N1')}", **{"X-Tenant-ID": BETA})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{OWN}", **{"X-Tenant-ID": BETA}).status_code, 200)

    def test_a_trainer_has_no_identity_in_a_tenant_they_do_not_belong_to(self):
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('B_N1')}", tenant=BETA).status_code, 401)


class IdTampering(TrainerWorldTestCase):
    def test_marking_a_trainee_outside_the_session_is_refused_and_writes_nothing(self):
        self.set_status(OWN, "Ongoing")
        response = self.post("trainer1", f"/admin/trainings/{OWN}/attendance/TR-OTHER-TRAINER", MARK)
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(self.alpha.query(Attendance).filter_by(conferenceUid=OWN, traineeUid="TR-OTHER-TRAINER").first())
        visible = {t["traineeUid"] for t in self.get("trainer1", "/admin/trainees").json()}
        self.assertNotIn("TR-OTHER-TRAINER", visible)

    def test_marking_a_session_participant_still_works(self):
        self.set_status(OWN, "Ongoing")
        # On the roster (pre-seeded "Pending" row)...
        self.assertEqual(self.post("trainer1", f"/admin/trainings/{OWN}/attendance/TR-S_N1-1", MARK).status_code, 200)
        # ...and "Attempted": a Post Test result but no attendance row yet.
        self.alpha.add(AssessmentResult(resultUid="RES-AO", conferenceUid=OWN, traineeUid="TR-ASSIGNED-ONLY",
                                        assessmentSuiteUid="SUITE-1", attemptNumber=1, totalScore=5, maxScore=10,
                                        percentage=50, status="Submitted"))
        self.alpha.commit()
        self.assertEqual(self.post("trainer1", f"/admin/trainings/{OWN}/attendance/TR-ASSIGNED-ONLY", MARK).status_code, 200)

    def test_search_cannot_widen_trainer_conditions(self):
        """Authorization is ANDed with the search's OR group, never ORed into it."""
        scope = resolve_scope(self.w.common, self.w.agency["trainer1"], ALPHA)
        conditions = dashboard_repository.conference_authorization_conditions(scope)
        for text in ("trainer2", "South Zone", "Other Co", "CONF-S_S1", "%", "' OR 1=1 --"):
            with self.subTest(search=text):
                rows, _cursor, _total = conference_repository.list_page(self.alpha, conditions, search=text)
                self.assertTrue(all(row.trainerEmployeeId == "trainer1" for row in rows))


class TrainingCreationByTrainers(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        # TenantWorld stubs UID generation to None (its rows carry explicit UIDs); a training
        # created through the API needs a real one to build its response.
        counter = itertools.count(1)
        uid_patch = patch("app.models.uid_events.next_uid", lambda connection, prefix: f"{prefix}-NEW-{next(counter)}")
        uid_patch.start()
        self.addCleanup(uid_patch.stop)

    def payload(self, trainer, company="Samsung India"):
        return {"company": company, "trainerEmployeeId": trainer, "trainerName": trainer.title(),
                "conferenceDate": "2026-10-01", "conferenceTime": "10:00 AM"}

    def create_logs(self):
        return [row.remarks for row in self.alpha.query(LogsMaster).filter(LogsMaster.action == "CREATE_TRAINING")]

    def test_a_trainer_can_create_for_themselves(self):
        self.assertEqual(self.post("trainer1", "/admin/trainings", self.payload("trainer1")).status_code, 200)

    def test_a_trainer_can_assign_a_same_company_trainer_and_it_is_logged(self):
        response = self.post("trainer1", "/admin/trainings", self.payload("trainer2"))
        self.assertEqual(response.status_code, 200, response.text)
        logs = self.create_logs()
        self.assertEqual(len(logs), 1)
        self.assertIn("for trainer trainer2", logs[0])

    def test_a_trainer_cannot_assign_outside_their_company_or_tenant(self):
        for target in ("trainer3", "adm_trainer", "trainer_b", "nobody"):
            with self.subTest(target=target):
                response = self.post("trainer1", "/admin/trainings", self.payload(target))
                self.assertEqual(response.status_code, 403, response.text)
        self.assertEqual(self.create_logs(), [])
        self.assertEqual(self.alpha.query(Conference).filter(Conference.conferenceDate == "2026-10-01").count(), 0)

    def test_a_trainer_cannot_forge_the_training_company(self):
        response = self.post("trainer1", "/admin/trainings", self.payload("trainer1", company="Other Co"))
        self.assertEqual(response.status_code, 403)

    def test_a_trainer_without_the_trainer_role_cannot_create(self):
        self.set_agency_role("trainer1", None)
        self.assertEqual(self.post("trainer1", "/admin/trainings", self.payload("trainer1")).status_code, 403)

    def test_admin_creation_inside_the_grant_works_and_is_logged(self):
        response = self.post("coadmin", "/admin/trainings", self.payload("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(self.create_logs()), 1)


if __name__ == "__main__":
    unittest.main()
