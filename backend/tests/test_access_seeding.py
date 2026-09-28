"""Phase C step 2: the dry-run planner (app/services/access_seeding.py).

A synthetic copy of the live shape: account 1 = admin with no company (unrestricted today),
2 = trainer, 3-7 = Samsung India admins each limited to one zone via data_scopes. Nothing here
touches a real database, and the read-only tests prove the planner cannot write."""

import unittest
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import CommonBase, TenantBase
from app.models import *  # noqa: F401,F403
from app.models.admin import Admin
from app.models.admin_access import AccessBase, AdminAccess
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.data_scope import DataScope
from app.models.logs_master import LogsMaster
from app.services.access_seeding import Assignment, build_plan, is_read_statement, make_read_only, render_report
from app.services.access_service import company_admin_key

TENANT = "samsung"
USER_PLAN = [
    Assignment(1, "super_admin"), Assignment(2, "trainer"), Assignment(3, "company_admin", "Samsung India"),
    Assignment(4, "coordinator"), Assignment(5, "coordinator"), Assignment(6, "coordinator"), Assignment(7, "coordinator"),
]
ZONE_OF = {3: "North Zone", 4: "South Zone", 5: "East Zone", 6: "West Zone", 7: "North Zone"}


def mem():
    return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)


class SeedingWorld(unittest.TestCase):
    def setUp(self):
        # the models fill a missing UID with a MySQL-only statement; leave it empty in SQLite tests
        stub = patch("app.models.uid_events.next_uid", lambda connection, prefix: None)
        stub.start()
        self.addCleanup(stub.stop)
        self.common_engine, self.tenant_engine = self.make_engines()
        CommonBase.metadata.create_all(self.common_engine)
        TenantBase.metadata.create_all(self.tenant_engine)
        self.common = sessionmaker(bind=self.common_engine)()
        self.tenant = sessionmaker(bind=self.tenant_engine)()

        self.common.add(Tenant(tenant_uid=TENANT, company_name="Samsung", database_host="h", database_port=3306, database_name="d",
                               database_username="u", database_password="p", status="active"))

        def admin(admin_id, role, company):
            self.common.add(Admin(id=admin_id, adminUid=f"a{admin_id}", username=f"account{admin_id}", name=f"Account {admin_id}", password="hash",
                                  role=role, company=company, status="Active"))

        admin(1, "admin", None)
        admin(2, "trainer", None)
        for admin_id in (3, 4, 5, 6, 7):
            admin(admin_id, "admin", "Samsung India")
        self.common.commit()

        for admin_id, zone in ZONE_OF.items():
            self.tenant.add(DataScope(user_id=admin_id, table_type="admin", scope_type="zone", scope_value=zone))
        n = 0
        for zone in ("North Zone", "South Zone", "East Zone", "West Zone", None):
            for i in range(3):
                n += 1
                self.tenant.add(Conference(conferenceUid=f"C{n}", company="Samsung India", zone=zone, region=f"R{n}" if zone else None,
                                           trainerEmployeeId="account2" if n == 1 else "t9", conferenceDate="2026-09-20", conferenceStatus="Scheduled", status="Approved"))
        for _ in range(3):
            self.tenant.add(LogsMaster(username="account1", role="admin", action="LOGIN", timestamp=datetime(2026, 9, 20, 9, 0)))
        self.tenant.commit()
        self.total_conferences = 15

    def make_engines(self):
        return mem(), mem()

    def plan(self, assignments=USER_PLAN, confirmed=frozenset()):
        return build_plan(self.common, self.tenant, TENANT, assignments, confirmed)

    def levels(self, plan, level):
        return [f.text for f in plan.findings if f.level == level]


