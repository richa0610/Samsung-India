"""Trainer Flow Phase 2.2 - remaining security gaps closeout.

- The admin dashboard's trainer pool follows the caller's tenant and every rule of their grant.
- Database errors never carry bound parameters (phones, emails, password hashes) into logs.
- WebSocket tokens in query strings are masked in uvicorn's log lines.
- The media migration planner assigns files only from database references, and only plans.

Synthetic TenantWorld (in-memory SQLite) and temporary folders only.
"""

import logging
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.log_redaction import TokenRedactionFilter, install_token_redaction, redact
from app.core.security import hash_password
from app.database.common import common_engine
from app.database.connection import SAFE_ENGINE_OPTIONS, engine as default_engine
from app.database.tenant import tenant_manager
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.common.tenant_registry import Tenant
from app.models.trainee import Trainee
from scripts import plan_media_tenant_migration as planner
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD
from tests.test_trainer_authorization import TrainerWorldTestCase

SECRET_PHONE = "9876501234"


class DashboardTrainerPool(TrainerWorldTestCase):
    """ALPHA agency trainers: trainer1, trainer2 (Samsung India), trainer3 (Other Co), plus
    trainer4 (Third Co, added here). Admin-table trainers: adm_trainer (ALPHA grant, no company)
    and beta_trainer (BETA grant only, Samsung India)."""

    def setUp(self):
        super().setUp()
        self.alpha.add(AgencyTeam(agencyTeamUid="g4", username="trainer4", name="Trainer4", password=hash_password(PASSWORD),
                                  role="trainer", company="Third Co"))
        self.alpha.commit()
        beta_trainer = Admin(adminUid="a-bt", username="beta_trainer", name="Beta Trainer", password=hash_password(PASSWORD),
                             role="trainer", company="Samsung India")
        two = Admin(adminUid="a-two", username="twoco", name="Two Co", password=hash_password(PASSWORD), role="admin")
        self.w.common.add_all([beta_trainer, two])
        self.w.common.flush()
        self.w.grant(beta_trainer, "trainer", BETA)
        self.w.grant(two, "company_admin", ALPHA, "Other Co")
        self.w.grant(two, "coordinator", ALPHA, "Samsung India", zone="North Zone")
        self.w.common.commit()
        self.w.admins["twoco"] = two

    def pool(self, who, tenant=ALPHA):
        response = self.get(who, "/admin/dashboard/stats?fresh=true", tenant)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["trainers"]["pool"]

    def test_a_super_admin_counts_this_tenants_trainers_only(self):
        # trainer1-4 + adm_trainer; beta_trainer holds a grant for BETA only.
        self.assertEqual(self.pool("super"), 5)

    def test_a_company_admin_counts_their_company_only(self):
        self.assertEqual(self.pool("coadmin"), 2)  # trainer1, trainer2

    def test_a_grant_spanning_two_companies_counts_both_and_nothing_else(self):
        # Used to count every company (a multi-company grant fell back to "unrestricted").
        self.assertEqual(self.pool("twoco"), 3)  # trainer1, trainer2 (Samsung India) + trainer3 (Other Co)

    def test_another_tenants_admin_sees_only_their_tenant(self):
        self.assertEqual(self.pool("betaonly", BETA), 1)  # beta_trainer; ALPHA's trainers never counted


class DatabaseErrorsHideParameters(unittest.TestCase):
    def test_every_app_engine_hides_parameters(self):
        self.assertTrue(common_engine.hide_parameters)
        self.assertTrue(default_engine.hide_parameters)

    def test_a_tenant_engine_hides_parameters(self):
        world_common = sessionmaker(bind=create_engine("sqlite://", poolclass=StaticPool))()
        Tenant.__table__.create(world_common.get_bind())
        world_common.add(Tenant(tenant_uid="GAMMA", company_name="Gamma", database_host="127.0.0.1", database_port=1,
                                database_name="gamma", database_username="u", database_password="p", status="active"))
        world_common.commit()
        try:
            engine = tenant_manager.get_engine("GAMMA", world_common)  # lazy: nothing connects
            self.assertTrue(engine.hide_parameters)
        finally:
            tenant_manager._engines.pop("GAMMA", None)
            tenant_manager._sessionmakers.pop("GAMMA", None)
            tenant_manager.clear_status_cache()

    def test_an_error_message_does_not_contain_the_values(self):
        Base = declarative_base()

        class Row(Base):
            __tablename__ = "rows"
            id = Column(Integer, primary_key=True)
            phone = Column(String(20), unique=True)

        engine = create_engine("sqlite://", **SAFE_ENGINE_OPTIONS)
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        db.add(Row(phone=SECRET_PHONE))
        db.commit()
        db.add(Row(phone=SECRET_PHONE))
        with self.assertRaises(IntegrityError) as caught:
            db.commit()
        self.assertNotIn(SECRET_PHONE, str(caught.exception))


