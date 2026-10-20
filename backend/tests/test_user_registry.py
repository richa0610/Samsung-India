"""The central user registry, Phase 1 (user, 2026-10-19): every trainee and trainer of every company
in the shared Common Database, written when this app registers or changes someone and brought in line
with each company by the sync. Login doesn't use it yet (Phase 2).

Synthetic TenantWorld (in-memory SQLite) only - no real database is touched."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

from app.core import rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.database.tenant import tenant_manager
from app.models.agency_team import AgencyTeam
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.models.uid_sequence import UidSequence
from app.services import user_registry_service as registry_service
from app.utils import uid as uid_utils
from tests.tenant_fixtures import ALPHA, BETA
from tests.test_trainer_authorization import TrainerWorldTestCase


class RegistryTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        rate_limit.reset()
        self.addCleanup(rate_limit.reset)
        # The world stubs ID generation; these tests need the real counters, the shared one included.
        real_ids = patch("app.models.uid_events.next_uid", uid_utils.next_uid)
        real_ids.start()
        self.addCleanup(real_ids.stop)
        self.common = self.w.common
        self.beta = self.w.tenant_db[BETA]
        self.count = 0

    def self_register(self, tenant=ALPHA, **extra):
        self.count += 1
        body = {"name": "New Person", "phone": 9_700_000_000 + self.count, "email": f"new{self.count}@example.com",
                "state": "Delhi", **extra}
        return self.w.client.post("/trainees/register", json=body, headers={"X-Tenant-ID": tenant})

    def staff_register(self, **extra):
        self.count += 1
        n = self.count
        body = {"fullName": "New Person", "designation": "Promoter", "gender": "Male", "primaryEmail": f"p{n}@example.com",
                "primaryPhone": f"91234567{n:02d}", "state": "Delhi", "zone": "North Zone", "region": "North 1",
                "requestedBy": "Quess", "trainerId": "trainer1", "trainerName": "T", "supervisorId": "s",
                "supervisorName": "S", "jobStatus": "Active", "username": f"placement{n}", "password": "Correct-Horse-9",
                **extra}
        return self.w.client.post("/admin/trainees", json=body, headers=self.w.headers("trainer1"))

    def entry(self, user_uid):
        self.common.expire_all()
        return self.common.query(UserRegistry).filter(UserRegistry.user_uid == user_uid).one_or_none()

    def entries(self):
        self.common.expire_all()
        return self.common.query(UserRegistry).all()

    def record(self, db, user_uid):
        db.expire_all()
        return db.query(Trainee).filter(Trainee.traineeUid == user_uid).one_or_none()

    def add_entry(self, **fields):
        row = UserRegistry(**{"tenant_uid": BETA, "user_type": "trainee", "status": "active", **fields})
        self.common.add(row)
        self.common.commit()
        return row

    def sync(self, db=None, tenant=ALPHA, **kwargs):
        return registry_service.reconcile_tenant(self.common, db or self.alpha, tenant, **kwargs)


class RegistrationWritesTheRegistry(RegistryTestCase):
    def test_a_staff_registration_leaves_an_active_entry_matching_the_company_record(self):
        response = self.staff_register(username="Placement.One")
        self.assertEqual(response.status_code, 201, response.text)
        uid = response.json()["traineeUid"]
        record, entry = self.record(self.alpha, uid), self.entry(uid)
        self.assertEqual(
            (entry.tenant_uid, entry.user_type, entry.username, entry.phone, entry.status, entry.max_devices),
            (ALPHA, "trainee", "placement.one", record.phone, "active", 2),
        )
        self.assertEqual(entry.password_hash, record.password)

    def test_registered_without_a_username_the_trainee_s_id_is_it(self):
        uid = self.staff_register(username=None).json()["traineeUid"]
        self.assertEqual(self.record(self.alpha, uid).username, uid)
        self.assertEqual(self.entry(uid).username, uid.lower())

    def test_a_self_registration_leaves_an_active_entry_without_a_password(self):
        response = self.self_register(employee_id=" HO-New-1 ")
        self.assertEqual(response.status_code, 201, response.text)
        entry = self.entry(response.json()["trainee"]["traineeUid"])
        self.assertEqual((entry.status, entry.password_hash, entry.hoid, entry.username), ("active", None, "ho-new-1", None))


class IdsNeverRepeatAcrossCompanies(RegistryTestCase):
    def test_two_companies_take_consecutive_ids_from_the_shared_counter(self):
        first = self.self_register(ALPHA).json()["trainee"]["traineeUid"]
        second = self.self_register(BETA).json()["trainee"]["traineeUid"]
        self.assertNotEqual(first, second)
        self.assertEqual(uid_utils.serial_of(second, "TRN"), uid_utils.serial_of(first, "TRN") + 1)

    def test_the_shared_counter_starts_above_every_company_s_numbers(self):
        self.alpha.add(UidSequence(prefix="TRN", next_val=10050))   # ALPHA's own counter
        self.alpha.commit()
        self.beta.add(Trainee(traineeUid="TRN2610077", name="B", email="b77@example.test", phone=9_600_000_077))  # an ID BETA carries
        self.beta.commit()
        uid = self.self_register(ALPHA).json()["trainee"]["traineeUid"]
        self.assertEqual(uid_utils.serial_of(uid, "TRN"), 10078)

    def test_a_company_that_can_t_be_read_refuses_the_first_registration(self):
        real = tenant_manager.get_session

        def beta_is_down(tenant_uid, common_db=None):
            if tenant_uid == BETA:
                raise HTTPException(status_code=503, detail="down")
            return real(tenant_uid, common_db)

        with patch.object(tenant_manager, "get_session", side_effect=beta_is_down):
            response = self.self_register(ALPHA)
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(self.entries(), [])
        self.assertIsNone(self.alpha.query(Trainee).filter(Trainee.email == "new1@example.com").first())


class ClashesAreRefusedBeforeAnythingIsSaved(RegistryTestCase):
    def test_a_username_another_company_holds_is_refused(self):
        self.add_entry(user_uid="TRN-BETA-1", username="taken.name")
        response = self.staff_register(username=" Taken.Name ")
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], registry_service.USERNAME_TAKEN)
        self.assertEqual([entry.user_uid for entry in self.entries()], ["TRN-BETA-1"])
        self.assertIsNone(self.alpha.query(Trainee).filter(Trainee.email == "p1@example.com").first())

    def test_an_ho_id_another_company_holds_is_refused(self):
        self.add_entry(user_uid="TRN-BETA-1", hoid="ho-123")
        response = self.self_register(employee_id="HO-123")
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], registry_service.HOID_TAKEN)

    def test_a_race_lost_at_the_database_is_a_clean_refusal(self):
        real = registry_service.ensure_available
        calls = []

        def another_registration_wins(common_db, **kwargs):
            if not calls:   # this request checked just before the other one saved
                calls.append(1)
                common_db.add(UserRegistry(tenant_uid=BETA, user_type="trainee", user_uid="TRN-OTHER", username="racer", status="active"))
                common_db.commit()
                return
            return real(common_db, **kwargs)

        with patch.object(registry_service, "ensure_available", side_effect=another_registration_wins):
            response = self.staff_register(username="Racer")
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], registry_service.USERNAME_TAKEN)
        self.assertEqual([entry.user_uid for entry in self.entries()], ["TRN-OTHER"])
        self.assertIsNone(self.alpha.query(Trainee).filter(Trainee.email == "p1@example.com").first())


class HalfFinishedRegistrationsRecover(RegistryTestCase):
    def test_a_failed_company_save_releases_the_reservation(self):
        down = OperationalError("INSERT", {}, Exception("company database is down"))
        with patch("app.services.user_registry_service.trainee_repository.create", side_effect=down):
            response = self.staff_register()
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(self.entries(), [])

    def test_a_failed_activation_says_so_and_the_sync_finishes_it(self):
        down = OperationalError("UPDATE", {}, Exception("common database blipped"))
        with patch.object(registry_service, "_activate", side_effect=down):
            response = self.staff_register()
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(response.json()["detail"], registry_service.NOT_READY)
        (entry,) = self.entries()
        self.assertEqual(entry.status, "pending")
        self.assertIsNotNone(self.record(self.alpha, entry.user_uid))

        self.sync()
        self.assertEqual(self.entry(entry.user_uid).status, "active")

    def test_the_sync_removes_a_reservation_that_never_finished_and_keeps_a_fresh_one(self):
        self.add_entry(tenant_uid=ALPHA, user_uid="TRN2699998", status="pending", created_at=datetime.utcnow() - timedelta(minutes=10))
        self.add_entry(tenant_uid=ALPHA, user_uid="TRN2699999", status="pending")
        self.assertEqual(self.sync().removed, 1)
        self.assertIsNone(self.entry("TRN2699998"))
        self.assertEqual(self.entry("TRN2699999").status, "pending")


class ProfileChangesReachTheRegistry(RegistryTestCase):
    def trainee_headers(self, phone):
        return {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=ALPHA, role='trainee')}"}

    def registered(self):
        uid = self.self_register().json()["trainee"]["traineeUid"]
        return uid, self.trainee_headers(self.record(self.alpha, uid).phone)

    def test_a_trainee_s_new_phone_and_ho_id_are_copied(self):
        uid, headers = self.registered()
        response = self.w.client.patch("/trainees/me", json={"phone": 9_755_555_555, "employee_id": "HO-777"}, headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        entry = self.entry(uid)
        self.assertEqual((entry.phone, entry.hoid), (9_755_555_555, "ho-777"))

    def test_an_ho_id_another_company_holds_is_refused_and_nothing_changes(self):
        uid, headers = self.registered()
        self.add_entry(user_uid="TRN-BETA-1", hoid="ho-999")
        response = self.w.client.patch("/trainees/me", json={"employee_id": "HO-999"}, headers=headers)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(response.json()["detail"], registry_service.HOID_TAKEN)
        self.assertIsNone(self.record(self.alpha, uid).employee_id)

    def test_a_trainer_s_new_password_is_copied(self):
        response = self.w.client.patch("/admin/profile", json={"password": "Brand-New-7"}, headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        entry = self.entry("g1")
        self.assertEqual((entry.tenant_uid, entry.user_type, entry.status), (ALPHA, "trainer", "active"))
        self.assertTrue(verify_password("Brand-New-7", entry.password_hash))


class TheSyncMatchesEachCompany(RegistryTestCase):
    def company_accounts(self):
        return self.alpha.query(Trainee).count() + self.alpha.query(AgencyTeam).count()

    def test_a_dry_run_reports_and_writes_nothing(self):
        report = self.sync(apply=False)
        self.assertEqual(report.added, self.company_accounts())
        self.assertEqual(self.entries(), [])

    def test_every_account_is_added_under_its_company_and_a_second_run_changes_nothing(self):
        self.sync()
        entries = self.entries()
        self.assertEqual(len(entries), self.company_accounts())
        self.assertEqual({entry.tenant_uid for entry in entries}, {ALPHA})
        trainer = self.entry("g1")
        self.assertEqual((trainer.user_type, trainer.username, trainer.hoid, trainer.status), ("trainer", "trainer1", "off1", "active"))
        self.assertEqual(self.entry("TR-S_N1-0").password_hash, self.record(self.alpha, "TR-S_N1-0").password)

        again = self.sync()
        self.assertEqual((again.added, again.updated, again.unchanged), (0, 0, self.company_accounts()))

    def test_company_side_changes_are_copied_and_a_vanished_account_is_disabled(self):
        self.sync()
        leaving = self.record(self.alpha, "TR-S_S1-1")   # read first: record() expires unsaved changes
        self.w.agency["trainer1"].password = hash_password("Changed-Elsewhere-1")   # as the PHP system would
        self.alpha.delete(leaving)
        self.alpha.commit()

        report = self.sync()
        self.assertEqual((report.updated, report.disabled), (1, 1))
        self.assertTrue(verify_password("Changed-Elsewhere-1", self.entry("g1").password_hash))
        gone = self.entry("TR-S_S1-1")
        self.assertEqual(gone.status, "disabled")
        self.assertTrue(gone.remarks.startswith(registry_service.SYNC_REMARK))

    def test_a_row_an_admin_disabled_stays_disabled(self):
        self.sync()
        entry = self.entry("TR-S_N1-0")
        entry.status, entry.remarks = "disabled", "admin: left the company"
        self.common.commit()
        self.sync()
        entry = self.entry("TR-S_N1-0")
        self.assertEqual((entry.status, entry.remarks), ("disabled", "admin: left the company"))

    def test_an_agency_account_without_the_trainer_role_is_disabled_until_it_has_it_again(self):
        trainer3 = self.w.agency["trainer3"]
        trainer3.role = "manager"
        self.alpha.commit()
        self.sync()
        self.assertEqual(self.entry("g3").status, "disabled")

        trainer3.role = "Trainer"
        self.alpha.commit()
        self.sync()
        entry = self.entry("g3")
        self.assertEqual((entry.status, entry.remarks), ("active", None))

    def test_an_id_or_username_another_company_holds_is_skipped_and_reported(self):
        self.beta.add(Trainee(traineeUid="TR-S_N1-0", name="Copy", email="copy@example.test", phone=9_600_000_001))
        self.beta.add(Trainee(traineeUid="TR-BETA-NEW", name="Same", email="same@example.test", phone=9_600_000_002, username="USER1"))
        self.beta.commit()
        self.sync()
        report = self.sync(self.beta, BETA)
        self.assertIn(("TR-S_N1-0", f"ID already registered to company {ALPHA}"), report.skipped)
        self.assertIn(("TR-BETA-NEW", "username already used by TR-S_N1-0"), report.skipped)
        self.assertEqual(self.entry("TR-S_N1-0").tenant_uid, ALPHA)
        newcomer = self.entry("TR-BETA-NEW")
        self.assertEqual((newcomer.tenant_uid, newcomer.username), (BETA, None))


class CompanySessionsAreClosed(RegistryTestCase):
    def tracked(self, sessions):
        real = tenant_manager.get_session

        def open_and_track(tenant_uid, common_db=None):
            session = real(tenant_uid, common_db)
            session.close = Mock(wraps=session.close)
            sessions.append((tenant_uid, session))
            return session
        return open_and_track

    def test_the_sync_of_every_company_closes_each_session_it_opens(self):
        sessions = []
        reports = registry_service.reconcile_all(self.common, lambda uid: self.tracked(sessions)(uid, self.common))
        self.assertEqual({report.tenant_uid for report in reports}, {ALPHA, BETA})
        self.assertTrue(sessions and all(session.close.called for _uid, session in sessions))

    def test_starting_the_shared_counter_closes_the_company_sessions_it_reads(self):
        sessions = []
        with patch.object(tenant_manager, "get_session", side_effect=self.tracked(sessions)):
            self.assertEqual(self.self_register(ALPHA).status_code, 201)
        self.assertIn(BETA, [uid for uid, _session in sessions])   # every company was read
        self.assertTrue(all(session.close.called for _uid, session in sessions))