class PlanTests(SeedingWorld):
    def test_the_approved_assignments_produce_exactly_the_agreed_grants(self):
        plan = self.plan()
        self.assertEqual(self.levels(plan, "BLOCK"), [])
        rows = {(g.admin_id, g.role, g.zone, g.company, g.status) for g in plan.grants}
        self.assertEqual(rows, {
            (1, "super_admin", None, None, "held"),
            (2, "trainer", None, None, "planned"),
            (3, "company_admin", None, "Samsung India", "planned"),
            (4, "coordinator", "South Zone", "Samsung India", "planned"),
            (5, "coordinator", "East Zone", "Samsung India", "planned"),
            (6, "coordinator", "West Zone", "Samsung India", "planned"),
            (7, "coordinator", "North Zone", "Samsung India", "planned"),
        })

    def test_super_admin_is_held_until_confirmed(self):
        held = self.plan()
        self.assertEqual([g.status for g in held.grants if g.role == "super_admin"], ["held"])
        self.assertTrue(any("HELD" in t for t in self.levels(held, "WARN")))
        visibility = {v["id"]: v for v in held.visibility}
        self.assertEqual(visibility[1]["after"], "DENIED")           # deny-by-default while unconfirmed
        self.assertEqual(visibility[1]["verdict"], "LOSES ACCESS")   # it is unrestricted today

        confirmed = self.plan(confirmed=frozenset({1}))
        grant = next(g for g in confirmed.grants if g.role == "super_admin")
        self.assertEqual((grant.status, grant.tenant_uid), ("planned", None))  # global: no tenant
        v1 = {v["id"]: v for v in confirmed.visibility}[1]
        self.assertEqual((v1["before"], v1["after"], v1["verdict"]), (f"{self.total_conferences} of {self.total_conferences}",) * 2 + ("unchanged",))

    def test_super_admin_evidence_is_gathered_but_is_not_proof(self):
        evidence = self.plan().super_admin_evidence[1]
        self.assertEqual((evidence["account_role"], evidence["has_company"], evidence["recorded_logins"]), ("admin", False, 3))
        self.assertEqual(evidence["last_login"], "2026-09-20T09:00")

    def test_before_and_after_visibility(self):
        v = {row["id"]: row for row in self.plan(confirmed=frozenset({1})).visibility}
        for admin_id in (4, 5, 6, 7):                    # coordinators keep exactly today's zone limit
            self.assertEqual(v[admin_id]["verdict"], "unchanged", v[admin_id])
        self.assertEqual(v[4]["before"], "3 of 15")
        self.assertEqual(v[3]["before"], "3 of 15")      # zone-limited today ...
        self.assertEqual(v[3]["after"], "15 of 15")      # ... company-wide as Company Admin (blank-zone trainings included)
        self.assertEqual(v[3]["verdict"], "widens by 12")
        self.assertEqual(v[2]["verdict"], "unchanged")   # the trainer keeps their own trainings

    def test_a_coordinator_with_two_zones_gets_two_grants(self):
        self.tenant.add(DataScope(user_id=4, table_type="admin", scope_type="zone", scope_value="North Zone"))
        self.tenant.commit()
        self.assertEqual(sorted(g.zone for g in self.plan().grants if g.admin_id == 4), ["North Zone", "South Zone"])

    def test_the_company_admin_grant_carries_the_unique_key(self):
        grant = next(g for g in self.plan().grants if g.role == "company_admin")
        self.assertEqual(grant.key, company_admin_key(TENANT, "Samsung India"))
        self.assertIn(f"'{grant.key}'", grant.sql())

    def test_planned_rows_are_valid_for_the_real_table(self):
        """The SQL printed for review satisfies every constraint of admin_access."""
        scratch = mem()
        AccessBase.metadata.create_all(scratch)
        with scratch.begin() as conn:
            for g in self.plan(confirmed=frozenset({1})).grants:
                conn.execute(text(g.sql()))
        with scratch.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT COUNT(*) FROM admin_access")).scalar(), 7)


class ProblemDetectionTests(SeedingWorld):
    def test_things_that_would_lock_people_out_or_break_rules_are_blocked(self):
        cases = {
            "coordinator with no zone": ([Assignment(3, "coordinator")], lambda: self.tenant.query(DataScope).filter_by(user_id=3).delete()),
            "account that does not exist": ([Assignment(99, "company_admin", "Samsung India")], None),
            "unknown role": ([Assignment(3, "root")], None),
            "trainer role on an admin account": ([Assignment(3, "trainer")], None),
            "admin-panel role on a trainer account": ([Assignment(2, "company_admin", "Samsung India")], None),
            "two company admins for one company": ([Assignment(3, "company_admin", "Samsung India"), Assignment(4, "company_admin", " samsung india ")], None),
            "same assignment twice": ([Assignment(3, "company_admin", "Samsung India"), Assignment(3, "company_admin", "Samsung India")], None),
            "sub-coordinator without a region": ([Assignment(3, "sub_coordinator")], None),
            "company admin without a company": ([Assignment(1, "company_admin")], None),
        }
        for name, (assignments, prepare) in cases.items():
            with self.subTest(name):
                self.setUp()
                if prepare:
                    prepare()
                    self.tenant.commit()
                self.assertTrue(self.plan(assignments).blockers, name)

    def test_an_existing_company_admin_blocks_a_second_one(self):
        AccessBase.metadata.create_all(self.common_engine)
        self.common.add(AdminAccess(admin_id=4, role="company_admin", tenant_uid=TENANT, company="Samsung India",
                                    company_admin_key=company_admin_key(TENANT, "Samsung India")))
        self.common.commit()
        self.assertTrue(any("already exists" in f.text for f in self.plan().blockers))

    def test_an_account_left_out_of_the_plan_is_reported_as_denied(self):
        plan = self.plan([a for a in USER_PLAN if a.admin_id != 7])
        self.assertTrue(any("account 7" in t and "DENIED" in t for t in self.levels(plan, "WARN")))
        self.assertEqual({v["id"]: v for v in plan.visibility}[7]["verdict"], "LOSES ACCESS")

    def test_data_quality_warnings(self):
        text_ = " ".join(self.levels(self.plan(), "WARN"))
        self.assertIn("3 training(s) have no zone", text_)
        self.tenant.query(DataScope).filter_by(user_id=6).update({"scope_value": "Mars Zone"})
        self.tenant.commit()
        self.assertTrue(any("Mars Zone" in t for t in self.levels(self.plan(), "WARN")))


