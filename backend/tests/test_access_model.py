"""Phase C step 1: the access model (AdminAccess + resolve_scope). Synthetic, in-memory only.

Covers deny-by-default, explicit Super Admin grants, tenant membership, the company / zone /
region rules and the safety properties (the table can't be created by app startup; the SQL file
for review matches the model; the running app doesn't use any of this yet)."""

import os
import subprocess
import sys
import unittest

from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database.connection import CommonBase, TenantBase
from app.models.admin import Admin
from app.models.admin_access import AccessBase, AdminAccess
from app.services.access_service import AccessRole, AccessScope, ScopeRule, company_admin_key, resolve_scope
from tests.tenant_fixtures import ALPHA, BETA, CONFERENCES, TenantWorld, uid

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ResolveScopeTests(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()

    def tearDown(self):
        self.w.close()

    def scope(self, who, tenant=ALPHA):
        return resolve_scope(self.w.common, self.w.principal(who), tenant)

    def visible(self, scope):
        """Fixture conference keys inside the scope."""
        return {key for key, _t, company, zone, region, _tr in CONFERENCES if _t == ALPHA and scope.allows_row(company, zone, region)}

    # ---- deny by default ------------------------------------------------------------
    def test_an_admin_with_no_grant_is_denied_everywhere(self):
        for tenant in (ALPHA, BETA):
            scope = self.scope("ungranted", tenant)
            self.assertFalse(scope.allowed)
            self.assertFalse(scope.is_super)
            self.assertFalse(scope.allows_row("Samsung India", "North Zone", "North 1"))

    def test_no_company_no_longer_means_unrestricted(self):
        # an admin with no company and no grant - today's "unrestricted" account shape
        self.w.admins["ungranted"].company = None
        self.w.common.commit()
        self.assertFalse(self.scope("ungranted").allowed)

    def test_missing_tenant_or_unknown_principal_is_denied(self):
        self.assertFalse(resolve_scope(self.w.common, self.w.admins["coadmin"], "").allowed)
        self.assertFalse(resolve_scope(self.w.common, self.w.admins["coadmin"], None).allowed)
        self.assertFalse(resolve_scope(self.w.common, object(), ALPHA).allowed)

    # ---- super admin ---------------------------------------------------------------------
    def test_super_admin_only_through_an_explicit_grant_and_is_global(self):
        for tenant in (ALPHA, BETA):
            scope = self.scope("super", tenant)
            self.assertTrue(scope.allowed and scope.is_super)
            self.assertEqual(scope.role, AccessRole.SUPER_ADMIN)
            self.assertTrue(scope.allows_row("Any Company", "Any Zone", "Any Region"))
        self.assertEqual(self.visible(self.scope("super")), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V", "O_N1"})

    def test_a_super_grant_on_a_non_admin_account_is_ignored(self):
        self.w.grant(self.w.admins["adm_trainer"], "super_admin")  # account role is "trainer"
        self.w.common.commit()
        scope = self.scope("adm_trainer")
        self.assertFalse(scope.is_super)
        self.assertEqual(scope.role, AccessRole.TRAINER)

    # ---- company admin -------------------------------------------------------------------
    def test_company_admin_sees_every_zone_and_region_of_their_company_only(self):
        scope = self.scope("coadmin")
        self.assertEqual(scope.role, AccessRole.COMPANY_ADMIN)
        # includes the blank-zone training and the spelling variant; excludes the other company
        self.assertEqual(self.visible(scope), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V"})

    def test_membership_is_per_tenant(self):
        self.assertFalse(self.scope("coadmin", BETA).allowed)  # a member of ALPHA is not a member of BETA
        self.assertFalse(self.scope("betaonly", ALPHA).allowed)
        beta = self.scope("betaonly", BETA)
        self.assertTrue(beta.allowed)
        self.assertTrue(beta.allows_row("Samsung India", "North Zone", "North 1"))  # same company text, its own tenant

    # ---- coordinator / sub-coordinator -----------------------------------------------------
    def test_coordinator_sees_only_their_zone_and_never_blank_zone_rows(self):
        scope = self.scope("coord")
        self.assertEqual(scope.role, AccessRole.COORDINATOR)
        self.assertEqual(self.visible(scope), {"S_N1", "S_DEL", "S_N1V"})
        self.assertFalse(scope.allows_row("Samsung India", None, None))
        self.assertFalse(scope.allows_row("Samsung India", "", "North 1"))
        self.assertFalse(scope.allows_row("Other Co", "North Zone", "North 1"))  # zone names repeat across companies

    def test_sub_coordinator_sees_only_their_region(self):
        scope = self.scope("subcoord")
        self.assertEqual(scope.role, AccessRole.SUB_COORDINATOR)
        self.assertEqual(self.visible(scope), {"S_DEL"})
        self.assertFalse(scope.allows_row("Samsung India", "North Zone", None))

    def test_spelling_and_spacing_do_not_change_the_answer(self):
        scope = self.scope("coord")
        self.assertTrue(scope.allows_row("  SAMSUNG india", " NORTH zone ", None))

    # ---- several grants ----------------------------------------------------------------------
    def test_grants_are_a_union_and_the_highest_role_wins(self):
        coord = self.w.admins["coord"]
        self.w.grant(coord, "coordinator", ALPHA, "Samsung India", zone="South Zone")
        self.w.common.commit()
        scope = self.scope("coord")
        self.assertEqual(scope.role, AccessRole.COORDINATOR)
        self.assertEqual(len(scope.rules), 2)
        self.assertEqual(self.visible(scope), {"S_N1", "S_DEL", "S_N1V", "S_S1"})
        self.w.grant(coord, "company_admin", ALPHA, "Other Co")  # (Samsung India already has its one Company Admin)
        self.w.common.commit()
        promoted = self.scope("coord")
        self.assertEqual(promoted.role, AccessRole.COMPANY_ADMIN)
        self.assertTrue(promoted.allows_row("Other Co", "South Zone", "South 1"))    # whole Other Co ...
        self.assertFalse(promoted.allows_row("Samsung India", "East Zone", "East 1"))  # ... and for Samsung still only the North and South zones

    def test_duplicate_grants_do_not_duplicate_rules(self):
        self.w.grant(self.w.admins["coord"], "coordinator", ALPHA, " samsung india ", zone="north zone")  # same slice, other spelling
        self.w.common.commit()
        self.assertEqual(len(self.scope("coord").rules), 1)

    def test_inactive_grants_are_ignored(self):
        # deactivating a company admin grant also releases its unique key (the table refuses one without the other)
        self.w.common.query(AdminAccess).filter_by(admin_id=self.w.admins["coadmin"].id).update({"active": 0, "company_admin_key": None})
        self.w.common.commit()
        self.assertFalse(self.scope("coadmin").allowed)

    def test_a_grant_whose_role_does_not_fit_the_account_is_ignored(self):
        self.w.grant(self.w.admins["adm_trainer"], "company_admin", ALPHA, "Third Co")  # trainer account, admin-panel grant
        self.w.grant(self.w.admins["ungranted"], "trainer", ALPHA)  # admin account, trainer grant
        self.w.common.commit()
        self.assertEqual(self.scope("adm_trainer").role, AccessRole.TRAINER)
        self.assertFalse(self.scope("adm_trainer").allows_row("Third Co", "North Zone", "North 1"))
        self.assertFalse(self.scope("ungranted").allowed)

    def test_a_corrupted_grant_row_is_still_refused_by_the_resolver(self):
        """The table's CHECK constraints stop bad rows being written. If one ever got in anyway (a
        manual edit, an old database without the constraints), the resolver must still refuse it."""
        from sqlalchemy import text

        self.w.common.execute(AdminAccess.__table__.delete())
        self.w.common.execute(text("PRAGMA ignore_check_constraints = ON"))
        admin_id = self.w.admins["coord"].id
        for row in (
            dict(role="coordinator", tenant_uid=ALPHA, company="Samsung India", zone=None),                        # no zone
            dict(role="company_admin", tenant_uid=ALPHA, company=None),                                             # no company
            dict(role="super_admin", tenant_uid=ALPHA, company=None),                                               # super admin tagged with a tenant
            dict(role="coordinator", tenant_uid=None, company="Samsung India", zone="North Zone"),                  # tenant-less non-super
            dict(role="made_up", tenant_uid=ALPHA, company="Samsung India"),                                        # unknown role
        ):
            self.w.common.execute(AdminAccess.__table__.insert().values(admin_id=admin_id, **row))
        self.w.common.execute(text("PRAGMA ignore_check_constraints = OFF"))
        self.w.common.commit()
        scope = self.scope("coord")
        self.assertFalse(scope.allowed, scope)
        self.assertFalse(scope.is_super)

    # ---- trainers ----------------------------------------------------------------------------
    def test_agency_trainer_is_an_implicit_member_of_their_own_tenant(self):
        scope = self.scope("trainer1")
        self.assertTrue(scope.allowed)
        self.assertEqual(scope.role, AccessRole.TRAINER)
        self.assertEqual(scope.trainer_username, "trainer1")
        self.assertFalse(scope.is_admin_panel)
        self.assertFalse(scope.allows_row("Samsung India", "North Zone", "North 1"))  # trainers are not company-scoped

    def test_admin_table_trainer_needs_a_trainer_grant_for_the_tenant(self):
        scope = self.scope("adm_trainer")
        self.assertEqual(scope.role, AccessRole.TRAINER)
        self.assertEqual(scope.trainer_username, "adm_trainer")
        self.assertFalse(self.scope("adm_trainer", BETA).allowed)

    def test_an_agency_account_that_is_not_a_trainer_is_denied(self):
        self.w.agency["trainer1"].role = "agency_manager"
        self.assertFalse(self.scope("trainer1").allowed)

    def test_admin_panel_flag(self):
        self.assertTrue(self.scope("subcoord").is_admin_panel)
        self.assertFalse(self.scope("adm_trainer").is_admin_panel)
        self.assertFalse(AccessScope.denied(ALPHA, "x").is_admin_panel)


class GrantTableConstraintTests(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()

    def tearDown(self):
        self.w.close()

    def row(self, **fields):
        """A valid active company_admin row for "Fresh Co" in ALPHA, with fields overridden."""
        base = {"admin_id": 999, "role": "company_admin", "tenant_uid": ALPHA, "company": "Fresh Co", "company_admin_key": company_admin_key(ALPHA, "Fresh Co")}
        base.update(fields)
        return AdminAccess(**base)

    def assert_rejected(self, **fields):
        self.w.common.add(self.row(**fields))
        with self.assertRaises(IntegrityError):
            self.w.common.commit()
        self.w.common.rollback()

    def test_rows_that_break_the_rules_cannot_be_stored(self):
        self.assert_rejected(role="root", company_admin_key=None)                          # unknown role
        self.assert_rejected(role="super_admin", company_admin_key=None, company=None)     # a super admin is tenant-less
        self.assert_rejected(tenant_uid=None)                                              # everyone else belongs to a tenant
        self.assert_rejected(company=None)                                                 # company admin needs a company
        self.assert_rejected(role="coordinator", zone=None, company_admin_key=None)        # coordinator needs a zone
        self.assert_rejected(role="sub_coordinator", region=None, company_admin_key=None)  # sub-coordinator needs a region

    def test_valid_rows_are_accepted(self):
        rows = [
            self.row(),
            AdminAccess(admin_id=999, role="super_admin"),
            AdminAccess(admin_id=999, role="coordinator", tenant_uid=ALPHA, company="Fresh Co", zone="North Zone"),
            AdminAccess(admin_id=999, role="sub_coordinator", tenant_uid=ALPHA, company="Fresh Co", region="North 1"),
            AdminAccess(admin_id=999, role="trainer", tenant_uid=ALPHA),
        ]
        self.w.common.add_all(rows)
        self.w.common.commit()

    # ---- one Company Admin per company (enforced by the database) ------------------------------
    def test_the_company_admin_key_ignores_spelling(self):
        self.assertEqual(company_admin_key("ALPHA", "Samsung India"), company_admin_key(" ALPHA", "  samsung INDIA "))
        self.assertNotEqual(company_admin_key("ALPHA", "Samsung India"), company_admin_key("BETA", "Samsung India"))

    def test_a_company_can_have_only_one_company_admin_per_tenant(self):
        self.w.common.add(self.row())
        self.w.common.commit()
        # a second admin account, the same company written differently: refused
        self.assert_rejected(admin_id=1000, company=" fresh co ", company_admin_key=company_admin_key(ALPHA, " FRESH CO "))
        # the existing seeded Company Admin of Samsung India cannot be doubled up either
        self.assert_rejected(admin_id=1001, company="Samsung India", company_admin_key=company_admin_key(ALPHA, "Samsung India"))

    def test_other_companies_and_other_tenants_are_unaffected(self):
        self.w.common.add(self.row())
        self.w.common.add(self.row(admin_id=1000, company="Second Co", company_admin_key=company_admin_key(ALPHA, "Second Co")))   # another company
        self.w.common.add(self.row(admin_id=1001, tenant_uid=BETA, company_admin_key=company_admin_key(BETA, "Fresh Co")))         # same company, another tenant
        self.w.common.commit()

    def test_a_replacement_company_admin_needs_the_old_grant_deactivated_first(self):
        first = self.row()
        self.w.common.add(first)
        self.w.common.commit()
        first.active, first.company_admin_key = 0, None  # deactivate: the key is released
        self.w.common.commit()
        self.w.common.add(self.row(admin_id=1000))
        self.w.common.commit()

    def test_the_key_must_match_the_grant(self):
        self.assert_rejected(company_admin_key=None)                                       # an active company admin must carry its key
        self.assert_rejected(active=0)                                                      # a deactivated one must not
        self.assert_rejected(role="coordinator", zone="North Zone")                         # other roles never carry it

    def test_other_roles_may_be_many_per_company(self):
        for n in range(3):
            self.w.common.add(AdminAccess(admin_id=2000 + n, role="coordinator", tenant_uid=ALPHA, company="Samsung India", zone=f"Zone {n}"))
            self.w.common.add(AdminAccess(admin_id=3000 + n, role="sub_coordinator", tenant_uid=ALPHA, company="Samsung India", region=f"Region {n}"))
        self.w.common.commit()


class SafetyTests(unittest.TestCase):
    def test_app_startup_cannot_create_the_table(self):
        """app.main runs CommonBase.metadata.create_all against the live shared database. The grants
        table must not be on that metadata (nor the tenant one), so a restart can never create it."""
        self.assertNotIn("admin_access", CommonBase.metadata.tables)
        self.assertNotIn("admin_access", TenantBase.metadata.tables)
        self.assertIn("admin_access", AccessBase.metadata.tables)

    def test_the_sql_file_for_review_matches_the_model(self):
        table = AdminAccess.__table__
        ddl = str(CreateTable(table).compile(dialect=mysql.dialect())).strip() + ";"
        ddl += "".join("\n\n" + str(CreateIndex(ix).compile(dialect=mysql.dialect())).strip() + ";" for ix in sorted(table.indexes, key=lambda i: i.name))
        with open(os.path.join(BACKEND_DIR, "..", "docs", "admin_access_table.sql"), encoding="utf-8") as fh:
            self.assertIn(ddl, fh.read())

    def test_the_running_app_only_uses_the_access_model_for_the_one_approved_check(self):
        """Phase C started as "designed but not wired in": nothing imported access_service or
        admin_access. That changed with one specific, approved wiring - training_service now
        calls resolve_scope so an admin-table account (Super Admin / Company Admin /
        Coordinator / Sub-coordinator) can start and operate a conference inside their granted
        scope, the same way the assigned trainer does (see training_service._get_owned_conference
        and live_quiz_service._owned_live_conference). So the module IS now imported - this test
        pins that fact rather than its absence. What still must hold, and is pinned by
        test_app_startup_cannot_create_the_table, is that importing the app can never CREATE the
        table; this test only pins which tables are on which metadata, not import timing."""
        code = "import sys, app.main; print(any(m in sys.modules for m in ('app.services.access_service', 'app.models.admin_access')))"
        result = subprocess.run([sys.executable, "-c", code], cwd=BACKEND_DIR, env=dict(os.environ), capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr[-600:])
        self.assertEqual(result.stdout.strip().splitlines()[-1], "True")

    def test_scope_rule_matching_is_company_bound(self):
        rule = ScopeRule("samsung india", zone="north zone")
        self.assertTrue(rule.matches("Samsung India", "North Zone", "any"))
        self.assertFalse(rule.matches("Other Co", "North Zone", "any"))
        self.assertFalse(rule.matches("Samsung India", None, "any"))


if __name__ == "__main__":
    unittest.main()
