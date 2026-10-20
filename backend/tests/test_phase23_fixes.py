"""Phase 2.2 follow-up fixes (approved decisions - see the memory note "security decisions"):

- the recorded caller IP trusts only the IP Render appends; failed logins are limited per account
  only - no login or sign-up is limited per caller IP (user, 2026-10-17);
- the trainee login failure message reveals nothing;
- WebSocket tokens travel in the first message (URL tokens still accepted until retired);
- tokens can be revoked (logout) through a per-account version;
- tenant database passwords are encrypted at rest;
- tenant databases get the additive schema sync when first opened;
- business rules 1-4: placement by trainers/admins, partial PATCH, attendance reset.

Synthetic TenantWorld (in-memory SQLite) only - no real database, secret or file is touched.
"""

import unittest
from unittest.mock import patch

from cryptography.fernet import Fernet
from sqlalchemy import Column, Integer, create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.websockets import WebSocketDisconnect

from app.core import rate_limit, secret_box
from app.core.config import settings
from app.core.security import create_access_token
from app.database.tenant import TenantConnectionManager, tenant_manager
from app.models.attendance import Attendance
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.logs_master import LogsMaster
from app.models.trainee import Trainee
from scripts import encrypt_tenant_db_passwords as encrypt_script
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

PLAIN_DB_PASSWORD = "synthetic-db-password"


class FixesTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        rate_limit.reset()
        self.addCleanup(rate_limit.reset)

    def login(self, username, password=PASSWORD, forwarded="203.0.113.10", tenant=ALPHA, **headers):
        return self.w.client.post(
            "/admin/login",
            json={"username": username, "password": password},
            headers={"X-Tenant-ID": tenant, "X-Forwarded-For": forwarded, **headers},
        )


class RecordedCallerIpTrustsOnlyTheProxyHop(FixesTestCase):
    def recorded_login_ip(self, **login_kwargs):
        self.assertEqual(self.login("trainer1", **login_kwargs).status_code, 200)
        self.alpha.expire_all()
        return self.alpha.query(LogsMaster).filter(LogsMaster.action == "LOGIN").order_by(LogsMaster.id.desc()).first().login_IP

    def test_forged_forwarding_headers_are_not_recorded(self):
        # Render appends the real caller last; everything the client adds in front is ignored,
        # and CF-Connecting-IP (no Cloudflare in front) is never trusted.
        ip = self.recorded_login_ip(forwarded="10.0.0.1, 198.51.100.7", **{"CF-Connecting-IP": "10.1.1.1"})
        self.assertEqual(ip, "198.51.100.7")

    def test_without_a_proxy_the_socket_peer_is_recorded(self):
        with patch.object(settings, "TRUSTED_PROXY_HOPS", 0):
            ip = self.recorded_login_ip(forwarded="198.51.100.7")
        self.assertEqual(ip, "testclient")


class StaffLoginHasNoPerAddressLimit(FixesTestCase):
    OFFICE_WIFI = "198.51.100.66"
    MANY = 25   # more than any per-address limit this login ever had (5 requests / 5 min)

    def test_many_logins_from_one_address_all_succeed(self):
        for i in range(self.MANY):
            with self.subTest(login=i):
                self.assertEqual(self.login("trainer1", forwarded=self.OFFICE_WIFI).status_code, 200)

    def test_failures_for_other_accounts_from_one_address_never_block_that_address(self):
        for i in range(self.MANY):
            self.assertEqual(self.login(f"nobody{i}", "wrong", forwarded=self.OFFICE_WIFI).status_code, 401)
        self.assertEqual(self.login("trainer1", forwarded=self.OFFICE_WIFI).status_code, 200)