class ReadOnlyTests(SeedingWorld):
    def make_engines(self):
        """Real SQLite files: disposing an engine must not erase the data (an in-memory database would)."""
        import shutil
        import tempfile

        folder = tempfile.mkdtemp()
        engines = tuple(create_engine(f"sqlite:///{folder}/{name}.db") for name in ("common", "tenant"))
        self.addCleanup(lambda: (*[e.dispose() for e in engines], shutil.rmtree(folder, ignore_errors=True)))
        return engines

    def test_planning_works_through_read_only_connections_and_writes_nothing(self):
        def snapshot():
            with self.common_engine.connect() as c, self.tenant_engine.connect() as t:
                return ({tbl: c.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() for tbl in ("admin", "tenants")},
                        {tbl: t.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar() for tbl in ("conference", "data_scopes", "logsmaster")})

        before = snapshot()
        make_read_only(self.common_engine)
        make_read_only(self.tenant_engine)
        self.common_engine.dispose()  # new connections pick up the read-only setting
        self.tenant_engine.dispose()
        common = sessionmaker(bind=self.common_engine)()
        tenant = sessionmaker(bind=self.tenant_engine)()
        plan = build_plan(common, tenant, TENANT, USER_PLAN)
        self.assertEqual(plan.blockers, [])
        self.assertEqual(snapshot(), before)

    def test_the_read_only_connections_refuse_writes(self):
        make_read_only(self.common_engine)
        self.common_engine.dispose()
        session = sessionmaker(bind=self.common_engine)()
        session.add(Admin(adminUid="x", username="x", password="x", role="admin"))
        with self.assertRaises(Exception) as caught:
            session.commit()
        self.assertIn("non-read statement", str(caught.exception))
        session.rollback()
        with self.common_engine.connect() as conn:
            with self.assertRaises(Exception):
                conn.execute(text("UPDATE admin SET company = 'x'"))
            with self.assertRaises(Exception):
                conn.execute(text("DELETE FROM admin"))


class ReadOnlyGuardTests(unittest.TestCase):
    def test_only_reads_and_the_switch_that_enables_read_only_mode_are_allowed(self):
        for ok in ("SELECT 1", "  select * from admin", "SHOW TABLES", "EXPLAIN SELECT 1", "DESCRIBE admin_access",
                   "SET SESSION TRANSACTION READ ONLY", "PRAGMA query_only = ON", 'PRAGMA main.table_info("admin_access")', "SELECT 1;"):
            self.assertTrue(is_read_statement(ok), ok)
        for refused in ("INSERT INTO admin_access VALUES (1)", "UPDATE admin SET company='x'", "DELETE FROM admin", "DROP TABLE admin",
                        "ALTER TABLE admin ADD x INT", "CREATE TABLE t (a INT)", "TRUNCATE admin", "REPLACE INTO admin VALUES (1)",
                        "SET SESSION TRANSACTION READ WRITE", "PRAGMA query_only = OFF", "PRAGMA writable_schema = ON", "CALL cleanup()",
                        "WITH x AS (SELECT 1) DELETE FROM admin", "SELECT 1; DROP TABLE admin", "SELECT 1 INTO OUTFILE '/tmp/x'", "GRANT ALL ON *.* TO x"):
            self.assertFalse(is_read_statement(refused), refused)


class ReportTests(SeedingWorld):
    def test_the_report_says_it_is_a_dry_run_and_masks_usernames(self):
        report = render_report(self.plan())
        self.assertIn("DRY RUN", report)
        self.assertIn("NOTHING is written", report)
        self.assertIn("INSERT INTO admin_access", report)   # shown for review
        self.assertIn("HELD", report)
        for admin_id in range(1, 8):
            self.assertNotIn(f"account{admin_id}", report)  # full usernames never appear
        self.assertIn("ac*", report)


if __name__ == "__main__":
    unittest.main()
