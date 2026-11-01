"""The two staff areas (user, 2026-10-31): trainers use /trainer and admins /admin - one set of handlers
behind a gate per area - each signing in at their own login, which the other kind can't use. A trainer
still on the old app, which calls /admin, is told to update it.

Route-by-route authorization (anonymous, trainee, admin, trainer and other-trainer callers) is in
test_phase7_route_coverage. This covers what that can't: the twins run the very same code, the two
logins with and without a company code, and the two live-event channels.

Synthetic TenantWorld (in-memory SQLite) only."""

import unittest
from contextlib import ExitStack

from fastapi.routing import APIRoute

from app.dependencies.auth import ADMIN_ACCOUNT_REQUIRED
from app.services import admin_service
from tests.tenant_fixtures import ALPHA, PASSWORD, TenantWorld
from tests.test_phase7_route_coverage import _walk
from tests.test_sign_in_without_company import SignInTestCase
from tests.test_ws_connection_release import SocketTestCase


def _endpoints(app) -> dict:
    """(method, path) -> the function that serves it, for every HTTP route as the app serves it."""
    found = {}
    for route in _walk(app.routes):
        original = getattr(route, "original_route", route)
        if isinstance(original, APIRoute):
            for method in route.methods:
                found[(method, route.path)] = original.endpoint
    return found


class TheTrainerAreaIsTheStaffAreaAgain(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.endpoints = _endpoints(self.w.app)

    def test_every_trainer_route_runs_the_same_code_as_its_admin_twin(self):
        trainer_routes = {key: fn for key, fn in self.endpoints.items() if key[1].startswith("/trainer/") and key[1] != "/trainer/login"}
        self.assertEqual(len(trainer_routes), 44)
        for (method, path), endpoint in trainer_routes.items():
            with self.subTest(method=method, path=path):
                self.assertIs(endpoint, self.endpoints[(method, "/admin" + path.removeprefix("/trainer"))])

    def test_a_trainer_on_the_old_app_is_told_to_update_it(self):
        headers = self.w.headers("trainer1")
        for path in ("/trainings/page", "/trainings/summary", "/attendance/page", "/trainees/page", "/zones", "/profile"):
            with self.subTest(path=path):
                via_admin = self.w.client.get("/admin" + path, headers=headers)      # what the old app calls
                self.assertEqual((via_admin.status_code, via_admin.json()["detail"]), (403, ADMIN_ACCOUNT_REQUIRED))
                self.assertEqual(self.w.client.get("/trainer" + path, headers=headers).status_code, 200)


class TrainerLoginWithACompanyCode(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)

    def sign_in(self, area, username, password=PASSWORD):
        return self.w.client.post(f"/{area}/login", json={"username": username, "password": password}, headers={"X-Tenant-ID": ALPHA})

    def test_trainers_sign_in_there_whichever_table_holds_them(self):
        for who in ("trainer1", "adm_trainer"):
            with self.subTest(who=who):
                response = self.sign_in("trainer", who)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["admin"]["role"], "trainer")

    def test_an_admin_is_sent_to_admin_login_once_the_password_is_right(self):
        for who in ("super", "coadmin"):
            with self.subTest(who=who):
                response = self.sign_in("trainer", who)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["detail"], {"code": "USE_ADMIN_LOGIN", "message": admin_service.USE_ADMIN_LOGIN})

    def test_a_wrong_password_is_the_same_refusal_on_both_logins(self):
        for who in ("trainer1", "super"):
            with self.subTest(who=who):
                via_trainer = self.sign_in("trainer", who, password="wrong")
                via_admin = self.sign_in("admin", who, password="wrong")
                self.assertEqual((via_trainer.status_code, via_trainer.json()), (via_admin.status_code, via_admin.json()))
                self.assertEqual(via_trainer.status_code, 401)

    def test_admin_login_sends_a_trainer_to_trainer_login_once_the_password_is_right(self):
        for who in ("trainer1", "adm_trainer"):
            with self.subTest(who=who):
                response = self.sign_in("admin", who)
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["detail"], {"code": "USE_TRAINER_LOGIN", "message": admin_service.USE_TRAINER_LOGIN})

    def test_admins_sign_in_at_admin_login(self):
        response = self.sign_in("admin", "coadmin")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["admin"]["role"], "admin")


class TrainerLoginWithoutACompanyCode(SignInTestCase):
    def trainer_sign_in(self, username, password=PASSWORD):
        return self.w.client.post("/trainer/login", json={"username": username, "password": password})

    def test_a_trainer_signs_in_and_is_told_their_company(self):
        response = self.trainer_sign_in("trainer1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()["admin"]["role"], self.claims(response)["tenant_id"]), ("trainer", ALPHA))

    def test_an_admin_with_several_companies_is_sent_to_admin_login_not_asked_to_choose(self):
        response = self.trainer_sign_in("super")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "USE_ADMIN_LOGIN")
        self.assertEqual(self.staff_sign_in("super").json()["detail"]["code"], "CHOOSE_COMPANY")   # Admin login unchanged

    def test_a_trainer_at_admin_login_is_sent_to_trainer_login(self):
        response = self.w.client.post("/admin/login", json={"username": "trainer1", "password": PASSWORD})   # no company code
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "USE_TRAINER_LOGIN")

    def test_a_wrong_password_is_still_just_a_failed_sign_in(self):
        self.assertEqual(self.trainer_sign_in("super", password="wrong").status_code, 401)
        self.assertEqual(self.trainer_sign_in("trainer1", password="wrong").status_code, 401)


class StaffLiveEvents(SocketTestCase):
    def assert_channel_takes(self, channel, welcome, refused):
        for who in welcome:
            with self.subTest(channel=channel, who=who), ExitStack() as stack:
                self.open_ready(stack, channel, self.w.token(who))
        for who in refused:
            with self.subTest(channel=channel, who=who):
                self.assertEqual(self.close_code(channel, self.w.token(who)), 1008)

    def test_each_channel_takes_its_own_kind_of_account_only(self):
        self.assert_channel_takes("/ws/trainer", welcome=("trainer1", "adm_trainer"), refused=("super", "coadmin"))
        self.assert_channel_takes("/ws/admin", welcome=("super", "coadmin"), refused=("trainer1", "adm_trainer"))


if __name__ == "__main__":
    unittest.main()
