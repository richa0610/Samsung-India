"""Phase C: tenant isolation and role scopes, through the real API, on the synthetic world in
tests/tenant_fixtures.py (two tenants, two companies, zones / regions, one account per role).

Two kinds of test live here:

  * Regression tests - behaviour that already holds and must keep holding while the later steps
    change authentication and scoping (valid-token rules, login contract, company scope on the
    paged attendance list, ...). They run normally.

  * `@pending_phase_c(step)` tests - the approved end state that a LATER step introduces. Each one
    was checked to fail today for the intended reason (see tests/_pending.py; run them for real
    with PHASE_C_ENFORCE=1). Until the step lands they are expectedFailure, so the suite is green;
    when it lands they flip to "unexpected success" and the decorator is removed.

Conventions the end state uses: an out-of-scope object (another company, zone, region or tenant's
id) looks like it does not exist (404); an account with no access to the tenant at all is 403.
"""

import asyncio
import base64
import json
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import httpx
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core import rate_limit
from app.core.config import settings
from app.core.security import create_access_token
from app.database.tenant import tenant_manager
from app.models.admin_access import AdminAccess
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.routers import admin as admin_router
from app.schemas.admin import AdminAuthSession
from tests._pending import pending_phase_c
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD, TenantWorld, uid

TRAININGS = "/admin/trainings/page?approval=pending&limit=200"
ATTENDANCE = "/admin/attendance/page?mode=all&limit=200"


