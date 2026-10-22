"""Sign-in without a company code, Phase 2 (user, 2026-10-19): the central user registry says which
company a trainee or trainer belongs to, their company record decides; an admin's grants say which
company - several mean choosing, with a ticket. A sign-in that names a company (an older app) works
exactly as before.

Synthetic TenantWorld (in-memory SQLite) only - no real database is touched."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from jose import jwt

from app.core import rate_limit
from app.core.config import settings
from app.core.security import hash_password
from app.database.tenant import tenant_manager
from app.models import uid_events
from app.models.agency_team import AgencyTeam
from app.models.common.tenant_registry import Tenant
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.services import admin_service, sign_in_service, trainee_service
from app.services import user_registry_service as registry_service
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD
from tests.test_trainer_authorization import TrainerWorldTestCase

SAMSUNG = "Samsung India"


class SignInTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        rate_limit.reset()
        self.addCleanup(rate_limit.reset)
        sign_in_service._not_found.clear()
        self.addCleanup(sign_in_service._not_found.clear)
        self.common = self.w.common
        self.beta = self.w.tenant_db[BETA]
        self.sync_all()

    def sync_all(self):
        registry_service.reconcile_tenant(self.common, self.alpha, ALPHA)
        registry_service.reconcile_tenant(self.common, self.beta, BETA)

    def trainee_sign_in(self, identifier, password=PASSWORD, headers=None):
        return self.w.client.post("/trainees/login", json={"identifier": str(identifier), "password": password}, headers=headers or {})

    def staff_sign_in(self, username, password=PASSWORD, headers=None):
        return self.w.client.post("/admin/login", json={"username": username, "password": password}, headers=headers or {})

    def claims(self, response):
        return jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def entry(self, user_uid):
        self.common.expire_all()
        return self.common.query(UserRegistry).filter(UserRegistry.user_uid == user_uid).one()

    def trainee(self, db, user_uid):
        return db.query(Trainee).filter(Trainee.traineeUid == user_uid).one()


class TraineesSignInWithoutACompanyCode(SignInTestCase):
    def test_any_of_their_ids_signs_them_into_their_company(self):
        for identifier in ("user1", "HO-S_N1-0", "tr-s_n1-0", 9_000_000_001):
            with self.subTest(identifier=identifier):
                response = self.trainee_sign_in(identifier)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual((self.claims(response)["tenant_id"], self.claims(response)["sub"]), (ALPHA, "9000000001"))
                self.assertEqual(response.json()["company"], {"tenantId": ALPHA, "companyName": SAMSUNG})

    def test_another_company_s_trainee_lands_in_their_own_company(self):
        response = self.trainee_sign_in("user13")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.claims(response)["tenant_id"], BETA)
        self.assertEqual(response.json()["trainee"]["traineeUid"], "TR-B_N1-0")

    def test_the_token_s_company_wins_over_any_company_a_request_names(self):
        token = self.trainee_sign_in("user13").json()["access_token"]
        response = self.w.client.get("/tenants/current", headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": ALPHA})
        self.assertEqual(response.json()["tenantId"], BETA)

    def test_a_wrong_password_and_an_unknown_id_get_the_same_answer(self):
        for identifier, password in (("user1", "wrong"), ("nobody-at-all", PASSWORD)):
            with self.subTest(identifier=identifier):
                response = self.trainee_sign_in(identifier, password)
                self.assertEqual((response.status_code, response.json()["detail"]), (401, trainee_service.LOGIN_FAILED))

    def test_a_disabled_entry_can_t_sign_in(self):
        self.entry("TR-S_N1-0").status = "disabled"
        self.common.commit()
        self.assertEqual(self.trainee_sign_in("user1").status_code, 401)

    def test_a_pending_entry_whose_company_record_is_saved_is_finished_and_signs_in(self):
        # A registration whose last step failed (user, 2026-10-20: entries in both databases).
        self.entry("TR-S_N1-0").status = "pending"
        self.common.commit()
        self.assertEqual(self.trainee_sign_in("user1").status_code, 200)
        self.assertEqual(self.entry("TR-S_N1-0").status, "active")

    def test_an_entry_whose_company_record_is_gone_is_refused_and_disabled(self):
        self.alpha.delete(self.trainee(self.alpha, "TR-S_N1-1"))
        self.alpha.commit()
        self.assertEqual(self.trainee_sign_in("user2").status_code, 401)
        self.assertEqual(self.entry("TR-S_N1-1").status, "disabled")

    def test_a_suspended_or_unregistered_company_can_t_be_signed_in_to(self):
        self.common.query(Tenant).filter_by(tenant_uid=ALPHA).update({"status": "suspended"})
        self.common.commit()
        tenant_manager.clear_status_cache()
        self.assertEqual(self.trainee_sign_in("user1").status_code, 401)

        self.entry("TR-B_N1-0").tenant_uid = "GHOST"   # a mapping to a company nobody registered
        self.common.commit()
        self.assertEqual(self.trainee_sign_in("user13").status_code, 401)

    def test_a_password_changed_in_the_company_works_at_once_and_the_old_one_stops(self):
        self.trainee(self.alpha, "TR-S_N1-0").password = hash_password("Changed-Elsewhere-1")
        self.alpha.commit()
        self.assertEqual(self.trainee_sign_in("user1").status_code, 401)
        self.assertEqual(self.trainee_sign_in("user1", "Changed-Elsewhere-1").status_code, 200)
        self.assertEqual(self.entry("TR-S_N1-0").password_hash, self.trainee(self.alpha, "TR-S_N1-0").password)

    def test_a_username_changed_in_the_company_stops_answering_and_the_new_one_works(self):
        self.trainee(self.alpha, "TR-S_N1-0").username = "renamed"
        self.alpha.commit()
        self.assertEqual(self.trainee_sign_in("user1").status_code, 401)
        self.assertEqual(self.trainee_sign_in("renamed").status_code, 200)

    def test_an_older_app_that_sends_the_company_code_signs_in_as_before(self):
        response = self.trainee_sign_in("user1", headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["company"])


class TwoPeopleSharingAPhone(SignInTestCase):
    def setUp(self):
        super().setUp()
        self.beta.add(Trainee(traineeUid="TR-BETA-TWIN", name="Twin", email="twin@example.test", phone=9_000_000_001,
                              username="beta.twin", employee_id="HO-TWIN", password=hash_password(PASSWORD)))
        self.beta.commit()
        registry_service.reconcile_tenant(self.common, self.beta, BETA)

    def test_a_password_that_opens_both_asks_for_the_ho_id_or_username(self):
        response = self.trainee_sign_in(9_000_000_001)
        self.assertEqual((response.status_code, response.json()["detail"]), (409, sign_in_service.SHARED_PHONE))
        self.assertEqual(self.claims(self.trainee_sign_in("beta.twin"))["tenant_id"], BETA)
        self.assertEqual(self.claims(self.trainee_sign_in("HO-TWIN"))["tenant_id"], BETA)
        self.assertEqual(self.claims(self.trainee_sign_in("user1"))["tenant_id"], ALPHA)

    def test_a_password_that_opens_only_one_signs_into_it(self):
        self.trainee(self.beta, "TR-BETA-TWIN").password = hash_password("Another-Secret-2")
        self.beta.commit()
        response = self.trainee_sign_in(9_000_000_001)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.claims(response)["tenant_id"], ALPHA)

    def test_from_a_training_qr_code_its_company_says_which_account(self):
        for company in (ALPHA, BETA):
            with self.subTest(company=company):
                response = self.w.client.post(
                    "/trainees/login", json={"identifier": "9000000001", "password": PASSWORD, "company": company}
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(self.claims(response)["tenant_id"], company)


class SigningInFromATrainingQrCode(SignInTestCase):
    """The sign-in names the company the scanned QR code is for: only an account there signs in
    (user, 2026-10-22)."""

    def qr_sign_in(self, identifier, company, password=PASSWORD):
        return self.w.client.post("/trainees/login", json={"identifier": str(identifier), "password": password, "company": company})

    def test_a_trainee_of_that_company_signs_in_there_in_any_letter_case(self):
        for company in (ALPHA, ALPHA.upper(), "   "):   # blank names no company
            with self.subTest(company=company):
                response = self.qr_sign_in("user1", company)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(self.claims(response)["tenant_id"], ALPHA)

    def test_another_company_s_trainee_gets_no_training_access_and_is_not_signed_in(self):
        response = self.qr_sign_in("user13", ALPHA)   # BETA's trainee
        self.assertEqual((response.status_code, response.json()["detail"]), (403, sign_in_service.NO_TRAINING_ACCESS))
        self.assertIsNone(self.entry("TR-B_N1-0").devices)   # no device slot taken
        self.assertEqual(self.qr_sign_in("user13", BETA).status_code, 200)   # as signing in does take one
        self.assertIsNotNone(self.entry("TR-B_N1-0").devices)

    def test_a_wrong_password_gets_the_usual_answer_whatever_the_company(self):
        for identifier in ("user1", "user13"):
            with self.subTest(identifier=identifier):
                response = self.qr_sign_in(identifier, ALPHA, password="wrong")
                self.assertEqual((response.status_code, response.json()["detail"]), (401, trainee_service.LOGIN_FAILED))


class StaffSignInWithoutACompanyCode(SignInTestCase):
    def choose(self, ticket, tenant_id):
        return self.w.client.post("/admin/login/company", json={"ticket": ticket, "tenantId": tenant_id})

    def test_a_trainer_signs_in_by_username_or_ho_id(self):
        for username in ("trainer1", "OFF1"):
            with self.subTest(username=username):
                response = self.staff_sign_in(username)
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual((body["admin"]["role"], body["admin"]["tenant_id"], body["company"]["tenantId"]), ("trainer", ALPHA, ALPHA))
                self.assertEqual(self.claims(response)["sub"], "agencyteam:trainer1")

    def test_an_agency_account_without_the_trainer_role_is_refused(self):
        self.w.agency["trainer2"].role = "manager"
        self.alpha.commit()
        self.assertEqual(self.staff_sign_in("trainer2").status_code, 403)

    def test_an_admin_with_one_company_signs_straight_into_it(self):
        for username, tenant in (("coadmin", ALPHA), ("coord", ALPHA), ("betaonly", BETA), ("adm_trainer", ALPHA)):
            with self.subTest(username=username):
                response = self.staff_sign_in(username)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual((self.claims(response)["tenant_id"], response.json()["company"]["tenantId"]), (tenant, tenant))

    def test_a_super_admin_chooses_the_company_with_the_ticket(self):
        response = self.staff_sign_in("super")
        self.assertEqual(response.status_code, 409, response.text)
        detail = response.json()["detail"]
        self.assertEqual(detail["code"], "CHOOSE_COMPANY")
        self.assertEqual({company["tenantId"] for company in detail["companies"]}, {ALPHA, BETA})

        chosen = self.choose(detail["ticket"], BETA)
        self.assertEqual(chosen.status_code, 200, chosen.text)
        self.assertEqual((self.claims(chosen)["tenant_id"], self.claims(chosen)["sub"]), (BETA, "admin:super"))

    def test_a_ticket_is_no_sign_in_token_and_opens_only_the_companies_it_lists(self):
        ticket = self.staff_sign_in("super").json()["detail"]["ticket"]
        self.assertEqual(self.w.client.get("/admin/profile", headers={"Authorization": f"Bearer {ticket}"}).status_code, 401)
        self.assertEqual(self.choose(ticket, "GHOST").status_code, 403)
        self.assertEqual(self.choose(ticket + "x", ALPHA).status_code, 401)
        access_token = self.staff_sign_in("coadmin").json()["access_token"]
        self.assertEqual(self.choose(access_token, ALPHA).status_code, 401)   # nor a sign-in token a ticket

    def test_an_expired_or_revoked_ticket_is_refused(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        expired = jwt.encode({"sub": "super", "purpose": "company-choice", "companies": [ALPHA], "ver": 0, "iat": past,
                              "exp": past + timedelta(minutes=2)}, sign_in_service._ticket_key(), algorithm=settings.ALGORITHM)
        self.assertEqual(self.choose(expired, ALPHA).status_code, 401)

        ticket = self.staff_sign_in("super").json()["detail"]["ticket"]
        self.w.admins["super"].tokenVersion = 1   # signed out everywhere meanwhile
        self.common.commit()
        self.assertEqual(self.choose(ticket, ALPHA).status_code, 401)

    def test_an_admin_with_no_grant_is_refused_and_a_wrong_password_is_a_plain_failure(self):
        self.assertEqual(self.staff_sign_in("ungranted").status_code, 403)
        response = self.staff_sign_in("super", "wrong")
        self.assertEqual((response.status_code, response.json()["detail"]), (401, admin_service.LOGIN_FAILED))


class TrainerShapedIdsNeverSignInAsTrainees(SignInTestCase):
    """A guard on top of the table rule (user, 2026-10-20): an ID that starts with AGT - a trainer's -
    never signs in as a trainee. It only ever refuses."""

    def setUp(self):
        super().setUp()
        self.alpha.add(Trainee(traineeUid="AGT2610099", name="Odd", email="odd@example.test", phone=9_200_000_099,
                               username="odd.one", password=hash_password(PASSWORD)))
        self.alpha.commit()
        registry_service.reconcile_tenant(self.common, self.alpha, ALPHA)

    def test_refused_with_or_without_the_company_code(self):
        self.assertEqual(self.trainee_sign_in("odd.one").status_code, 401)
        self.assertEqual(self.trainee_sign_in("odd.one", headers={"X-Tenant-ID": ALPHA}).status_code, 401)

    def test_real_trainers_and_trainees_are_unaffected(self):
        self.assertEqual(self.staff_sign_in("trainer1").status_code, 200)
        self.assertEqual(self.trainee_sign_in("user1").status_code, 200)

    def test_a_zone_that_would_spell_agt_gives_a_trainee_a_trn_id(self):
        self.assertEqual(uid_events.trainee_uid_prefix("Agt Zone"), "TRN")
        self.assertEqual(uid_events.trainee_uid_prefix("North"), "NORTH")


class FailedSignInsAreLimited(SignInTestCase):
    def test_failures_with_a_company_code_count_for_the_sign_in_without_one(self):
        for _ in range(rate_limit.ACCOUNT_MAX_FAILURES):
            self.trainee_sign_in("user1", "wrong", headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(self.trainee_sign_in("user1").status_code, 429)

    def test_failures_without_one_lock_the_account_both_ways(self):
        for _ in range(rate_limit.ACCOUNT_MAX_FAILURES):
            self.assertEqual(self.trainee_sign_in("HO-S_N1-0", "wrong").status_code, 401)
        self.assertEqual(self.trainee_sign_in("user1").status_code, 429)
        self.assertEqual(self.trainee_sign_in("user1", headers={"X-Tenant-ID": ALPHA}).status_code, 429)

    def test_made_up_ids_are_limited_too(self):
        for _ in range(rate_limit.ACCOUNT_MAX_FAILURES):
            self.assertEqual(self.staff_sign_in("nobody-at-all").status_code, 401)
        self.assertEqual(self.staff_sign_in("nobody-at-all").status_code, 429)


class AccountsCreatedOutsideThisApp(SignInTestCase):
    def test_a_trainer_the_php_system_added_signs_in_at_once(self):
        self.alpha.add(AgencyTeam(agencyTeamUid="g9", username="trainer9", name="Trainer9", password=hash_password(PASSWORD),
                                  role="trainer", company=SAMSUNG, offerId="OFF9"))
        self.alpha.commit()
        response = self.staff_sign_in("trainer9")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.entry("g9").tenant_uid, ALPHA)

    def test_a_made_up_id_is_looked_for_in_every_company_at_most_once_a_minute(self):
        with patch.object(tenant_manager, "get_session", wraps=tenant_manager.get_session) as opened:
            self.trainee_sign_in("nobody-at-all")
            looked = opened.call_count
            self.trainee_sign_in("nobody-at-all")
        self.assertGreaterEqual(looked, 2)   # ALPHA and BETA
        self.assertEqual(opened.call_count, looked)


class CompanySessionsAreClosed(SignInTestCase):
    def test_every_company_session_a_sign_in_opens_is_closed(self):
        sessions = []
        real = tenant_manager.get_session

        def open_and_track(tenant_uid, common_db=None):
            session = real(tenant_uid, common_db)
            session.close = Mock(wraps=session.close)
            sessions.append(session)
            return session

        self.beta.add(Trainee(traineeUid="TR-BETA-TWIN", name="Twin", email="twin@example.test", phone=9_000_000_001,
                              username="beta.twin", password=hash_password(PASSWORD)))
        self.beta.commit()
        registry_service.reconcile_tenant(self.common, self.beta, BETA)
        with patch.object(tenant_manager, "get_session", side_effect=open_and_track):
            self.assertEqual(self.trainee_sign_in("user1").status_code, 200)        # signed in
            self.assertEqual(self.trainee_sign_in("user1", "wrong").status_code, 401)   # refused
            self.assertEqual(self.trainee_sign_in(9_000_000_001).status_code, 409)     # two accounts
            self.assertEqual(self.staff_sign_in("coadmin").status_code, 200)        # an admin
        self.assertTrue(sessions and all(session.close.called for session in sessions))