class WebSocketTokensAreMaskedInLogs(unittest.TestCase):
    TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.c2lnbmF0dXJl"

    def format(self, msg, *args):
        record = logging.LogRecord("uvicorn.error", logging.INFO, __file__, 1, msg, args, None)
        TokenRedactionFilter().filter(record)
        return record.getMessage()

    def test_a_handshake_line_never_carries_the_token(self):
        for path in (f"/ws/live/CONF-1?token={self.TOKEN}", f"/ws/admin?token={self.TOKEN}", f"/ws/admin?x=1&token={self.TOKEN}&y=2"):
            with self.subTest(path=path):
                line = self.format('%s - "WebSocket %s" [accepted]', "10.0.0.1:5000", path)
                self.assertNotIn(self.TOKEN, line)
                self.assertIn("token=[REDACTED]", line)
        self.assertNotIn(self.TOKEN, self.format(f'"WebSocket /ws/admin?access_token={self.TOKEN}" 403'))

    def test_other_query_values_are_untouched(self):
        self.assertEqual(redact("/admin/trainings/page?approval=pending&limit=10"), "/admin/trainings/page?approval=pending&limit=10")

    def test_the_filter_is_on_uvicorns_loggers_once_the_app_is_loaded(self):
        import app.main  # noqa: F401 - installs it

        install_token_redaction()  # idempotent
        for name in ("uvicorn.error", "uvicorn.access"):
            filters = [f for f in logging.getLogger(name).filters if isinstance(f, TokenRedactionFilter)]
            self.assertEqual(len(filters), 1, name)


class MediaMigrationPlanner(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def put(self, relative):
        (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
        (self.root / relative).write_bytes(b"synthetic")

    def test_every_file_gets_exactly_one_action_from_the_database_references(self):
        files = {
            "trainee_photos/TR-S_N1-0.jpg": "MOVE",
            "trainer_documents/aadhar/agency_1.pdf": "FLAG_AMBIGUOUS",
            "trainee_photos/nobody.jpg": "SKIP_ORPHAN",
            "trainer_photos/default_male.png": "SHARED",
            "admin_profile/admin_7.png": "FLAG_ACCOUNT_FILE",
            "attendance_sheets/CONF-S_N1.pdf": "FLAG_CONFLICT",
        }
        for path in files:
            self.put(path)
        self.put(f"{ALPHA}/attendance_sheets/CONF-S_N1.pdf")  # already migrated copy
        references = {
            ALPHA: {"trainee_photos/TR-S_N1-0.jpg", "trainer_documents/aadhar/agency_1.pdf", "attendance_sheets/CONF-S_N1.pdf"},
            BETA: {"trainer_documents/aadhar/agency_1.pdf"},
        }
        entries = planner.plan(self.root, references, {"admin_profile/admin_7.png": {ALPHA, "*"}})
        self.assertEqual({e.path: e.action for e in entries}, files)
        by_path = {e.path: e for e in entries}
        self.assertEqual(by_path["trainee_photos/TR-S_N1-0.jpg"].tenants, [ALPHA])
        self.assertEqual(by_path["trainer_documents/aadhar/agency_1.pdf"].tenants, [ALPHA, BETA])

    def test_planning_never_changes_the_folder(self):
        self.put("trainee_photos/TR-S_N1-0.jpg")
        before = sorted(p.as_posix() for p in self.root.rglob("*"))
        planner.plan(self.root, {ALPHA: {"trainee_photos/TR-S_N1-0.jpg"}}, {})
        self.assertEqual(sorted(p.as_posix() for p in self.root.rglob("*")), before)

    def test_tenant_folders_and_unknown_folders_are_not_legacy_files(self):
        self.put(f"{ALPHA}/trainee_photos/x.jpg")
        self.put("random/thing.txt")
        self.assertEqual(planner.legacy_files(self.root), [])

    def test_references_are_read_from_every_upload_column(self):
        self.alpha.query(Trainee).filter(Trainee.traineeUid == "TR-S_N1-0").update({"profilePhoto": "trainee_photos/a.jpg"})
        self.alpha.query(Attendance).filter(Attendance.attendanceUid == "ATT-S_N1-0").update({"checkInPhoto": "attendance_photos/b.jpg"})
        self.alpha.query(AgencyTeam).filter(AgencyTeam.username == "trainer1").update({"aadharImage": "trainer_documents/aadhar/agency_1.pdf"})
        self.alpha.commit()
        self.assertEqual(
            planner.collect_tenant_references(self.alpha),
            {"trainee_photos/a.jpg", "attendance_photos/b.jpg", "trainer_documents/aadhar/agency_1.pdf"},
        )

    def test_account_files_list_the_accounts_granted_tenants(self):
        self.w.admins["coadmin"].profilePhoto = "admin_profile/admin_2.png"
        self.w.admins["super"].aadharImage = "trainer_documents/aadhar/admin_1.pdf"
        self.w.common.commit()
        references = planner.collect_account_references(self.w.common)
        self.assertEqual(references["admin_profile/admin_2.png"], {ALPHA})
        self.assertEqual(references["trainer_documents/aadhar/admin_1.pdf"], {planner.ALL_TENANTS})
