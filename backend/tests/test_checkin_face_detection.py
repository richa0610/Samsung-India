"""Trainee security check-in: a tenant runs the face check before the photo, or just captures it.

1. The setting lives on the tenant's registry row (Common DB `tenants`, next to the proctoring
   controls), is ON by default - including for rows that existed before the column did - and is
   tenant-wide.
2. Only a Super Admin reads or changes it (GET / PUT /admin/settings/check-in); every change is
   logged in that tenant's activity log; only a real JSON true / false is accepted.
3. The check-in's location step (POST /attendance/verify-location) tells the trainee app which
   one its tenant uses.
"""

import unittest

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database.connection import CommonBase
from app.database.schema_sync import sync_missing_columns
from app.models.common.tenant_registry import Tenant
from app.models.logs_master import LogsMaster
from app.models.trainee import Trainee
from tests.tenant_fixtures import ALPHA, BETA, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

SETTINGS = "/admin/settings/check-in"


class CheckInFaceDetectionTestCase(TrainerWorldTestCase):
    def put(self, who, json, tenant=ALPHA):
        return self.w.client.put(SETTINGS, json=json, headers=self.w.headers(who, tenant))

    def stored(self, tenant):
        self.w.common.expire_all()
        return self.w.common.query(Tenant).filter(Tenant.tenant_uid == tenant).one().checkin_face_detection_enabled

    def trainee_headers(self, tenant):
        trainee = self.w.tenant_db[tenant].query(Trainee).filter(Trainee.traineeUid.like("TR-%")).first()
        token = create_access_token(subject=str(trainee.phone), tenant_id=tenant, role="trainee")
        return {"Authorization": f"Bearer {token}"}

    def verify_location(self, tenant, conference_key):
        return self.w.client.post(
            "/attendance/verify-location",
            json={"conferenceUid": uid(conference_key), "latitude": 28.6, "longitude": 77.2},
            headers=self.trainee_headers(tenant),
        )


class TheSettingIsTenantWideAndOnByDefault(CheckInFaceDetectionTestCase):
    def test_every_tenant_starts_with_the_face_check_on(self):
        self.assertEqual((self.stored(ALPHA), self.stored(BETA)), (1, 1))
        response = self.get("super", SETTINGS)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"faceDetectionEnabled": True})

    def test_a_super_admin_turns_it_off_and_on_again_for_their_tenant_only(self):
        off = self.put("super", {"faceDetectionEnabled": False})
        self.assertEqual(off.status_code, 200, off.text)
        self.assertEqual(off.json(), {"faceDetectionEnabled": False})
        self.assertEqual((self.stored(ALPHA), self.stored(BETA)), (0, 1))
        self.assertEqual(self.get("super", SETTINGS).json(), {"faceDetectionEnabled": False})
        self.assertEqual(self.get("super", SETTINGS, tenant=BETA).json(), {"faceDetectionEnabled": True})

        self.assertEqual(self.put("super", {"faceDetectionEnabled": True}).json(), {"faceDetectionEnabled": True})
        self.assertEqual(self.stored(ALPHA), 1)

    def test_every_change_is_logged_in_that_tenants_activity_log(self):
        self.put("super", {"faceDetectionEnabled": False})
        self.put("super", {"faceDetectionEnabled": True})
        rows = self.alpha.query(LogsMaster).filter(LogsMaster.action == "UPDATE_CHECKIN_FACE_DETECTION").order_by(LogsMaster.id).all()
        self.assertEqual([(r.username, r.role) for r in rows], [("super", "super_admin")] * 2)
        self.assertEqual(
            [r.remarks for r in rows],
            ["Face detection at trainee check-in turned off", "Face detection at trainee check-in turned on"],
        )
        beta_rows = self.w.tenant_db[BETA].query(LogsMaster).filter(LogsMaster.action == "UPDATE_CHECKIN_FACE_DETECTION").count()
        self.assertEqual(beta_rows, 0)


