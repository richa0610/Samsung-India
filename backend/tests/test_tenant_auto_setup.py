"""Automatic company setup (user, 2026-10-22): a `tenants` row added with just a company name gets
its own database through cPanel's API, the app's tables, the default company's dropdown lists and
its connection details - nothing is served for it until then.

Synthetic TenantWorld (in-memory SQLite) with cPanel and the new company databases stood in for -
no real database or cPanel is touched."""

import json
import re

import httpx
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.secret_box import decrypt_secret
from app.database.schema_sync import relax_columns
from app.database.tenant import NOT_SET_UP, tenant_manager
from app.models.agency import Agency
from app.models.category import Category, SubCategory
from app.models.common.tenant_registry import Tenant
from app.repositories import tenant_repository
from app.services import tenant_directory, tenant_setup
from app.services.cpanel_client import CpanelClient, CpanelError
from tests.tenant_fixtures import ALPHA, BETA
from tests.test_trainer_authorization import TrainerWorldTestCase

CONFIG = tenant_setup.SetupConfig(
    cpanel_url="https://cpanel.example.test:2083", cpanel_user="mmtbtwob", cpanel_token="TOKEN-123", verify_tls=True,
    db_host="db.example.test", db_port=3306, db_user="mmtbtwob_app", db_password="Db-Pass-9", name_prefix="mmtbtwob_tops_",
)


class FakeCpanel:
    """Stands in for cPanel: records each call; `fail` makes create_database refuse once per entry."""

    def __init__(self, fail=(), exists=False):
        self.calls, self.fail, self.exists = [], list(fail), exists

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def create_database(self, name):
        self.calls.append(("create_database", name))
        if self.fail:
            raise CpanelError(self.fail.pop(0))
        return not self.exists

    def grant_all(self, user, database):
        self.calls.append(("grant_all", user, database))


class AutoSetupTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        tenant_setup._resting.clear()
        self.addCleanup(tenant_setup._resting.clear)
        self.common = self.w.common
        self.cpanel = FakeCpanel()
        self.databases = {}
        for code, zone in (("N", "North"), ("S", "South")):   # the default company's dropdown lists
            self.alpha.add(Category(categoryUid=f"CAT-{code}", name=zone, visibleOnWeb="Zone", status="Approved"))
            self.alpha.add(SubCategory(subCategoryUid=f"SUB-{code}1", categoryUid=f"CAT-{code}", subCategory=f"{zone} 1",
                                       visibleOnWeb="No", status="Approved"))
        self.alpha.commit()

    def open_engine(self, url):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.databases[url.database] = engine
        engine.dispose = lambda: None   # kept open so the test can look inside
        return engine

    def add_row(self, **columns):
        """As a person adds one in DBeaver - plain SQL, no app code filling anything in."""
        columns = {"company_name": "Acme Retail", **columns}
        names = ", ".join(columns)
        self.common.execute(text(f"INSERT INTO tenants ({names}) VALUES ({', '.join(':' + c for c in columns)})"), columns)
        self.common.commit()
        return self.common.query(Tenant).filter(Tenant.company_name == columns["company_name"]).one()

    def run_setup(self, config=CONFIG):
        return tenant_setup.set_up_pending(self.common, config=config, cpanel_factory=lambda _c: self.cpanel,
                                           open_engine=self.open_engine, default_engine=lambda: self.w.alpha_engine)

    def row(self, company="Acme Retail"):
        self.common.expire_all()
        return self.common.query(Tenant).filter(Tenant.company_name == company).one()