class AccountFailureLimit(FixesTestCase):
    def test_wrong_passwords_from_many_addresses_lock_only_that_account(self):
        for i in range(rate_limit.ACCOUNT_MAX_FAILURES):
            self.assertEqual(self.login("trainer1", "wrong", forwarded=f"198.51.100.{i}").status_code, 401)
        self.assertEqual(self.login("trainer1", forwarded="198.51.100.99").status_code, 429)  # even the right password
        self.assertEqual(self.login("trainer2", forwarded="198.51.100.98").status_code, 200)  # other accounts unaffected

    def test_a_success_clears_the_count(self):
        for i in range(rate_limit.ACCOUNT_MAX_FAILURES - 1):
            self.login("trainer1", "wrong", forwarded=f"198.51.100.{i}")
        self.assertEqual(self.login("trainer1", forwarded="198.51.100.50").status_code, 200)
        self.assertEqual(self.login("trainer1", "wrong", forwarded="198.51.100.51").status_code, 401)
        self.assertEqual(self.login("trainer1", forwarded="198.51.100.52").status_code, 200)


class TraineeLoginTestCase(FixesTestCase):
    def trainee_login(self, identifier, forwarded="198.51.100.1", password=PASSWORD):
        return self.w.client.post("/trainees/login", json={"identifier": str(identifier), "password": password},
                                  headers={"X-Tenant-ID": ALPHA, "X-Forwarded-For": forwarded})

    def trainee(self, trainee_uid="TR-S_N1-0"):
        return self.alpha.query(Trainee).filter(Trainee.traineeUid == trainee_uid).one()

    def set_stored_password(self, trainee_uid, value):
        self.trainee(trainee_uid).password = value
        self.alpha.commit()