class OnlyASuperAdminMayReadOrChangeIt(CheckInFaceDetectionTestCase):
    def test_every_other_admin_role_and_trainer_is_refused_and_nothing_changes(self):
        for who in ("coadmin", "coord", "subcoord", "ungranted", "adm_trainer", "trainer1"):
            with self.subTest(who=who):
                self.assertEqual(self.get(who, SETTINGS).status_code, 403)
                self.assertEqual(self.put(who, {"faceDetectionEnabled": False}).status_code, 403)
        self.assertEqual(self.stored(ALPHA), 1)

    def test_a_trainee_or_an_anonymous_caller_is_refused(self):
        headers = self.trainee_headers(ALPHA)
        self.assertEqual(self.w.client.put(SETTINGS, json={"faceDetectionEnabled": False}, headers=headers).status_code, 401)
        self.assertEqual(self.w.client.put(SETTINGS, json={"faceDetectionEnabled": False}).status_code, 401)
        self.assertEqual(self.stored(ALPHA), 1)

    def test_a_super_admin_token_for_another_tenant_cannot_reach_this_one(self):
        # The tenant comes from the signed token, never a header: a BETA token changes BETA only.
        response = self.w.client.put(
            SETTINGS, json={"faceDetectionEnabled": False}, headers={**self.w.headers("super", BETA), "X-Tenant-ID": ALPHA}
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((self.stored(ALPHA), self.stored(BETA)), (1, 0))

    def test_only_a_real_true_or_false_is_accepted(self):
        for body in ({}, {"faceDetectionEnabled": "no"}, {"faceDetectionEnabled": 0}, {"faceDetectionEnabled": None}):
            with self.subTest(body=body):
                self.assertEqual(self.put("super", body).status_code, 422)
        self.assertEqual(self.stored(ALPHA), 1)


class TheCheckInLearnsItsTenantsSetting(CheckInFaceDetectionTestCase):
    def test_the_location_step_says_whether_to_run_the_face_check(self):
        response = self.verify_location(ALPHA, "S_N1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIs(response.json()["faceDetectionRequired"], True)

        self.put("super", {"faceDetectionEnabled": False})
        self.assertIs(self.verify_location(ALPHA, "S_N1").json()["faceDetectionRequired"], False)
        self.assertIs(self.verify_location(BETA, "B_N1").json()["faceDetectionRequired"], True)

    def test_a_tenant_without_a_registry_row_keeps_the_face_check(self):
        self.w.common.query(Tenant).filter(Tenant.tenant_uid == ALPHA).delete()
        self.w.common.commit()
        response = self.verify_location(ALPHA, "S_N1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIs(response.json()["faceDetectionRequired"], True)


class ExistingRegistryRowsGetTheColumnSwitchedOn(unittest.TestCase):
    """The column reaches a live `tenants` table through schema_sync on the next startup; every
    tenant that already exists must come out with the face check ON (today's behaviour)."""

    def test_schema_sync_adds_it_on_for_existing_tenants(self):
        engine = create_engine("sqlite://", poolclass=StaticPool)
        self.addCleanup(engine.dispose)
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE tenants (id INTEGER PRIMARY KEY, tenant_uid VARCHAR(100) NOT NULL, company_name VARCHAR(200) NOT NULL, "
                "database_host VARCHAR(255) NOT NULL, database_port INTEGER NOT NULL, database_name VARCHAR(100) NOT NULL, "
                "database_username VARCHAR(100) NOT NULL, database_password VARCHAR(255) NOT NULL, status VARCHAR(50) NOT NULL, "
                "live_proctoring_enabled INTEGER NOT NULL DEFAULT 0, proctoring_max_warnings INTEGER NOT NULL DEFAULT 3, "
                "created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
            ))
            conn.execute(text(
                "INSERT INTO tenants VALUES (1, 'existing', 'Existing Co', 'h', 3306, 'db', 'u', 'p', 'active', 0, 3, "
                "'2026-01-01', '2026-01-01')"
            ))

        sync_missing_columns(engine, CommonBase)

        self.assertIn("checkin_face_detection_enabled", {c["name"] for c in inspect(engine).get_columns("tenants")})
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT checkin_face_detection_enabled FROM tenants")).scalar_one(), 1)


if __name__ == "__main__":
    unittest.main()