class ARowWithJustANameIsSetUp(AutoSetupTestCase):
    def test_it_gets_an_id_a_database_its_tables_lists_and_details(self):
        self.common.add(Agency(agencyUid="AGY2611111", companyName="ACME retail", name="Contact", status="Approved"))
        self.common.commit()
        self.add_row()
        finished = self.run_setup()

        row = self.row()
        self.assertRegex(row.tenant_uid, r"^TEN_ACM_\d{7}$")
        name = f"mmtbtwob_tops_{row.tenant_uid.lower()}"
        self.assertEqual(finished, [row.tenant_uid])
        self.assertEqual((row.database_host, row.database_port, row.database_name, row.database_username),
                         ("db.example.test", 3306, name, "mmtbtwob_app"))
        self.assertEqual(decrypt_secret(row.database_password), "Db-Pass-9")
        self.assertEqual((row.agency_uid, row.setup_error, row.status), ("AGY2611111", None, "active"))
        self.assertTrue(row.is_ready)
        self.assertEqual(self.cpanel.calls, [("create_database", name), ("grant_all", "mmtbtwob_app", name)])

        made = self.databases[name]
        self.assertTrue({"trainee", "conference", "agencyteam", "uid_sequence"} <= set(inspect(made).get_table_names()))
        with made.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM category")).scalar(), 2)
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM subcategory")).scalar(), 2)
        self.assertIn(row.tenant_uid, tenant_repository.list_active_uids(self.common))

    def test_an_id_typed_into_the_row_is_kept(self):
        self.add_row(tenant_uid="acme")
        self.run_setup()
        self.assertEqual((self.row().tenant_uid, self.row().database_name), ("acme", "mmtbtwob_tops_acme"))

    def test_a_database_left_by_an_interrupted_setup_is_used(self):
        self.cpanel.exists = True
        self.add_row(tenant_uid="acme")
        self.run_setup()
        self.assertTrue(self.row().is_ready)

    def test_a_row_with_only_part_of_its_database_details_is_set_up(self):
        self.add_row(tenant_uid="acme", database_name="typed_by_hand")   # no host, no login
        self.assertEqual(self.run_setup(), ["acme"])
        row = self.row()
        self.assertTrue(row.is_ready)
        self.assertEqual((row.database_host, row.database_name), ("db.example.test", "mmtbtwob_tops_acme"))

    def test_a_row_with_its_database_typed_in_only_gets_its_id(self):
        details = {"database_host": "other.example.test", "database_name": "acme_db", "database_username": "acme_user"}
        self.add_row(**details)
        finished = self.run_setup()
        row = self.row()
        self.assertRegex(row.tenant_uid, r"^TEN_ACM_\d{7}$")
        self.assertEqual(finished, [row.tenant_uid])
        self.assertEqual({column: getattr(row, column) for column in details}, details)
        self.assertTrue(row.is_ready)
        self.assertEqual(self.cpanel.calls, [])

    def test_the_companies_already_set_up_are_left_alone(self):
        before = {t.tenant_uid: (t.database_name, t.database_password) for t in self.common.query(Tenant)}
        self.add_row()
        self.run_setup()
        self.common.expire_all()
        after = {t.tenant_uid: (t.database_name, t.database_password) for t in self.common.query(Tenant) if t.tenant_uid in before}
        self.assertEqual(after, before)
        self.assertEqual(len([c for c in self.cpanel.calls if c[0] == "create_database"]), 1)


class UntilItIsSetUp(AutoSetupTestCase):
    def test_nothing_is_served_for_it(self):
        self.add_row(tenant_uid="acme")
        self.assertNotIn("acme", tenant_repository.list_active_uids(self.common))
        for attempt in (lambda: tenant_directory.lookup(self.common, "ACME"), lambda: tenant_manager.get_session("acme", self.common)):
            with self.assertRaises(HTTPException) as refused:
                attempt()
            self.assertEqual((refused.exception.status_code, refused.exception.detail), (503, NOT_SET_UP))
        self.assertEqual(self.w.client.get("/tenants/lookup", params={"code": "acme"}).status_code, 503)

    def test_an_inactive_row_waits(self):
        self.add_row(status="inactive")
        self.assertEqual(self.run_setup(), [])
        self.assertEqual(self.cpanel.calls, [])