class TraineeLoginWithCompanyIdOrPhoneAndPassword(TraineeLoginTestCase):
    def test_the_trainee_uid_username_or_phone_with_the_password_signs_in(self):
        t = self.trainee()
        for identifier in (t.traineeUid, t.username, t.phone, f"  {t.traineeUid} "):
            with self.subTest(identifier=identifier):
                response = self.trainee_login(identifier)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["trainee"]["traineeUid"], "TR-S_N1-0")

    def test_the_signed_in_trainee_carries_the_profile_pages_zone_region_and_managers_designation(self):
        t = self.trainee()
        t.supervisorDesignation = "Store Manager"
        self.alpha.commit()
        trainee = self.trainee_login(t.traineeUid).json()["trainee"]
        self.assertEqual((trainee["zone"], trainee["region"], trainee["supervisorDesignation"]), ("North Zone", "North 1", "Store Manager"))

    def test_every_failure_gets_the_same_generic_401(self):
        self.set_stored_password("TR-S_N1-1", None)       # e.g. self-registered: no password
        self.set_stored_password("TR-S_DEL-0", "")
        self.set_stored_password("TR-S_DEL-1", PASSWORD)  # not a bcrypt hash: never matches, even as typed
        cases = {
            "wrong password": ("TR-S_N1-0", "wrong"),
            "unknown company id": ("TR-NOBODY", PASSWORD),
            "unknown phone": (9_999_999_999, PASSWORD),
            "no password set": ("TR-S_N1-1", PASSWORD),
            "empty password stored": ("TR-S_DEL-0", PASSWORD),
            "stored value is not a hash": ("TR-S_DEL-1", PASSWORD),
            "over bcrypt's 72-byte limit": ("TR-S_N1-0", "x" * 100),
        }
        details = set()
        for case, (identifier, password) in cases.items():
            with self.subTest(case):
                response = self.trainee_login(identifier, password=password)
                self.assertEqual(response.status_code, 401)
                details.add(response.json()["detail"])
        self.assertEqual(len(details), 1)
        self.assertNotIn("No trainee", details.pop())

    def test_an_identifier_naming_two_trainees_signs_in_neither(self):
        self.trainee("TR-S_N1-1").username = "TR-S_N1-0"   # one's username is another's Trainee UID
        self.alpha.commit()
        self.assertEqual(self.trainee_login("TR-S_N1-0").status_code, 401)
        self.assertEqual(self.trainee_login(self.trainee().phone).status_code, 200)

    def test_a_phone_only_request_from_an_old_app_build_is_refused(self):
        response = self.w.client.post("/trainees/login", json={"phone": self.trainee().phone}, headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(response.status_code, 422)

    def test_an_account_is_locked_after_repeated_failures_whichever_id_is_typed(self):
        t = self.trainee()
        identifiers = (t.traineeUid, t.username, t.phone)
        for i in range(rate_limit.ACCOUNT_MAX_FAILURES):
            self.trainee_login(identifiers[i % len(identifiers)], f"198.51.100.{i}", password="wrong")
        self.assertEqual(self.trainee_login(t.phone, "198.51.100.200").status_code, 429)   # even the right password
        self.assertEqual(self.trainee_login("TR-S_N1-1", "198.51.100.201").status_code, 200)   # others unaffected

    def test_an_unknown_phone_is_locked_after_repeated_failures_from_any_address(self):
        for i in range(rate_limit.ACCOUNT_MAX_FAILURES):
            self.trainee_login(9_999_999_999, f"198.51.100.{i}")
        self.assertEqual(self.trainee_login(9_999_999_999, "198.51.100.200").status_code, 429)


class TraineeLoginHasNoPerAddressLimit(TraineeLoginTestCase):
    VENUE_WIFI = "198.51.100.77"
    CLASSROOM = 25   # more than any per-address limit this login ever had (20 failures / 5 min)

    def unknown_phone(self, i):
        return 6_000_000_000 + i   # no fixture trainee has a 6... number; one try each, so no account lock

    def test_a_classroom_on_one_address_is_never_blocked_by_its_own_successes(self):
        phones = [phone for (phone,) in self.alpha.query(Trainee.phone)]
        for i in range(self.CLASSROOM):
            with self.subTest(login=i):
                self.assertEqual(self.trainee_login(phones[i % len(phones)], self.VENUE_WIFI).status_code, 200)

    def test_failures_for_other_accounts_from_one_address_never_block_that_address(self):
        for i in range(self.CLASSROOM):
            self.assertEqual(self.trainee_login(self.unknown_phone(i), self.VENUE_WIFI).status_code, 401)
        self.assertEqual(self.trainee_login(self.trainee().phone, self.VENUE_WIFI).status_code, 200)


class SelfRegistrationSignsInWithoutAPassword(TraineeLoginTestCase):
    NEW = {"name": "New Person", "phone": 9_876_543_210, "email": "new.person@example.com", "state": "Delhi"}

    def register(self, person=None):
        person = person or self.NEW
        # The synthetic world switches UID generation off (tenant_fixtures); a self-registration needs one.
        with patch("app.models.uid_events.next_uid", lambda connection, prefix: f"{prefix}-SELF-{person['phone']}"):
            return self.w.client.post("/trainees/register", json=person, headers={"X-Tenant-ID": ALPHA, "X-Forwarded-For": "198.51.100.5"})

    def test_a_classroom_can_sign_up_from_one_address(self):
        # No per-address limit on sign-up (user, 2026-10-17): it used to refuse the 6th within 5 minutes.
        for i in range(8):
            person = {**self.NEW, "phone": 9_876_543_300 + i, "email": f"new.person.{i}@example.com"}
            with self.subTest(sign_up=i):
                self.assertEqual(self.register(person).status_code, 201)

    def test_registering_returns_a_working_session_for_that_trainee(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["trainee"]["phone"], self.NEW["phone"])
        headers = {"Authorization": f"Bearer {body['access_token']}"}
        self.assertNotEqual(self.w.client.get("/sessions/current", headers=headers).status_code, 401)
        self.assertEqual(self.w.client.post("/trainees/logout", headers=headers).status_code, 204)

    def test_a_self_registered_trainee_has_no_password_so_cannot_log_in_later(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertIsNone(self.alpha.query(Trainee).filter(Trainee.phone == self.NEW["phone"]).one().password)
        self.assertEqual(self.trainee_login(self.NEW["phone"]).status_code, 401)


class WebSocketFirstMessageAuth(FixesTestCase):
    def joins(self, conference_key, token):
        try:
            with self.w.client.websocket_connect(f"/ws/live/{uid(conference_key)}") as ws:
                ws.send_json({"type": "auth", "token": token})
                return ws.receive_json() == {"type": "ready"}
        except WebSocketDisconnect:
            return False

    def test_a_token_in_the_first_message_joins_an_authorized_room(self):
        self.assertTrue(self.joins("S_N1", self.w.token("trainer1")))
        self.assertFalse(self.joins("S_S1", self.w.token("trainer1")))  # trainer2's room
        self.assertFalse(self.joins("B_N1", self.w.token("coadmin")))   # another tenant

    def test_no_or_bad_auth_message_is_refused(self):
        for message in ({"type": "hello"}, {"type": "auth", "token": "not-a-jwt"}, {"type": "auth"}):
            with self.subTest(message=message):
                with self.w.client.websocket_connect(f"/ws/live/{uid('S_N1')}") as ws:
                    ws.send_json(message)
                    with self.assertRaises(WebSocketDisconnect):
                        ws.receive_json()

    def test_the_admin_channel_takes_the_first_message_too(self):
        with self.w.client.websocket_connect("/ws/admin") as ws:
            ws.send_json({"type": "auth", "token": self.w.token("coadmin")})
            self.assertEqual(ws.receive_json(), {"type": "ready"})

    def test_a_token_in_the_url_is_never_accepted(self):
        # Every app build sends the token in the first message; a URL token (which proxies log)
        # authenticates nothing - without the auth message the connection is closed.
        with self.w.client.websocket_connect(f"/ws/live/{uid('S_N1')}?token={self.w.token('trainer1')}") as ws:
            ws.send_json({"type": "hello"})
            with self.assertRaises(WebSocketDisconnect):
                ws.receive_json()


class TokenRevocation(FixesTestCase):
    def test_logout_revokes_every_token_of_that_account_only(self):
        first = self.login("trainer1").json()["access_token"]
        second = self.login("trainer1", forwarded="198.51.100.2").json()["access_token"]  # another device
        other = self.w.headers("trainer2")
        response = self.w.client.post("/admin/logout", headers={"Authorization": f"Bearer {first}"})
        self.assertEqual(response.status_code, 204)
        for token in (first, second):
            self.assertEqual(self.w.client.get("/admin/profile", headers={"Authorization": f"Bearer {token}"}).status_code, 401)
        self.assertEqual(self.w.client.get("/admin/profile", headers=other).status_code, 200)
        fresh = self.login("trainer1", forwarded="198.51.100.3").json()["access_token"]
        self.assertEqual(self.w.client.get("/admin/profile", headers={"Authorization": f"Bearer {fresh}"}).status_code, 200)
        logouts = self.alpha.query(LogsMaster).filter(LogsMaster.action == "LOGOUT").count()
        self.assertEqual(logouts, 1)

    def test_an_admin_table_account_is_revoked_in_the_common_database(self):
        token = self.login("coadmin").json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(self.w.client.post("/admin/logout", headers=headers).status_code, 204)
        self.assertEqual(self.w.client.get("/admin/profile", headers=headers).status_code, 401)

    def test_a_trainee_can_log_out_and_the_token_dies_everywhere(self):
        phone = self.alpha.query(Trainee).filter(Trainee.traineeUid == "TR-S_N1-0").one().phone
        token = self.w.client.post("/trainees/login", json={"identifier": str(phone), "password": PASSWORD},
                                   headers={"X-Tenant-ID": ALPHA}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(self.w.client.post("/trainees/logout", headers=headers).status_code, 204)
        self.assertEqual(self.w.client.get("/sessions/current", headers=headers).status_code, 401)
        self.assertEqual(self.w.client.get("/media/trainer_photos/default_male.png", headers=headers).status_code, 401)
        with self.w.client.websocket_connect(f"/ws/live/{uid('S_N1')}") as ws:
            ws.send_json({"type": "auth", "token": token})
            with self.assertRaises(WebSocketDisconnect):
                ws.receive_json()

    def test_tokens_issued_before_versions_existed_keep_working_until_a_logout(self):
        legacy = create_access_token(subject="agencyteam:trainer1", tenant_id=ALPHA, role="trainer")  # ver 0
        self.assertEqual(self.w.client.get("/admin/profile", headers={"Authorization": f"Bearer {legacy}"}).status_code, 200)


class TenantPasswordEncryption(unittest.TestCase):
    def setUp(self):
        self.key = Fernet.generate_key().decode()
        keys = patch.object(settings, "TENANT_SECRETS_KEYS", self.key)
        keys.start()
        self.addCleanup(keys.stop)

    def test_round_trip_and_plaintext_passthrough(self):
        stored = secret_box.encrypt_secret(PLAIN_DB_PASSWORD)
        self.assertTrue(stored.startswith(secret_box.ENCRYPTED_PREFIX))
        self.assertNotIn(PLAIN_DB_PASSWORD, stored)
        self.assertEqual(secret_box.decrypt_secret(stored), PLAIN_DB_PASSWORD)
        self.assertEqual(secret_box.decrypt_secret(PLAIN_DB_PASSWORD), PLAIN_DB_PASSWORD)  # not yet migrated

    def test_rotation_keeps_old_values_readable(self):
        old = secret_box.encrypt_secret(PLAIN_DB_PASSWORD)
        new_key = Fernet.generate_key().decode()
        with patch.object(settings, "TENANT_SECRETS_KEYS", f"{new_key},{self.key}"):
            self.assertEqual(secret_box.decrypt_secret(old), PLAIN_DB_PASSWORD)
            rotated = secret_box.reencrypt_secret(old)
        with patch.object(settings, "TENANT_SECRETS_KEYS", new_key):
            self.assertEqual(secret_box.decrypt_secret(rotated), PLAIN_DB_PASSWORD)

    def test_a_missing_or_wrong_key_fails_without_revealing_anything(self):
        stored = secret_box.encrypt_secret(PLAIN_DB_PASSWORD)
        for keys in ("", Fernet.generate_key().decode()):
            with self.subTest(keys=bool(keys)), patch.object(settings, "TENANT_SECRETS_KEYS", keys):
                with self.assertRaises(secret_box.SecretUnavailable) as caught:
                    secret_box.decrypt_secret(stored)
                self.assertNotIn(PLAIN_DB_PASSWORD, str(caught.exception))

    def common(self):
        engine = create_engine("sqlite://", poolclass=StaticPool)
        Tenant.__table__.create(engine)
        return sessionmaker(bind=engine)()

    def add_tenant(self, db, uid_, password):
        db.add(Tenant(tenant_uid=uid_, company_name=uid_, database_host="127.0.0.1", database_port=1,
                      database_name=uid_.lower(), database_username="u", database_password=password, status="active"))
        db.commit()

    def test_the_tenant_manager_connects_with_the_decrypted_password(self):
        db = self.common()
        self.add_tenant(db, "ENCRYPTED_T", secret_box.encrypt_secret(PLAIN_DB_PASSWORD))
        manager = TenantConnectionManager()
        engine = manager.get_engine("ENCRYPTED_T", db)  # lazy: nothing connects
        self.assertEqual(engine.url.password, PLAIN_DB_PASSWORD)
        self.assertNotIn(PLAIN_DB_PASSWORD, repr(engine.url))

    def test_an_undecryptable_tenant_is_unavailable_not_crashed(self):
        db = self.common()
        self.add_tenant(db, "LOCKED_T", secret_box.encrypt_secret(PLAIN_DB_PASSWORD))
        with patch.object(settings, "TENANT_SECRETS_KEYS", ""):
            with self.assertRaises(Exception) as caught:
                TenantConnectionManager().get_engine("LOCKED_T", db)
        self.assertEqual(getattr(caught.exception, "status_code", None), 503)

    def test_the_migration_script_encrypts_verifies_and_is_dry_by_default(self):
        db = self.common()
        self.add_tenant(db, "PLAIN_T", PLAIN_DB_PASSWORD)
        self.add_tenant(db, "DONE_T", secret_box.encrypt_secret(PLAIN_DB_PASSWORD))
        rows = encrypt_script.plan(db)
        self.assertEqual({t.tenant_uid: a for t, a in rows}, {"PLAIN_T": "encrypt", "DONE_T": "re-encrypt"})
        self.assertEqual(db.query(Tenant).filter_by(tenant_uid="PLAIN_T").one().database_password, PLAIN_DB_PASSWORD)
        encrypt_script.apply(db, rows)
        db.expire_all()
        for tenant in db.query(Tenant):
            self.assertTrue(secret_box.is_encrypted(tenant.database_password))
            self.assertEqual(secret_box.decrypt_secret(tenant.database_password), PLAIN_DB_PASSWORD)


class EncryptionRollback(TenantPasswordEncryption):
    def test_rollback_restores_plaintext_and_is_idempotent(self):
        db = self.common()
        self.add_tenant(db, "ROLL_T", PLAIN_DB_PASSWORD)
        encrypt_script.apply(db, encrypt_script.plan(db))
        self.assertEqual(encrypt_script.rollback(db), 1)
        db.expire_all()
        self.assertEqual(db.query(Tenant).filter_by(tenant_uid="ROLL_T").one().database_password, PLAIN_DB_PASSWORD)
        self.assertEqual(encrypt_script.rollback(db), 0)


class TenantSchemaSyncOnFirstUse(unittest.TestCase):
    def test_a_missing_tenant_column_is_added_when_the_pool_is_created(self):
        legacy = declarative_base()

        class OldTrainee(legacy):  # the trainee table as it was before tokenVersion
            __tablename__ = "trainee"
            id = Column(Integer, primary_key=True)

        engine = create_engine("sqlite://", poolclass=StaticPool)
        legacy.metadata.create_all(engine)
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO trainee (id) VALUES (1)"))  # a row from before the column existed
        with patch.object(settings, "TESTING", False):
            TenantConnectionManager._sync_schema("OLD_T", engine)
        self.assertIn("tokenVersion", {c["name"] for c in inspect(engine).get_columns("trainee")})
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text('SELECT "tokenVersion" FROM trainee WHERE id = 1')).scalar(), 0)

    def test_tests_never_run_schema_changes(self):
        engine = create_engine("sqlite://", poolclass=StaticPool)
        with patch("app.database.tenant.sync_missing_columns") as sync:
            TenantConnectionManager._sync_schema("ANY", engine)  # TESTING is on in this suite
        sync.assert_not_called()


class PlacementRules(FixesTestCase):
    """Rule 1 (trainer registering a trainee) and rule 2 (admin assigning trainers)."""

    def register(self, who, n, trainer="trainer1", zone="North Zone"):
        body = {"traineeUid": f"TR-P-{n}", "fullName": "New Person", "designation": "Promoter", "gender": "Male",
                "primaryEmail": f"p{n}@example.com", "primaryPhone": f"91234567{n:02d}", "state": "Delhi", "zone": zone,
                "region": "North 1", "requestedBy": "Quess", "trainerId": trainer,
                "trainerName": "T", "supervisorId": "s", "supervisorName": "S", "jobStatus": "Active",
                "username": f"placement{n}", "password": "Correct-Horse-9"}
        return self.w.client.post("/admin/trainees", json=body, headers=self.w.headers(who)).status_code

    def test_a_trainer_registers_trainees_for_their_own_company_only(self):
        self.assertEqual(self.register("trainer1", 1), 201)                          # self
        self.assertEqual(self.register("trainer1", 2, trainer="trainer2"), 201)      # same-company trainer
        self.assertEqual(self.register("trainer1", 3, trainer="trainer3"), 403)      # Other Co trainer
        self.assertEqual(self.register("trainer3", 4, trainer="trainer3"), 403)      # an Other Co trainer: not this tenant's company
        self.assertEqual(self.register("trainer1", 5, trainer="ghost"), 403)         # not a trainer here

    def test_an_admin_assigns_only_trainers_from_companies_in_their_grant(self):
        self.assertEqual(self.register("coadmin", 6, trainer="trainer3"), 403)       # Other Co trainer
        self.assertEqual(self.register("coadmin", 7, trainer="trainer2"), 201)
        self.assertEqual(self.register("super", 8, trainer="trainer3"), 201)         # super: any trainer in the tenant
        create = {"conferenceDate": "2026-10-01", "conferenceTime": "10:00 AM",
                  "zone": "North Zone", "trainerEmployeeId": "trainer3"}
        self.assertEqual(self.w.client.post("/admin/trainings", json=create, headers=self.w.headers("coadmin")).status_code, 403)


class PartialTrainingPatch(FixesTestCase):
    """Rule 3: PATCH changes only the fields sent, and the merged result is authorized."""

    def patch(self, who, key, body):
        return self.w.client.patch(f"/admin/trainings/{uid(key)}", json=body, headers=self.w.headers(who))

    def row(self, key):
        self.alpha.expire_all()
        return self.alpha.query(Conference).filter(Conference.conferenceUid == uid(key)).one()

    def test_only_the_sent_fields_change(self):
        before = self.row("S_S1")
        place = (before.company, before.zone, before.region, before.trainerEmployeeId, before.conferenceDate)
        self.assertEqual(self.patch("coadmin", "S_S1", {"conferenceTime": "12:30 PM"}).status_code, 200)
        after = self.row("S_S1")
        self.assertEqual(after.conferenceTime, "12:30")                              # stored the other system's way (24-hour)
        self.assertEqual((after.company, after.zone, after.region, after.trainerEmployeeId, after.conferenceDate), place)

    def test_the_merged_result_must_stay_inside_the_grant(self):
        # The company isn't editable (it is the tenant's): an edit that sends one is refused.
        self.assertEqual(self.patch("coadmin", "S_S1", {"company": "Other Co"}).status_code, 422)
        self.assertEqual(self.patch("coord", "S_N1", {"zone": "South Zone"}).status_code, 403)
        self.assertEqual(self.patch("coadmin", "S_S1", {"trainerEmployeeId": "trainer3"}).status_code, 403)
        self.assertEqual(self.row("S_S1").company, "Samsung India")

    def test_date_and_time_can_be_left_out_but_not_blanked(self):
        self.assertEqual(self.patch("coadmin", "S_S1", {"approvalStatus": "Approved", "message": "ok"}).status_code, 200)
        for field in ("conferenceDate", "conferenceTime"):
            with self.subTest(field=field):
                self.assertEqual(self.patch("coadmin", "S_S1", {field: None}).status_code, 422)
                self.assertEqual(self.patch("coadmin", "S_S1", {field: "  "}).status_code, 422)

    def test_the_full_edit_form_still_works(self):
        row = self.row("S_N1")
        form = {"zone": row.zone, "region": row.region, "trainerEmployeeId": row.trainerEmployeeId,
                "trainerName": row.trainerName, "conferenceDate": "2026-10-05", "conferenceTime": "11:00 AM",
                "isResidential": False, "sessionFlow": None, "venue": None, "checklist": []}
        self.assertEqual(self.patch("coord", "S_N1", form).status_code, 200)
        self.assertEqual(self.row("S_N1").conferenceDate, "2026-10-05")


class AttendanceResetRules(FixesTestCase):
    """Rule 4: a reset needs a reason and a running session, like a manual mark."""

    PATH = f"/admin/trainings/{uid('S_N1')}/attendance/TR-S_N1-0"

    def reset(self, body):
        return self.w.client.request("DELETE", self.PATH, json=body, headers=self.w.headers("trainer1"))

    def test_a_reason_is_required(self):
        self.set_status(uid("S_N1"), "Ongoing")
        for body in (None, {}, {"reason": ""}, {"reason": "   "}):
            with self.subTest(body=body):
                self.assertEqual(self.reset(body).status_code, 422)

    def test_only_while_the_session_is_running(self):
        for status in ("Scheduled", "Completed"):
            with self.subTest(status=status):
                self.set_status(uid("S_N1"), status)
                self.assertEqual(self.reset({"reason": "Wrong person"}).status_code, 409)
        self.assertIsNotNone(self.alpha.query(Attendance).filter_by(conferenceUid=uid("S_N1"), traineeUid="TR-S_N1-0").first())

    def test_a_valid_reset_is_logged_with_its_reason(self):
        self.set_status(uid("S_N1"), "Ongoing")
        self.assertEqual(self.reset({"reason": "Marked the wrong person"}).status_code, 200)
        remarks = [r.remarks for r in self.alpha.query(LogsMaster).filter(LogsMaster.action == "RESET_ATTENDANCE")]
        self.assertEqual(remarks, [f"Reset attendance of TR-S_N1-0 for {uid('S_N1')}: Marked the wrong person"])


class MediaPlanEndpoint(FixesTestCase):
    """GET /admin/maintenance/media-plan - the migration report for a host without a shell."""

    def setUp(self):
        super().setUp()
        import tempfile
        from pathlib import Path

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        root = patch("app.services.media_migration.MEDIA_ROOT", self.root)
        root.start()
        self.addCleanup(root.stop)
        for relative in ("trainee_photos/TR-S_N1-0.jpg", "trainee_photos/orphan.jpg"):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            (self.root / relative).write_bytes(b"synthetic")
        self.alpha.query(Trainee).filter(Trainee.traineeUid == "TR-S_N1-0").update({"profilePhoto": "trainee_photos/TR-S_N1-0.jpg"})
        self.alpha.commit()

    def test_a_super_admin_gets_the_plan_and_nothing_moves(self):
        before = sorted(p.as_posix() for p in self.root.rglob("*"))
        with patch.object(settings, "DEFAULT_TENANT_ID", ALPHA):
            response = self.get("super", "/admin/maintenance/media-plan")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["dryRun"])
        actions = {e["path"]: (e["action"], e["tenants"]) for e in body["entries"]}
        self.assertEqual(actions["trainee_photos/TR-S_N1-0.jpg"], ("MOVE", [ALPHA]))
        self.assertEqual(actions["trainee_photos/orphan.jpg"][0], "SKIP_ORPHAN")
        self.assertEqual(sorted(p.as_posix() for p in self.root.rglob("*")), before)

    def test_everyone_else_is_refused(self):
        for who in ("coadmin", "coord", "trainer1", "adm_trainer"):
            with self.subTest(who=who):
                self.assertEqual(self.get(who, "/admin/maintenance/media-plan").status_code, 403)
        phone = self.alpha.query(Trainee).filter(Trainee.traineeUid == "TR-S_N1-0").one().phone
        trainee = create_access_token(subject=str(phone), tenant_id=ALPHA, role="trainee")
        response = self.w.client.get("/admin/maintenance/media-plan", headers={"Authorization": f"Bearer {trainee}"})
        self.assertEqual(response.status_code, 401)