class WorldTestCase(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        rate_limit.reset()
        admin_router._stats_cache.clear()

    def tearDown(self):
        self.w.close()

    def get(self, who, path, tenant=ALPHA, extra=None):
        headers = self.w.headers(who, tenant)
        headers.update(extra or {})
        return self.w.client.get(path, headers=headers)

    def keys(self, who, path, tenant=ALPHA):
        response = self.get(who, path, tenant)
        self.assertEqual(response.status_code, 200, f"{who} {path} -> {response.status_code} {response.text[:120]}")
        return self.w.conference_keys(response.json()["items"])

    def attendance_rows(self, keys):
        from app.models.attendance import Attendance

        wanted = {uid(k) for k in keys}
        return sum(1 for a in self.w.tenant_db[ALPHA].query(Attendance) if a.conferenceUid in wanted)


# ======================================================================= regression: must keep holding
class ExistingControlsStillHold(WorldTestCase):
    def test_a_valid_token_decides_the_tenant_not_the_header(self):
        response = self.get("super", "/admin/trainees", ALPHA, extra={"X-Tenant-ID": BETA})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(t["traineeUid"].startswith("TR-") and "B_N1" not in t["traineeUid"] for t in response.json()))

    def test_bad_credentials_are_rejected(self):
        def forged():
            b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
            exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
            return f"{b({'alg': 'none', 'typ': 'JWT'})}.{b({'sub': 'admin:super', 'tenant_id': ALPHA, 'exp': exp})}."

        expired = jwt.encode({"sub": "admin:super", "tenant_id": ALPHA, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        wrong_key = jwt.encode({"sub": "admin:super", "tenant_id": ALPHA, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "another-secret", algorithm=settings.ALGORITHM)
        cases = {"no header": {}, "malformed": {"Authorization": "Bearer abc.def"}, "expired": {"Authorization": f"Bearer {expired}"},
                 "wrong key": {"Authorization": f"Bearer {wrong_key}"}, "alg none": {"Authorization": f"Bearer {forged()}"},
                 "trainee token": {"Authorization": f"Bearer {create_access_token('9000000001', ALPHA, 'trainee')}"}}
        for name, headers in cases.items():
            with self.subTest(name):
                self.assertIn(self.w.client.get("/admin/trainees", headers=headers).status_code, (401, 403))

    def test_an_admin_token_is_rejected_on_trainee_endpoints(self):
        self.assertEqual(self.get("super", "/sessions/current").status_code, 401)

    def test_trainers_are_blocked_from_admin_only_endpoints(self):
        # Trainer Flow Phase 2: the paged attendance list serves trainers too, but only the
        # attendance on their own trainings - never a company-wide view.
        self.assertEqual(self.keys("trainer1", ATTENDANCE), {"S_N1", "S_DEL", "S_N1V"})
        self.assertEqual(self.w.client.post(f"/admin/trainings/{uid('S_N1')}/reject", json={"message": "x"}, headers=self.w.headers("trainer1")).status_code, 403)

    def test_a_trainer_cannot_open_another_trainers_training(self):
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('S_S1')}").status_code, 404)
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{uid('S_N1')}").status_code, 200)  # their own still works

    def test_unknown_tenant_is_not_found(self):
        response = self.w.client.post("/admin/login", json={"username": "super", "password": PASSWORD}, headers={"X-Tenant-ID": "NOPE"})
        self.assertEqual(response.status_code, 404)

    def test_login_response_contract_is_unchanged(self):
        response = self.w.client.post("/admin/login", json={"username": "coadmin", "password": PASSWORD}, headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(set(body), set(AdminAuthSession.model_fields))
        self.assertIn(body["admin"]["role"], ("admin", "trainer"))  # the mobile app routes on exactly these two values
        self.assertEqual(body["admin"]["tenant_id"], ALPHA)
        claims = jwt.decode(body["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # The token contract; `ver` (Phase 2.2, approved) lets an account's tokens be revoked.
        self.assertEqual(sorted(claims), ["exp", "role", "sub", "tenant_id", "ver"])
        self.assertEqual(claims["tenant_id"], ALPHA)

    def test_public_endpoints_still_resolve_the_tenant_from_the_header(self):
        response = self.w.client.get(f"/sessions/join/{uid('B_N1')}", headers={"X-Tenant-ID": BETA})
        self.assertNotIn("isn't valid", response.text)  # found in BETA (it is simply not open to join yet)

    def test_company_admin_sees_the_whole_company_and_nothing_else(self):
        expected = {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V"}
        self.assertEqual(self.keys("coadmin", TRAININGS), expected)
        self.assertEqual(self.keys("coadmin", ATTENDANCE), expected)
        stats = self.get("coadmin", "/admin/dashboard/stats?fresh=true").json()
        self.assertEqual(stats["audience"]["present"], 5)  # one Present attendee per Samsung training

    def test_super_admin_sees_every_company_together(self):
        self.assertEqual(self.keys("super", TRAININGS), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V", "O_N1"})
        self.assertEqual(self.get("super", "/admin/dashboard/stats?fresh=true").json()["audience"]["present"], 6)

    def test_a_forged_cursor_cannot_widen_the_company_scope(self):
        cursor = base64.urlsafe_b64encode(json.dumps({"s": "markedAt", "v": "2099-01-01T00:00:00", "id": 10**9}).encode()).decode()
        response = self.get("coadmin", f"/admin/attendance/page?mode=all&cursor={cursor}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.w.conference_keys(response.json()["items"]) - {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V"}, set())
        self.assertIsNone(response.json()["total"])


    def test_a_trainer_keeps_their_own_operations_and_cannot_touch_others(self):
        own, other = uid("S_N1"), uid("S_S1")
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{own}").status_code, 200)   # own training: unchanged
        self.assertEqual(self.get("trainer1", "/admin/profile").status_code, 200)             # own profile: unchanged
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{other}").status_code, 404)
        self.assertEqual(self.w.client.post(f"/admin/trainings/{other}/reject", json={"message": "x"}, headers=self.w.headers("trainer1")).status_code, 403)
        self.assertEqual(self.keys("trainer1", ATTENDANCE), {"S_N1", "S_DEL", "S_N1V"})       # own trainings only, no company-wide view
        self.assertEqual(self.get("trainer1", "/admin/attendance?org=true").status_code, 403)

    def test_an_admin_can_operate_a_training_within_their_granted_scope(self):
        """"Admin also can start training like trainers": an admin-table account can now run
        start/end/modules/attendance/live-quiz on a conference the same way its assigned trainer
        does, as long as their admin_access grant covers that conference's company/zone/region.
        /schedule-check is a read-only GET through the exact same gate (_get_owned_conference /
        _owned_live_conference) with none of start/end's side effects (photo, geofence, approval,
        date), so it isolates the scope check itself."""
        check = lambda who, key: self.get(who, f"/admin/trainings/{uid(key)}/schedule-check")

        # Company Admin: the whole company, including a training that isn't their own and isn't
        # any particular admin's - the point of the feature - but not another company.
        self.assertEqual(check("coadmin", "S_S1").status_code, 200)   # South Zone, trainer2's - in company
        self.assertEqual(check("coadmin", "O_N1").status_code, 404)   # Other Co - out of scope, looks absent

        # Coordinator: their zone only, inside their company.
        self.assertEqual(check("coord", "S_N1").status_code, 200)     # North Zone - granted
        self.assertEqual(check("coord", "S_S1").status_code, 404)     # South Zone - out of scope

        # Sub-coordinator: their region only.
        self.assertEqual(check("subcoord", "S_DEL").status_code, 200)  # Delhi NCR - granted
        self.assertEqual(check("subcoord", "S_N1").status_code, 404)   # North 1 - out of scope

        # Super Admin: any company, any tenant-registered conference.
        self.assertEqual(check("super", "O_N1").status_code, 200)

        # An admin-table account with no grant at all: denied - now at get_current_admin itself
        # (Phase B), before this per-training check even runs, so 403 rather than 404.
        self.assertEqual(check("ungranted", "S_N1").status_code, 403)

        # The assigned trainer's own path is untouched by any of this.
        self.assertEqual(check("trainer1", "S_N1").status_code, 200)
        self.assertEqual(check("trainer1", "S_S1").status_code, 404)


# ======================================================================= landed: Training List access control
class TrainingListAccessControl(WorldTestCase):
    """Phase 1 of the Training List RBAC task: /admin/trainings/page (TRAININGS) is now scoped
    at the SQL level by the caller's own admin_access grant (dashboard_repository.
    access_scope_conditions), not by anything the request sends. This only covers that one
    endpoint - detail/edit/report/session-dashboard object-level checks are Phase 2, still
    covered by the `RoleScopes` pending tests below until that phase lands."""

    def test_super_admin_sees_every_company(self):
        self.assertEqual(self.keys("super", TRAININGS), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V", "O_N1"})

    def test_company_admin_sees_their_company_only(self):
        self.assertEqual(self.keys("coadmin", TRAININGS), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V"})

    def test_coordinator_sees_their_zone_only(self):
        self.assertEqual(self.keys("coord", TRAININGS), {"S_N1", "S_DEL", "S_N1V"})

    def test_sub_coordinator_sees_their_region_only(self):
        self.assertEqual(self.keys("subcoord", TRAININGS), {"S_DEL"})

    def test_no_grant_returns_nothing(self):
        """The fail-open bug this replaces: an admin-table account with no admin_access grant at
        all used to fall through to "unrestricted" because nothing but the legacy company/zone
        columns gated it. get_current_admin (Phase B) now denies it at the gate, before the
        request even reaches this list - the query-level check (access_scope_conditions) is
        still what protects a request that DOES get through with a same-tenant-but-empty scope
        (see test_a_grant_in_another_tenant_does_not_leak_into_this_one)."""
        response = self.get("ungranted", TRAININGS)
        self.assertEqual(response.status_code, 403)

    def test_a_grant_in_another_tenant_does_not_leak_into_this_one(self):
        # "betaonly" is a real, active Company Admin - just not for ALPHA, so get_current_admin
        # denies them for this tenant before the list query ever runs.
        response = self.get("betaonly", TRAININGS)
        self.assertEqual(response.status_code, 403)

    def test_query_params_cannot_widen_a_coordinators_zone(self):
        """Frontend filters narrow inside the authorized scope; they can never widen past it -
        the same property already proven for the Attendance list's cursor
        (test_a_forged_cursor_cannot_widen_the_company_scope), now for the Training List's own
        zone/region query params."""
        widened = self.get("coord", TRAININGS + "&zones=South%20Zone")
        self.assertEqual(widened.json()["items"], [])  # South Zone isn't theirs - asking for it gets nothing, not South Zone's data

        widened_region = self.get("subcoord", TRAININGS + "&regions=North%201")
        self.assertEqual(widened_region.json()["items"], [])  # not their region either

        # Still allowed to narrow *inside* their own scope.
        narrowed = self.get("coord", TRAININGS + "&zones=North%20Zone")
        self.assertEqual(self.w.conference_keys(narrowed.json()["items"]), {"S_N1", "S_DEL", "S_N1V"})

    def test_total_count_reflects_only_authorized_rows(self):
        self.assertEqual(self.get("coord", TRAININGS).json()["total"], 3)
        self.assertEqual(self.get("subcoord", TRAININGS).json()["total"], 1)

    def test_sorting_stays_within_the_authorized_scope(self):
        response = self.get("coord", "/admin/trainings/page?approval=pending&limit=200&sort=zone&dir=asc")
        self.assertEqual(self.w.conference_keys(response.json()["items"]), {"S_N1", "S_DEL", "S_N1V"})

    def test_a_forged_cursor_cannot_widen_the_training_list_scope(self):
        """Same property test_a_forged_cursor_cannot_widen_the_company_scope already proves for
        Attendance, here for the Training List's own cursor (what "Export All" walks): a
        hand-built cursor claiming to be far past every real row can reach at most everything
        the scope query itself allows - never another company's or zone's rows."""
        cursor = base64.urlsafe_b64encode(json.dumps({"v": "2099-01-01T00:00:00", "id": 10**9}).encode()).decode()
        response = self.get("coord", f"/admin/trainings/page?approval=pending&limit=200&cursor={cursor}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.w.conference_keys(response.json()["items"]), {"S_N1", "S_DEL", "S_N1V"})


# ======================================================================= landed: related endpoints (Phase 2)
class RelatedEndpointAccessControl(WorldTestCase):
    """Phase 2: the same admin_access scope now gates the endpoints around the Training List that
    share its conferenceUid - detail, edit, report, session-dashboard, performers - not just the
    list query itself. All read through the same _get_owned_conference the write-path (start/end/
    modules) already used, so there is one authorization rule per training, not a different one
    per endpoint."""

    EDIT_PAYLOAD = {"conferenceDate": "2026-09-20", "conferenceTime": "10:00 AM"}

    def test_out_of_scope_training_is_404_on_every_related_endpoint(self):
        # A company, a zone and a region each account is NOT granted.
        cases = {"coord": "S_S1", "subcoord": "S_N1", "coadmin": "O_N1"}
        for who, key in cases.items():
            base = f"/admin/trainings/{uid(key)}"
            with self.subTest(who=who, key=key, endpoint="performers"):
                self.assertEqual(self.get(who, base + "/performers").status_code, 404)
            with self.subTest(who=who, key=key, endpoint="edit"):
                response = self.w.client.patch(base, json=self.EDIT_PAYLOAD, headers=self.w.headers(who))
                self.assertEqual(response.status_code, 404)

    def test_edit_never_touches_an_out_of_scope_row(self):
        """The 404 above must be a real refusal, not just a response code - confirm the row
        itself was never written to."""
        before = self.w.tenant_db[ALPHA].query(Conference).filter_by(conferenceUid=uid("S_S1")).one().conferenceDate
        self.w.client.patch(f"/admin/trainings/{uid('S_S1')}", json={"conferenceDate": "2099-01-01", "conferenceTime": "1:00 AM"},
                             headers=self.w.headers("coord"))
        self.w.tenant_db[ALPHA].expire_all()
        after = self.w.tenant_db[ALPHA].query(Conference).filter_by(conferenceUid=uid("S_S1")).one().conferenceDate
        self.assertEqual(before, after)

    def test_super_admin_reaches_every_related_endpoint(self):
        base = f"/admin/trainings/{uid('O_N1')}"  # Other Co - outside every other seeded account's scope
        self.assertEqual(self.get("super", base).status_code, 200)
        self.assertEqual(self.get("super", base + "/detail").status_code, 200)
        self.assertEqual(self.get("super", base + "/performers").status_code, 200)
        response = self.w.client.patch(base, json=self.EDIT_PAYLOAD, headers=self.w.headers("super"))
        self.assertEqual(response.status_code, 200)

    def test_an_ungranted_admin_reaches_none_of_them(self):
        # get_current_admin (Phase B) denies an account with no grant at all before any of these
        # requests reach _get_owned_conference's per-training 404 - see
        # TrainingListAccessControl.test_no_grant_returns_nothing.
        base = f"/admin/trainings/{uid('S_N1')}"
        for suffix in ("", "/detail", "/performers"):
            with self.subTest(endpoint=suffix or "dashboard"):
                self.assertEqual(self.get("ungranted", base + suffix).status_code, 403)
        response = self.w.client.patch(base, json=self.EDIT_PAYLOAD, headers=self.w.headers("ungranted"))
        self.assertEqual(response.status_code, 403)

    def test_a_company_admin_can_still_edit_a_training_that_is_not_their_own(self):
        """The point of the feature this scope is built on: a Company Admin manages the whole
        company, including a training assigned to a trainer they've never touched before. Sent the
        way the edit form sends it: the whole form, including the training's own place and trainer."""
        full_form = {**self.EDIT_PAYLOAD, "company": "Samsung India", "zone": "South Zone", "region": "South 1",
                     "trainerEmployeeId": "trainer2", "trainerName": "Trainer2"}
        response = self.w.client.patch(f"/admin/trainings/{uid('S_S1')}", json=full_form, headers=self.w.headers("coadmin"))
        self.assertEqual(response.status_code, 200)


class AccessScopeEndpoint(WorldTestCase):
    """Phase 3: GET /admin/access/scope - what the frontend reads to hide filter options and
    actions the caller isn't authorized for. Display only; it grants nothing itself, so its
    shape is tested here, not as a security boundary (that's every test above)."""

    def scope(self, who):
        response = self.get(who, "/admin/access/scope")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_super_admin_is_unrestricted_on_both_axes(self):
        self.assertEqual(self.scope("super"), {"allowed": True, "isSuper": True, "role": "super_admin", "zones": None, "regions": None})

    def test_company_admin_is_unrestricted_on_both_axes(self):
        body = self.scope("coadmin")
        self.assertEqual((body["isSuper"], body["zones"], body["regions"]), (False, None, None))

    def test_coordinator_is_restricted_to_their_zone_only(self):
        body = self.scope("coord")
        self.assertEqual((body["role"], body["zones"], body["regions"]), ("coordinator", ["north zone"], None))

    def test_sub_coordinator_is_restricted_to_their_region_only(self):
        body = self.scope("subcoord")
        self.assertEqual((body["role"], body["zones"], body["regions"]), ("sub_coordinator", None, ["delhi ncr"]))

    def test_no_grant_is_denied_before_it_can_explain_why(self):
        """Before get_current_admin's own membership check (Phase B), an ungranted account
        reached this endpoint and got back {"allowed": false, ...} - a graceful explanation the
        frontend could show. Now it's denied at the gate like everything else, the same 403, with
        no body to read. This endpoint still matters for a account that IS a tenant member but
        narrowly scoped (a Coordinator explaining which zone they're limited to, tested above) -
        it just can no longer explain a no-membership-at-all case to the account it's about,
        since that account can no longer reach any admin-panel endpoint at all."""
        self.assertEqual(self.get("ungranted", "/admin/access/scope").status_code, 403)

    def test_a_trainer_stored_in_the_admin_table_cannot_reach_it(self):
        """require_admin_role: this is an admin-panel concern, not something a trainer account
        (admin-table or agency-team) needs or should read."""
        self.assertEqual(self.get("trainer1", "/admin/access/scope").status_code, 403)


# ======================================================================= landed: Attendance List access control
class AttendanceListAccessControl(WorldTestCase):
    """/admin/attendance/page (ATTENDANCE) is now scoped by the same admin_access grant and the
    same SQL condition builder as the Training List - dashboard_repository.access_scope_conditions
    - replacing the legacy apply_identity_scope (company column + data_scopes zone rows,
    fail-open on a blank company). /admin/attendance?org=true (the non-paged cross-trainer view)
    gets the equivalent Python-side check via AccessScope.allows_row, since it isn't built from a
    SQL query."""

    def test_super_admin_sees_every_company(self):
        self.assertEqual(self.keys("super", ATTENDANCE), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V", "O_N1"})

    def test_company_admin_sees_their_company_only(self):
        self.assertEqual(self.keys("coadmin", ATTENDANCE), {"S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V"})

    def test_coordinator_sees_their_zone_only(self):
        north = {"S_N1", "S_DEL", "S_N1V"}
        self.assertEqual(self.keys("coord", ATTENDANCE), north)
        self.assertEqual(self.get("coord", ATTENDANCE).json()["total"], self.attendance_rows(north))

    def test_sub_coordinator_sees_their_region_only(self):
        self.assertEqual(self.keys("subcoord", ATTENDANCE), {"S_DEL"})

    def test_no_grant_returns_nothing(self):
        # get_current_admin (Phase B) denies an account with no grant at all before the request
        # reaches this list - see TrainingListAccessControl.test_no_grant_returns_nothing.
        self.assertEqual(self.get("ungranted", ATTENDANCE).status_code, 403)

    def test_a_grant_in_another_tenant_does_not_leak_into_this_one(self):
        self.assertEqual(self.get("betaonly", ATTENDANCE).status_code, 403)

    def test_query_params_cannot_widen_a_coordinators_zone(self):
        widened = self.get("coord", "/admin/attendance/page?mode=all&limit=200&zones=South%20Zone")
        self.assertEqual(widened.json()["items"], [])

    def test_a_forged_cursor_cannot_widen_the_attendance_scope(self):
        cursor = base64.urlsafe_b64encode(json.dumps({"s": "markedAt", "v": "2099-01-01T00:00:00", "id": 10**9}).encode()).decode()
        response = self.get("coord", f"/admin/attendance/page?mode=all&limit=200&cursor={cursor}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.w.conference_keys(response.json()["items"]), {"S_N1", "S_DEL", "S_N1V"})

    def test_the_non_paged_org_view_follows_the_same_scope(self):
        """/admin/attendance?org=true - a second, non-paged read of the same data (no live
        frontend caller today, but a real, callable endpoint) - Python-filtered via
        AccessScope.allows_row rather than SQL, but the same grant, the same result."""
        response = self.get("coord", "/admin/attendance?org=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.w.conference_keys(response.json()), {"S_N1", "S_DEL", "S_N1V"})
        self.assertEqual(self.get("ungranted", "/admin/attendance?org=true").status_code, 403)


# ======================================================================= landed: Trainee list access control
class TraineeListAccessControl(WorldTestCase):
    """GET /admin/trainees: an admin-table account (role="admin") is scoped by admin_access on
    Trainee's own company/zone/region columns (access_scope_conditions - no join needed); a
    trainer (agency-team, or an admin-table role="trainer" account) is scoped to their own
    assigned/rostered trainees instead (trainee_repository.trainer_owned_condition), unrelated
    to company/zone. test_a_trainer_sees_only_their_assigned_trainees /
    test_trainee_lists_follow_the_scope (above, now landed) already cover the by-role shapes in
    detail; this covers the remaining edge cases."""

    def trainees(self, who):
        return {t["traineeUid"] for t in self.get(who, "/admin/trainees").json()}

    def test_no_grant_sees_no_trainees(self):
        # get_current_admin (Phase B) denies an account with no grant at all before the request
        # reaches this list - see TrainingListAccessControl.test_no_grant_returns_nothing.
        self.assertEqual(self.get("ungranted", "/admin/trainees").status_code, 403)

    def test_a_grant_in_another_tenant_does_not_leak_into_this_one(self):
        self.assertEqual(self.get("betaonly", "/admin/trainees").status_code, 403)

    def test_super_admin_sees_every_company(self):
        special = {"TR-ASSIGNED-ONLY", "TR-ROSTER-ONLY", "TR-OTHER-TRAINER"}
        pair = lambda k: {f"TR-{k}-0", f"TR-{k}-1"}
        expected = pair("S_N1") | pair("S_DEL") | pair("S_S1") | pair("S_BLANK") | pair("S_N1V") | pair("O_N1") | special
        self.assertEqual(self.trainees("super"), expected)

    def test_adm_trainer_is_scoped_like_any_other_trainer(self):
        """An admin-table account whose role is "trainer" (not "admin") - tenant membership
        only, no admin_access company/zone/region grant - goes through the same ownership rule
        an agency-team trainer does, not the admin scope branch."""
        self.assertEqual(self.get("adm_trainer", "/admin/trainees").json(), [])  # assigned to no one, on no one's roster


class TraineeRegistrationAuthorization(WorldTestCase):
    """POST /admin/trainees: company/zone/region come from the request body like every other
    field on the form, but for a Company Admin, Coordinator or Sub-coordinator they also double
    as an authorization boundary - a mismatched value is a forged scope, not a typo, and is
    rejected rather than silently corrected."""

    def payload(self, **overrides):
        base = {
            "traineeUid": "TR-NEW", "fullName": "New Person", "designation": "Promoter", "gender": "Male",
            "primaryEmail": "new.person@example.com", "primaryPhone": "9123456780", "state": "Delhi",
            "zone": "North Zone", "region": "North 1", "company": "Samsung India", "requestedBy": "Quess Corp Ltd",
            "trainerId": "trainer1", "trainerName": "Trainer One", "supervisorId": "sup1", "supervisorName": "Sup One",
            "jobStatus": "Active", "username": "newperson", "password": "Correct-Horse-9",
        }
        base.update(overrides)
        return base

    def register(self, who, **overrides):
        return self.w.client.post("/admin/trainees", json=self.payload(**overrides), headers=self.w.headers(who))

    def test_company_admin_cannot_forge_a_different_company(self):
        response = self.register("coadmin", company="Other Co")
        self.assertEqual(response.status_code, 403)

    def test_company_admin_can_register_within_their_own_company_any_zone(self):
        response = self.register("coadmin", zone="South Zone", region="South 1")  # any zone is fine - whole company
        self.assertEqual(response.status_code, 201, response.text)

    def test_coordinator_cannot_forge_a_different_zone(self):
        response = self.register("coord", zone="South Zone")  # coord is granted North Zone
        self.assertEqual(response.status_code, 403)

    def test_coordinator_can_register_within_their_own_zone(self):
        response = self.register("coord", zone="North Zone", region="North 3")  # any region within their zone
        self.assertEqual(response.status_code, 201, response.text)

    def test_sub_coordinator_cannot_forge_a_different_region(self):
        response = self.register("subcoord", region="North 1")  # subcoord is granted Delhi NCR
        self.assertEqual(response.status_code, 403)

    def test_sub_coordinator_can_register_within_their_own_region(self):
        response = self.register("subcoord", zone="North Zone", region="Delhi NCR")
        self.assertEqual(response.status_code, 201, response.text)

    def test_super_admin_is_not_restricted_to_any_single_company(self):
        response = self.register("super", company="Other Co", zone="North Zone", region="North 1")
        self.assertEqual(response.status_code, 201, response.text)

    def test_a_rejected_registration_writes_nothing(self):
        self.register("coord", zone="South Zone")
        self.w.tenant_db[ALPHA].expire_all()
        self.assertIsNone(self.w.tenant_db[ALPHA].query(Trainee).filter_by(traineeUid="TR-NEW").first())


class DashboardStatsAccessControl(WorldTestCase):
    """GET /admin/dashboard/stats: same admin_access scope as the Training/Attendance/Trainee
    lists, replacing apply_identity_scope. The cache key already carries admin.id (see
    stats_cache_key), so isolation between accounts never depended on the scope mechanism."""

    def stats(self, who):
        response = self.get(who, "/admin/dashboard/stats?fresh=true")
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_super_admin_counts_every_company(self):
        self.assertEqual(self.stats("super")["audience"]["present"], 6)

    def test_company_admin_counts_their_company_only(self):
        self.assertEqual(self.stats("coadmin")["audience"]["present"], 5)

    def test_coordinator_counts_their_zone_only(self):
        self.assertEqual(self.stats("coord")["audience"]["present"], 3)

    def test_no_grant_is_denied(self):
        # get_current_admin (Phase B) denies an account with no grant at all before the request
        # reaches this endpoint - see TrainingListAccessControl.test_no_grant_returns_nothing.
        self.assertEqual(self.get("ungranted", "/admin/dashboard/stats?fresh=true").status_code, 403)

    def test_a_grant_in_another_tenant_is_denied_here(self):
        self.assertEqual(self.get("betaonly", "/admin/dashboard/stats?fresh=true").status_code, 403)


# ======================================================================= landed: login & per-request tenant membership
class LoginTenantMembership(WorldTestCase):
    """Phase A (admin_service.login) + Phase B (get_current_admin): an admin-table account's
    admin_access grant is now checked both when it logs in and on every subsequent request,
    reusing resolve_scope both times - not a second, parallel mechanism. Trainer (AgencyTeam)
    login/auth is untouched: it's already tenant-safe by construction (the account only exists
    inside its own tenant's database), so nothing here applies to it."""

    def login(self, who, tenant):
        return self.w.client.post("/admin/login", json={"username": who, "password": PASSWORD}, headers={"X-Tenant-ID": tenant})

    def test_every_role_can_log_into_a_tenant_it_is_actually_granted_for(self):
        for who in ("super", "coadmin", "coord", "subcoord"):
            with self.subTest(who=who):
                response = self.login(who, ALPHA)
                self.assertEqual(response.status_code, 200)
                self.assertIn("access_token", response.json())

    def test_a_coordinator_cannot_obtain_a_token_for_a_tenant_they_are_not_granted(self):
        response = self.login("coord", BETA)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("access_token", response.json())  # a rejected login issues no token at all

    def test_a_sub_coordinator_cannot_obtain_a_token_for_a_tenant_they_are_not_granted(self):
        self.assertEqual(self.login("subcoord", BETA).status_code, 403)

    def test_super_admin_logs_into_any_tenant(self):
        self.assertEqual(self.login("super", BETA).status_code, 200)  # explicit global grant

    def test_an_admin_with_no_grant_at_all_cannot_log_in(self):
        response = self.login("ungranted", ALPHA)
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("access_token", response.json())

    def test_a_grant_for_another_tenant_does_not_authorize_this_one(self):
        self.assertEqual(self.login("betaonly", ALPHA).status_code, 403)  # header cannot pick an unauthorised tenant

    def test_wrong_password_and_wrong_tenant_are_not_distinguishable_by_message(self):
        """Same detail text either way - the status code differs (401 bad credentials, 403 right
        credentials/wrong tenant) because that distinction is already the approved contract
        (test_a_coordinator_cannot_obtain_a_token_for_a_tenant_they_are_not_granted expects
        exactly 403), but neither response says which of username/password/tenant/grant it was."""
        bad_password = self.w.client.post("/admin/login", json={"username": "coadmin", "password": "wrong"}, headers={"X-Tenant-ID": ALPHA})
        wrong_tenant = self.login("coadmin", BETA)
        self.assertEqual(bad_password.status_code, 401)
        self.assertEqual(wrong_tenant.status_code, 403)
        self.assertNotIn("tenant", bad_password.json()["detail"].lower())
        self.assertNotIn("password", wrong_tenant.json()["detail"].lower())

    def test_trainer_login_is_unaffected(self):
        response = self.w.client.post("/admin/login", json={"username": "trainer1", "password": PASSWORD}, headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["admin"]["role"], "trainer")

    def test_a_grant_revoked_after_the_token_was_issued_stops_working_on_the_next_request(self):
        """The highest-value property of checking this per request rather than only at login:
        a 30-day token (see ACCESS_TOKEN_EXPIRE_MINUTES) must not keep working after the grant
        behind it is gone."""
        token = self.w.token("coadmin", ALPHA)
        self.assertEqual(self.w.client.get("/admin/trainees", headers={"Authorization": f"Bearer {token}"}).status_code, 200)

        row = self.w.common.query(AdminAccess).filter_by(admin_id=self.w.admins["coadmin"].id).one()
        row.active = 0
        row.company_admin_key = None  # ck_admin_access_company_key requires this on deactivation
        self.w.common.commit()

        self.assertEqual(self.w.client.get("/admin/trainees", headers={"Authorization": f"Bearer {token}"}).status_code, 403)

    def test_a_token_for_a_tenant_the_admin_does_not_belong_to_is_refused(self):
        token = create_access_token(subject="admin:betaonly", tenant_id=ALPHA, role="admin")  # minted with the tenant of their choice
        self.assertEqual(self.w.client.get("/admin/trainees", headers={"Authorization": f"Bearer {token}"}).status_code, 403)

    def test_a_token_with_no_tenant_claim_is_rejected(self):
        token = jwt.encode({"sub": "admin:coadmin", "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())},
                            settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        self.assertEqual(self.w.client.get("/admin/trainees", headers={"Authorization": f"Bearer {token}"}).status_code, 401)

    def test_internal_calls_cannot_skip_authorization_through_a_real_request(self):
        """admin=None only ever means "no principal to check" for a direct Python call (the
        SQL-equivalence test suites use it deliberately) - it must not be reachable by manipulating
        what an actual HTTP request sends. There is no request field that becomes `admin=None`;
        the account is always resolved server-side from the verified token."""
        response = self.w.client.get("/admin/trainees", headers={"Authorization": "Bearer "})
        self.assertIn(response.status_code, (401, 403))


# ======================================================================= landed: cross-endpoint regression
class CrossEndpointRegressionAfterAuthChange(WorldTestCase):
    """A representative spread of endpoints through get_current_admin, both an authorized
    success and an unauthorized denial, to prove the Phase B change didn't silently break
    something a narrower, endpoint-specific test wouldn't catch."""

    ENDPOINTS = [
        ("GET", TRAININGS), ("GET", ATTENDANCE), ("GET", "/admin/trainees"),
        ("GET", "/admin/dashboard/stats?fresh=true"), ("GET", "/admin/profile"),
        ("GET", "/admin/access/scope"), ("GET", f"/admin/trainings/{uid('S_N1')}"),
    ]

    def test_authorized_accounts_still_reach_every_endpoint(self):
        for method, path in self.ENDPOINTS:
            with self.subTest(path=path):
                self.assertEqual(self.w.client.request(method, path, headers=self.w.headers("coadmin")).status_code, 200)

    def test_an_unauthorized_account_is_denied_on_every_endpoint(self):
        for method, path in self.ENDPOINTS:
            with self.subTest(path=path):
                self.assertEqual(self.w.client.request(method, path, headers=self.w.headers("ungranted")).status_code, 403)


# ======================================================================= pending: approved end state
class RoleScopes(WorldTestCase):
    def test_an_admin_with_no_grant_is_denied_everywhere(self):
        for path in (TRAININGS, ATTENDANCE, "/admin/dashboard/stats?fresh=true", "/admin/trainees", "/admin/trainings/pending"):
            with self.subTest(path=path):
                self.assertEqual(self.get("ungranted", path).status_code, 403)

    def test_a_coordinator_sees_only_their_zone(self):
        north = {"S_N1", "S_DEL", "S_N1V"}  # blank-zone and other-zone trainings are not visible
        self.assertEqual(self.keys("coord", TRAININGS), north)
        self.assertEqual(self.keys("coord", ATTENDANCE), north)
        stats = self.get("coord", "/admin/dashboard/stats?fresh=true").json()
        self.assertEqual(stats["audience"]["present"], 3)
        self.assertEqual(self.get("coord", "/admin/attendance/page?mode=all&limit=200").json()["total"], self.attendance_rows(north))

    def test_a_sub_coordinator_sees_only_their_region(self):
        self.assertEqual(self.keys("subcoord", TRAININGS), {"S_DEL"})
        self.assertEqual(self.keys("subcoord", ATTENDANCE), {"S_DEL"})

    def test_trainee_lists_follow_the_scope(self):
        def trainees(who):
            return {t["traineeUid"] for t in self.get(who, "/admin/trainees").json()}

        special = {"TR-ASSIGNED-ONLY", "TR-ROSTER-ONLY", "TR-OTHER-TRAINER"}  # Samsung / North / North 1
        pair = lambda k: {f"TR-{k}-0", f"TR-{k}-1"}
        self.assertEqual(trainees("coadmin"), pair("S_N1") | pair("S_DEL") | pair("S_S1") | pair("S_BLANK") | pair("S_N1V") | special)
        self.assertEqual(trainees("coord"), pair("S_N1") | pair("S_DEL") | pair("S_N1V") | special)
        self.assertEqual(trainees("subcoord"), pair("S_DEL"))

    def test_manipulated_ids_look_like_they_do_not_exist(self):
        cases = {"coord": "S_S1", "subcoord": "S_N1", "coadmin": "O_N1"}  # a zone / region / company the account does not have
        for who, key in cases.items():
            with self.subTest(who=who, key=key):
                base = f"/admin/trainings/{uid(key)}"
                self.assertEqual(self.get(who, base).status_code, 404)
                self.assertEqual(self.get(who, base + "/detail").status_code, 404)
                self.assertEqual(self.get(who, base + "/report").status_code, 404)
                for action in ("approve", "reject"):
                    response = self.w.client.post(f"{base}/{action}", json={"message": "probe"}, headers=self.w.headers(who))
                    self.assertEqual(response.status_code, 404)
                self.w.tenant_db[ALPHA].expire_all()
                self.assertEqual(self.w.tenant_db[ALPHA].query(Conference).filter_by(conferenceUid=uid(key)).one().status, "Pending")  # untouched

    def test_walking_every_page_never_leaves_the_scope(self):
        """The list export walks every page with a cursor; forged cursors and page tricks are no wider."""
        seen, cursor = [], None
        for _ in range(50):
            url = "/admin/attendance/page?mode=all&limit=2" + (f"&cursor={cursor}" if cursor else "")
            body = self.get("coord", url).json()
            seen += body["items"]
            cursor = body["nextCursor"]
            if not cursor:
                break
        self.assertEqual(self.w.conference_keys(seen), {"S_N1", "S_DEL", "S_N1V"})
        self.assertEqual(len(seen), self.attendance_rows({"S_N1", "S_DEL", "S_N1V"}))

    def test_a_trainer_sees_only_their_assigned_trainees(self):
        response = self.get("trainer1", "/admin/trainees")
        self.assertEqual(response.status_code, 200)
        expected = {f"TR-{k}-{i}" for k in ("S_N1", "S_DEL", "S_N1V") for i in (0, 1)} | {"TR-ASSIGNED-ONLY", "TR-ROSTER-ONLY"}
        self.assertEqual({t["traineeUid"] for t in response.json()}, expected)  # not TR-OTHER-TRAINER, not other trainers' people

class TenantResolutionAndStatus(WorldTestCase):
    def test_an_invalid_token_never_selects_a_tenant(self):
        with patch.object(tenant_manager, "get_engine", wraps=tenant_manager.get_engine) as spy:
            response = self.w.client.get("/admin/trainees", headers={"Authorization": "Bearer not-a-jwt", "X-Tenant-ID": BETA})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(BETA, [call.args[0] for call in spy.call_args_list])

    def test_a_suspended_tenant_is_refused_even_after_first_use(self):
        self.assertEqual(self.get("super", "/admin/trainees").status_code, 200)  # warms the tenant's connection pool
        self.w.common.query(Tenant).filter_by(tenant_uid=ALPHA).update({"status": "suspended"})
        self.w.common.commit()
        getattr(tenant_manager, "clear_status_cache", lambda: None)()  # the step adds this so the test need not wait out the cache
        self.assertEqual(self.get("super", "/admin/trainees").status_code, 403)


class MediaIsTenantAndScopeBound(WorldTestCase):
    def test_files_are_tenant_folders_and_follow_the_scope(self):
        # A trainee photo is readable through the trainee that owns it (services/media_access.py).
        beta = self.w.tenant_db[BETA]
        beta.query(Trainee).filter(Trainee.traineeUid == "TR-B_N1-0").update({"profilePhoto": "trainee_photos/b.jpg"})
        beta.commit()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in (f"{ALPHA}/attendance_photos/{uid('S_N1')}/a.jpg", f"{ALPHA}/attendance_photos/{uid('S_S1')}/b.jpg", f"{BETA}/trainee_photos/b.jpg"):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_bytes(b"synthetic")
            with patch("app.routers.media.MEDIA_ROOT", root):
                get = lambda who, path, tenant=ALPHA: self.get(who, path, tenant).status_code
                self.assertEqual(get("coord", f"/media/attendance_photos/{uid('S_N1')}/a.jpg"), 200)        # own zone, own tenant folder
                self.assertIn(get("coord", f"/media/attendance_photos/{uid('S_S1')}/b.jpg"), (403, 404))   # another zone
                self.assertIn(get("coord", f"/media/{BETA}/trainee_photos/b.jpg"), (403, 404))             # naming another tenant's folder
                self.assertEqual(get("coord", "/media/trainee_photos/b.jpg"), 404)                          # BETA's file is not in ALPHA's folder
                self.assertEqual(get("betaonly", "/media/trainee_photos/b.jpg", BETA), 200)                 # ...but is BETA's own


class LiveUpdatesAreTenantScoped(WorldTestCase):
    """Phase C: /ws/live/{conferenceUid} - room MEMBERSHIP is authorized on join (not just the
    thin payload's own harmlessness). The conference is looked up only in the token's own
    verified tenant database, so a client-supplied uid can never reach another tenant's row."""

    def accepted(self, who, tenant, conference_key, token=None):
        url = f"/ws/live/{uid(conference_key)}?token={token or self.w.token(who, tenant)}"
        try:
            with self.w.client.websocket_connect(url):
                return True
        except Exception:
            return False

    def test_rooms_are_bound_to_the_token_tenant_and_scope(self):
        self.assertTrue(self.accepted("coord", ALPHA, "S_N1"))          # own zone
        self.assertFalse(self.accepted("coord", ALPHA, "S_S1"))         # another zone
        self.assertFalse(self.accepted("coadmin", ALPHA, "B_N1"))       # another tenant's training
        self.assertTrue(self.accepted("betaonly", BETA, "B_N1"))        # its own tenant

    def test_a_trainer_only_joins_their_own_conferences_room(self):
        self.assertTrue(self.accepted("trainer1", ALPHA, "S_N1"))    # their own
        self.assertFalse(self.accepted("trainer1", ALPHA, "S_S1"))   # trainer2's

    def test_a_trainee_only_joins_a_conference_they_are_on_the_roster_of(self):
        row = self.w.tenant_db[ALPHA].query(Trainee).filter_by(traineeUid="TR-S_N1-0").one()
        trainee_token = create_access_token(subject=str(row.phone), tenant_id=ALPHA, role="trainee")
        self.assertTrue(self.accepted(None, ALPHA, "S_N1", token=trainee_token))   # on S_N1's roster
        self.assertFalse(self.accepted(None, ALPHA, "S_S1", token=trainee_token))  # not on S_S1's

    def test_an_admin_with_no_grant_at_all_is_rejected(self):
        self.assertFalse(self.accepted("ungranted", ALPHA, "S_N1"))

    def test_a_nonexistent_conference_is_rejected(self):
        self.assertFalse(self.accepted("super", ALPHA, "DOES-NOT-EXIST"))

    def test_an_invalid_token_is_rejected(self):
        self.assertFalse(self.accepted(None, ALPHA, "S_N1", token="not-a-jwt"))

    def test_a_grant_revoked_before_the_connection_is_made_is_rejected(self):
        """Documents the revocation policy this phase actually implements: a NEW connection
        always re-checks (this test); an ALREADY-OPEN one is not force-closed mid-session (no
        mechanism for that exists yet - see the Phase C report)."""
        self.assertTrue(self.accepted("coadmin", ALPHA, "S_N1"))
        row = self.w.common.query(AdminAccess).filter_by(admin_id=self.w.admins["coadmin"].id).one()
        row.active = 0
        row.company_admin_key = None
        self.w.common.commit()
        self.assertFalse(self.accepted("coadmin", ALPHA, "S_N1"))


class _FakeSocket:
    """A `websocket.send_json`-shaped stand-in - ConnectionManager only ever calls that one
    method on what it's tracking, so this is enough to test its own routing logic (the tenant
    key, send_to/broadcast/disconnect) in complete isolation from the real ASGI/WebSocket
    plumbing, which the `accepted()`-based tests above already exercise end to end."""

    def __init__(self):
        self.received: list[dict] = []

    async def accept(self) -> None:
        pass

    async def send_json(self, event: dict) -> None:
        self.received.append(event)


class AdminChannelTenantIsolation(unittest.TestCase):
    """/ws/admin: connections are keyed by (tenant_id, username), not username alone - two
    different tenants' accounts that happen to share a username must never receive each other's
    events. Exercises `ConnectionManager` directly (see `_FakeSocket`) - a fresh instance per
    test, not the app's shared `manager`, so nothing here can leak into another test."""

    def setUp(self):
        from app.routers.ws import ConnectionManager

        self.manager = ConnectionManager()

    def test_two_tenants_with_the_same_username_are_isolated(self):
        async def scenario():
            alpha_sock, beta_sock = _FakeSocket(), _FakeSocket()
            await self.manager.connect(alpha_sock, "ALPHA", "super")
            await self.manager.connect(beta_sock, "BETA", "super")

            await self.manager.send_to("ALPHA", "super", {"for": "alpha"})
            self.assertEqual(alpha_sock.received, [{"for": "alpha"}])
            self.assertEqual(beta_sock.received, [])  # same username, other tenant - nothing

            await self.manager.send_to("BETA", "super", {"for": "beta"})
            self.assertEqual(beta_sock.received, [{"for": "beta"}])
            self.assertEqual(alpha_sock.received, [{"for": "alpha"}])  # unchanged

        asyncio.run(scenario())

    def test_broadcast_never_crosses_a_tenant_boundary(self):
        async def scenario():
            alpha_a, alpha_b, beta_a = _FakeSocket(), _FakeSocket(), _FakeSocket()
            await self.manager.connect(alpha_a, "ALPHA", "coord")
            await self.manager.connect(alpha_b, "ALPHA", "coadmin")
            await self.manager.connect(beta_a, "BETA", "coord")  # same username as alpha_a, other tenant

            await self.manager.broadcast("ALPHA", {"type": "training_created"})

            self.assertEqual(alpha_a.received, [{"type": "training_created"}])
            self.assertEqual(alpha_b.received, [{"type": "training_created"}])
            self.assertEqual(beta_a.received, [])  # never reaches BETA

        asyncio.run(scenario())

    def test_disconnecting_one_tenants_connection_does_not_affect_the_other(self):
        async def scenario():
            alpha_sock, beta_sock = _FakeSocket(), _FakeSocket()
            await self.manager.connect(alpha_sock, "ALPHA", "super")
            await self.manager.connect(beta_sock, "BETA", "super")

            self.manager.disconnect(alpha_sock, "ALPHA", "super")

            await self.manager.broadcast("BETA", {"type": "trainee_created"})
            self.assertEqual(beta_sock.received, [{"type": "trainee_created"}])  # still there

            await self.manager.send_to("ALPHA", "super", {"type": "should_not_arrive"})
            self.assertEqual(alpha_sock.received, [])  # gone

        asyncio.run(scenario())

    def test_multiple_connections_for_the_same_tenant_and_user_all_receive_the_event(self):
        async def scenario():
            first, second = _FakeSocket(), _FakeSocket()
            await self.manager.connect(first, "ALPHA", "coord")
            await self.manager.connect(second, "ALPHA", "coord")  # e.g. two device tabs

            await self.manager.send_to("ALPHA", "coord", {"type": "training_updated"})

            self.assertEqual(first.received, [{"type": "training_updated"}])
            self.assertEqual(second.received, [{"type": "training_updated"}])

        asyncio.run(scenario())


class OneTenantCannotHurtTheOthers(unittest.TestCase):
    """A slow / dead tenant database must not slow every other tenant down."""

    SLOW_SECONDS = 1.2

    def setUp(self):
        self.w = TenantWorld()

        def slow_connect():
            time.sleep(self.SLOW_SECONDS)
            return sqlite3.connect(":memory:", check_same_thread=False)

        self.w.common.add(Tenant(tenant_uid="SLOWT", company_name="Slow", database_host="h", database_port=3306, database_name="slow",
                                 database_username="u", database_password="p", status="active"))
        self.w.common.commit()
        tenant_manager.register_engine("SLOWT", create_engine("sqlite://", creator=slow_connect, poolclass=NullPool))

    def tearDown(self):
        tenant_manager._engines.pop("SLOWT", None)
        tenant_manager._sessionmakers.pop("SLOWT", None)
        self.w.close()

    @pending_phase_c("step 10: per-tenant concurrency limit")
    def test_flooding_a_slow_tenant_does_not_slow_a_healthy_one(self):
        async def scenario():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.w.app), base_url="http://t", timeout=60) as client:
                await client.get(f"/sessions/join/{uid('S_N1')}", headers={"X-Tenant-ID": ALPHA})  # warm-up
                flood = [asyncio.create_task(client.get("/sessions/join/X", headers={"X-Tenant-ID": "SLOWT"})) for _ in range(60)]
                await asyncio.sleep(0.3)
                started = time.perf_counter()
                await client.get(f"/sessions/join/{uid('S_N1')}", headers={"X-Tenant-ID": ALPHA})
                elapsed = time.perf_counter() - started
                await asyncio.gather(*flood, return_exceptions=True)
                return elapsed

        self.assertLess(asyncio.run(scenario()), 0.6)

    @pending_phase_c("step 10: keep-alive off the event loop")
    def test_the_keep_alive_does_not_freeze_the_event_loop(self):
        from app.main import _db_keepalive_loop

        async def scenario():
            gaps, stop = [], asyncio.Event()

            async def heartbeat():
                last = time.perf_counter()
                while not stop.is_set():
                    await asyncio.sleep(0.02)
                    now = time.perf_counter()
                    gaps.append(now - last)
                    last = now

            with patch("app.main.DB_KEEPALIVE_INTERVAL_SECONDS", 0.05):
                beat = asyncio.create_task(heartbeat())
                keepalive = asyncio.create_task(_db_keepalive_loop())
                await asyncio.sleep(self.SLOW_SECONDS + 1.5)
                keepalive.cancel()
                stop.set()
                await beat
            return max(gaps)

        self.assertLess(asyncio.run(scenario()), 0.5)


if __name__ == "__main__":
    unittest.main()