class WhenItFails(AutoSetupTestCase):
    def test_the_reason_is_written_on_the_row_and_it_is_tried_again_later(self):
        self.cpanel.fail = ["cPanel Mysql::create_database: Your account has reached its limit of databases."]
        self.add_row(tenant_uid="acme")
        self.assertEqual(self.run_setup(), [])
        row = self.row()
        self.assertIn("limit of databases", row.setup_error)
        self.assertIsNone(row.database_name)

        self.run_setup()   # resting: not tried again straight away
        self.assertEqual(len(self.cpanel.calls), 1)

        tenant_setup._resting.clear()   # RETRY_MINUTES later
        self.assertEqual(self.run_setup(), ["acme"])
        self.assertEqual((self.row().setup_error, self.row().database_name), (None, "mmtbtwob_tops_acme"))

    def test_missing_settings_are_named_and_cpanel_is_never_called(self):
        self.add_row(tenant_uid="acme")
        made = []
        tenant_setup.set_up_pending(
            self.common, config=tenant_setup.SetupConfig(**{**CONFIG.__dict__, "cpanel_token": "", "db_password": ""}),
            cpanel_factory=lambda c: made.append(c) or self.cpanel, open_engine=self.open_engine,
        )
        self.assertEqual(made, [])
        self.assertIn("CPANEL_API_TOKEN, TENANT_DB_PASSWORD", self.row().setup_error)
        self.assertNotIn("TOKEN-123", self.row().setup_error)

    def test_one_company_failing_doesn_t_stop_the_next(self):
        self.cpanel.fail = ["quota"]
        self.add_row(company_name="First Co", tenant_uid="first")
        self.add_row(company_name="Second Co", tenant_uid="second")
        self.assertEqual(self.run_setup(), ["second"])
        self.assertEqual(self.row("First Co").setup_error, "quota")


class DatabaseNames(AutoSetupTestCase):
    def test_prefix_and_the_id_in_lower_case(self):
        self.assertEqual(tenant_setup.database_name("mmtbtwob_tops_", "TEN_SAM_2620001"), "mmtbtwob_tops_ten_sam_2620001")
        self.assertEqual(tenant_setup.database_name("p_", " Acme-Retail! "), "p_acme_retail")
        for bad in ("!!!", "x" * 60):
            with self.assertRaises(ValueError):
                tenant_setup.database_name("mmtbtwob_tops_", bad)


class TheCpanelClient(AutoSetupTestCase):
    def client(self, answer):
        self.seen = []

        def handle(request):
            self.seen.append(request)
            status, body = answer(request)
            return httpx.Response(status, content=json.dumps(body).encode())
        return CpanelClient("https://cpanel.example.test:2083/", "mmtbtwob", "TOKEN-123", transport=httpx.MockTransport(handle))

    def test_a_call_carries_the_token_as_a_header_only(self):
        with self.client(lambda _r: (200, {"status": 1, "errors": None, "data": None})) as cpanel:
            self.assertTrue(cpanel.create_database("mmtbtwob_tops_acme"))
            cpanel.grant_all("mmtbtwob_app", "mmtbtwob_tops_acme")
        first, second = self.seen
        self.assertEqual(first.headers["Authorization"], "cpanel mmtbtwob:TOKEN-123")
        self.assertEqual((first.url.path, first.url.params["name"]), ("/execute/Mysql/create_database", "mmtbtwob_tops_acme"))
        self.assertNotIn("TOKEN-123", str(first.url))
        self.assertEqual((second.url.params["user"], second.url.params["privileges"]), ("mmtbtwob_app", "ALL PRIVILEGES"))

    def test_an_existing_database_is_not_an_error_but_other_refusals_are(self):
        exists = {"status": 0, "errors": ["The database “mmtbtwob_tops_acme” already exists."]}
        with self.client(lambda _r: (200, exists)) as cpanel:
            self.assertFalse(cpanel.create_database("mmtbtwob_tops_acme"))
        with self.client(lambda _r: (200, {"status": 0, "errors": ["limit reached"]})) as cpanel:
            with self.assertRaisesRegex(CpanelError, "limit reached"):
                cpanel.create_database("x")

    def test_a_refused_token_says_so_without_repeating_it(self):
        with self.client(lambda _r: (401, {})) as cpanel:
            with self.assertRaises(CpanelError) as refused:
                cpanel.create_database("x")
        self.assertIn("API token", str(refused.exception))
        self.assertNotIn("TOKEN-123", str(refused.exception))


class TheLiveTableIsLoosenedOnlyOnMySQL(AutoSetupTestCase):
    def test_elsewhere_nothing_is_changed(self):
        self.assertEqual(relax_columns(self.w.common_engine, "tenants", tenant_setup.SHORT_ROW_COLUMNS), [])

    def test_the_companies_of_the_world_are_ready(self):
        self.assertEqual(set(tenant_repository.list_active_uids(self.common)), {ALPHA, BETA})
