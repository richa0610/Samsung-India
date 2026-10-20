"""Signed-in devices, Phase 3 (user, 2026-10-19): a person in the central user registry may be signed
in on `max_devices` devices at once (2 unless changed); one more signs out the device used longest
ago, signing in again on the same device replaces its own session, and Logout ends only that device.
A token from before devices were tracked - or for an account not in the registry - works as before.

Synthetic TenantWorld (in-memory SQLite) only - no real database is touched."""

from datetime import datetime, timedelta
from unittest.mock import patch

from jose import jwt
from sqlalchemy.exc import OperationalError

from app.core import rate_limit
from app.core.config import settings
from app.core.security import create_access_token
from app.dependencies.auth import SIGNED_IN_ELSEWHERE
from app.models.common.login_session import LoginSession
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.services import device_sessions, sign_in_service
from app.services import user_registry_service as registry_service
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD
from tests.test_trainer_authorization import TrainerWorldTestCase


class DeviceTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        for reset in (rate_limit.reset, device_sessions._status.clear, sign_in_service._not_found.clear):
            reset()
            self.addCleanup(reset)
        self.common = self.w.common
        registry_service.reconcile_tenant(self.common, self.alpha, ALPHA)
        registry_service.reconcile_tenant(self.common, self.w.tenant_db[BETA], BETA)

    def sign_in(self, device_id=None, identifier="user1", headers=None):
        body = {"identifier": identifier, "password": PASSWORD, "deviceId": device_id}
        response = self.w.client.post("/trainees/login", json=body, headers=headers or {})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def staff_sign_in(self, device_id):
        response = self.w.client.post("/admin/login", json={"username": "trainer1", "password": PASSWORD, "deviceId": device_id})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def use(self, token, path="/sessions/history"):
        return self.w.client.get(path, headers={"Authorization": f"Bearer {token}"})

    def sid(self, token):
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]).get("sid")

    def session(self, token):
        self.common.expire_all()
        return self.common.query(LoginSession).filter(LoginSession.session_id == self.sid(token)).one()

    def live(self, user_uid="TR-S_N1-0"):
        self.common.expire_all()
        entry = self.common.query(UserRegistry).filter(UserRegistry.user_uid == user_uid).one()
        return self.common.query(LoginSession).filter(LoginSession.registry_id == entry.id, LoginSession.ended_at.is_(None)).count()


class EachSignInIsADevice(DeviceTestCase):
    def test_a_sign_in_names_its_device_session(self):
        token = self.sign_in("phone-a")
        session = self.session(token)
        self.assertEqual((session.device_id, session.tenant_uid, session.ended_at), ("phone-a", ALPHA, None))
        self.assertTrue(session.device_name)   # from the user agent when the app sends none
        self.assertEqual(self.use(token).status_code, 200)

    def test_a_third_device_signs_out_the_one_used_longest_ago(self):
        first, second = self.sign_in("phone-a"), self.sign_in("phone-b")
        self.assertEqual(self.use(first).status_code, 200)   # cached as live before it is signed out
        third = self.sign_in("phone-c")
        refused = self.use(first)
        self.assertEqual((refused.status_code, refused.json()["detail"]), (401, SIGNED_IN_ELSEWHERE))
        self.assertEqual([self.use(token).status_code for token in (second, third)], [200, 200])
        self.assertEqual(self.session(first).end_reason, device_sessions.REPLACED)

    def test_used_longest_ago_means_last_use_not_first_sign_in(self):
        first, second = self.sign_in("phone-a"), self.sign_in("phone-b")
        self.session(first).last_seen_at = datetime.utcnow()   # the first phone is the one in use
        self.session(second).last_seen_at = datetime.utcnow() - timedelta(hours=1)
        self.common.commit()
        self.sign_in("phone-c")
        self.assertEqual(self.use(first).status_code, 200)
        self.assertEqual(self.use(second).status_code, 401)

    def test_signing_in_again_on_the_same_device_replaces_only_its_own_session(self):
        old, other = self.sign_in("phone-a"), self.sign_in("phone-b")
        again = self.sign_in("phone-a")
        self.assertEqual(self.use(old).status_code, 401)
        self.assertEqual([self.use(token).status_code for token in (other, again)], [200, 200])
        self.assertEqual(self.live(), 2)

    def test_the_limit_is_per_person_and_changeable(self):
        entry = self.common.query(UserRegistry).filter(UserRegistry.user_uid == "TR-S_N1-0").one()
        entry.max_devices = 1
        self.common.commit()
        first = self.sign_in("phone-a")
        second = self.sign_in("phone-b")
        self.assertEqual((self.use(first).status_code, self.use(second).status_code), (401, 200))
        self.sign_in("phone-x", identifier="user2")   # someone else's devices don't count
        self.assertEqual(self.use(second).status_code, 200)

    def test_an_expired_session_takes_no_place(self):
        expired = self.sign_in("phone-a")
        self.session(expired).expires_at = datetime.utcnow() - timedelta(minutes=1)
        self.common.commit()
        second, third = self.sign_in("phone-b"), self.sign_in("phone-c")
        self.assertEqual([self.use(token).status_code for token in (second, third)], [200, 200])

    def test_a_sign_in_with_the_company_code_counts_too(self):
        first = self.sign_in("phone-a")
        self.sign_in("phone-b")
        self.sign_in("phone-c", headers={"X-Tenant-ID": ALPHA})   # an older app
        self.assertEqual(self.use(first).status_code, 401)

    def test_a_trainer_s_devices_are_limited_the_same_way(self):
        first, _second, _third = self.staff_sign_in("tab-a"), self.staff_sign_in("tab-b"), self.staff_sign_in("tab-c")
        refused = self.use(first, "/admin/profile")
        self.assertEqual((refused.status_code, refused.json()["detail"]), (401, SIGNED_IN_ELSEWHERE))

    def test_a_signed_out_device_can_t_reach_files_or_live_updates_either(self):
        first = self.sign_in("phone-a")
        self.sign_in("phone-b")
        self.sign_in("phone-c")
        self.assertEqual(self.use(first, "/tenants/current").status_code, 401)   # get_current_account / WebSocket rule


class LogoutEndsThisDeviceOnly(DeviceTestCase):
    def test_logout_signs_out_this_device_and_keeps_the_other(self):
        here, there = self.sign_in("phone-a"), self.sign_in("phone-b")
        version = self.alpha.query(Trainee).filter_by(traineeUid="TR-S_N1-0").one().tokenVersion
        response = self.w.client.post("/trainees/logout", headers={"Authorization": f"Bearer {here}"})
        self.assertEqual(response.status_code, 204, response.text)
        self.assertEqual((self.use(here).status_code, self.use(there).status_code), (401, 200))
        self.alpha.expire_all()
        self.assertEqual(self.alpha.query(Trainee).filter_by(traineeUid="TR-S_N1-0").one().tokenVersion, version)

    def test_a_trainer_s_logout_too(self):
        here, there = self.staff_sign_in("tab-a"), self.staff_sign_in("tab-b")
        self.assertEqual(self.w.client.post("/admin/logout", headers={"Authorization": f"Bearer {here}"}).status_code, 204)
        self.assertEqual((self.use(here, "/admin/profile").status_code, self.use(there, "/admin/profile").status_code), (401, 200))

    def test_a_token_from_before_devices_were_tracked_still_signs_out_everywhere(self):
        phone = self.alpha.query(Trainee).filter_by(traineeUid="TR-S_N1-0").one().phone
        old = create_access_token(subject=str(phone), tenant_id=ALPHA, role="trainee")   # no device session
        tracked = self.sign_in("phone-a")
        self.assertEqual(self.use(old).status_code, 200)
        self.assertEqual(self.w.client.post("/trainees/logout", headers={"Authorization": f"Bearer {old}"}).status_code, 204)
        self.assertEqual((self.use(old).status_code, self.use(tracked).status_code), (401, 401))


class EverythingElseKeepsWorking(DeviceTestCase):
    def test_an_account_not_in_the_registry_gets_no_device_session(self):
        self.common.query(UserRegistry).filter(UserRegistry.user_uid == "TR-S_N1-0").delete()
        self.common.commit()
        token = self.sign_in("phone-a", headers={"X-Tenant-ID": ALPHA})
        self.assertIsNone(self.sid(token))
        self.assertEqual(self.use(token).status_code, 200)

    def test_an_admin_table_account_has_no_device_limit(self):
        response = self.w.client.post("/admin/login", json={"username": "coadmin", "password": PASSWORD})
        self.assertIsNone(self.sid(response.json()["access_token"]))

    def test_a_new_phone_number_s_fresh_token_keeps_the_device_session(self):
        token = self.sign_in("phone-a")
        response = self.w.client.patch("/trainees/me", json={"phone": 9_766_666_666, "state": "Delhi"},
                                       headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200, response.text)
        fresh = response.json()["access_token"]
        self.assertEqual(self.sid(fresh), self.sid(token))
        self.assertEqual(self.use(fresh).status_code, 200)

    def test_registering_signs_the_trainee_in_on_that_device(self):
        body = {"name": "New Person", "phone": 9_788_888_888, "email": "new.device@example.com", "state": "Delhi", "deviceId": "phone-n"}
        with patch("app.models.uid_events.next_uid", lambda connection, prefix: f"{prefix}2610999"):
            response = self.w.client.post("/trainees/register", json=body, headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(self.session(response.json()["access_token"]).device_id, "phone-n")

    def test_a_common_database_blip_doesn_t_sign_anyone_out(self):
        token = self.sign_in("phone-a")
        device_sessions._status.clear()
        with patch.object(self.common, "query", side_effect=OperationalError("SELECT", {}, Exception("blip"))):
            self.assertEqual(self.use(token).status_code, 200)
