"""Phase 7 - every route is classified, and every protected route is probed.

1. The route inventory is locked: a route added, removed or re-guarded without updating ROUTES
   fails here, so nothing new can ship unreviewed.
2. Every protected HTTP route refuses an anonymous caller; staff routes refuse trainee tokens and
   trainee routes refuse staff tokens; admin-only routes refuse trainers.
3. Every staff route that names a training refuses a trainer who isn't that training's trainer -
   with a VALID request (so the refusal is authorization, not validation) - and changes nothing.
4. Tokens for another tenant, a demoted trainer, a deactivated admin grant and a revoked token are
   refused on every staff route.
"""

import unittest

from fastapi.routing import APIRoute, APIWebSocketRoute

from app.core.security import create_access_token
from app.models.admin_access import AdminAccess
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from tests.tenant_fixtures import ALPHA, BETA, TenantWorld, uid

PUBLIC, STAFF, ADMIN, TRAINEE, ACCOUNT, WS = "public", "staff", "admin-only", "trainee", "any-account", "websocket"

# (method, path) -> who may call it. STAFF = get_current_admin (trainers and admin-panel accounts,
# further scoped inside); ADMIN = require_admin_role; ACCOUNT = staff or trainee (media).
ROUTES = {
    ("GET", "/"): PUBLIC,
    ("POST", "/admin/login"): PUBLIC,
    ("POST", "/trainees/login"): PUBLIC,
    ("POST", "/trainees/register"): PUBLIC,
    ("GET", "/sessions/join/{code}"): PUBLIC,  # QR preview - needs a signed join code (tests/test_join_codes.py)
    ("GET", "/admin/access/scope"): ADMIN,
    ("GET", "/admin/assessment-suites"): STAFF,
    ("POST", "/admin/assessment-suites"): ADMIN,
    ("GET", "/admin/assessment-suites/{suite_uid}"): ADMIN,
    ("POST", "/admin/assessment-suites/{suite_uid}/questions"): ADMIN,
    ("DELETE", "/admin/assessment-suites/{suite_uid}/questions/{question_id}"): ADMIN,
    ("GET", "/admin/attendance/page"): STAFF,
    ("GET", "/admin/audiences"): STAFF,
    ("GET", "/admin/checklist-items"): STAFF,
    ("GET", "/admin/dashboard/stats"): ADMIN,
    ("POST", "/admin/logout"): STAFF,
    ("GET", "/admin/maintenance/media-plan"): ADMIN,
    ("GET", "/admin/profile"): STAFF,
    ("PATCH", "/admin/profile"): STAFF,
    ("POST", "/admin/profile/aadhar"): STAFF,
    ("POST", "/admin/profile/photo"): STAFF,
    ("GET", "/admin/requested-by-options"): STAFF,
    ("GET", "/admin/session-types"): STAFF,
    ("POST", "/admin/trainees"): STAFF,
    ("GET", "/admin/trainees/page"): STAFF,
    ("POST", "/admin/trainees/{trainee_uid}/photo"): STAFF,
    ("GET", "/admin/trainers"): STAFF,
    ("GET", "/admin/trainers/{username}"): STAFF,
    ("GET", "/admin/training-hubs"): STAFF,
    ("GET", "/admin/training-types"): STAFF,
    ("POST", "/admin/trainings"): STAFF,
    ("GET", "/admin/trainings/facets"): STAFF,
    ("GET", "/admin/trainings/page"): STAFF,
    ("GET", "/admin/trainings/summary"): STAFF,
    ("GET", "/admin/trainings/{conference_uid}"): STAFF,
    ("PATCH", "/admin/trainings/{conference_uid}"): ADMIN,
    ("POST", "/admin/trainings/{conference_uid}/advance-module"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/approve"): ADMIN,
    ("DELETE", "/admin/trainings/{conference_uid}/attendance/{trainee_uid}"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/attendance/{trainee_uid}"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/attendance/{trainee_uid}/unlock"): STAFF,
    ("GET", "/admin/trainings/{conference_uid}/detail"): ADMIN,
    ("GET", "/admin/trainings/{conference_uid}/join-code"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/end"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/live-quiz/broadcast"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/live-quiz/finish"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/live-quiz/leaderboard"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/live-quiz/lobby"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/live-quiz/stop-timer"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/modules/stop-active"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/modules/{module_key}/restart"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/modules/{module_key}/start"): STAFF,
    ("GET", "/admin/trainings/{conference_uid}/performers"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/reject"): ADMIN,
    ("GET", "/admin/trainings/{conference_uid}/report"): STAFF,
    ("GET", "/admin/trainings/{conference_uid}/schedule-check"): STAFF,
    ("POST", "/admin/trainings/{conference_uid}/start"): STAFF,
    ("GET", "/admin/venues"): STAFF,
    ("GET", "/assessments/{suite_uid}/questions"): TRAINEE,
    ("POST", "/assessments/{suite_uid}/submit"): TRAINEE,
    ("POST", "/attendance/check-in"): TRAINEE,
    ("POST", "/attendance/check-in/secure"): TRAINEE,
    ("POST", "/attendance/verify-location"): TRAINEE,
    ("GET", "/media/{file_path:path}"): ACCOUNT,
    ("GET", "/sessions/current"): TRAINEE,
    ("GET", "/sessions/dashboard"): TRAINEE,
    ("GET", "/sessions/history"): TRAINEE,
    ("POST", "/sessions/join/{code}"): TRAINEE,
    ("GET", "/sessions/live-quiz"): TRAINEE,
    ("POST", "/sessions/live-quiz/answer"): TRAINEE,
    ("GET", "/sessions/live-quiz/results"): TRAINEE,
    ("GET", "/sessions/live-quiz/reveal"): TRAINEE,
    ("POST", "/sessions/live-quiz/submit"): TRAINEE,
    ("GET", "/sessions/live-quiz/summary"): TRAINEE,
    ("POST", "/sessions/live-quiz/timeout"): TRAINEE,
    ("POST", "/sessions/proctoring-lock"): TRAINEE,
    ("GET", "/sessions/trainings"): TRAINEE,
    ("GET", "/sessions/{conference_uid}/detail"): TRAINEE,
    ("POST", "/trainees/logout"): TRAINEE,
    ("PATCH", "/trainees/me"): TRAINEE,
    ("POST", "/trainees/me/photo"): TRAINEE,
    ("WS", "/ws/admin"): WS,
    ("WS", "/ws/live/{conference_uid}"): WS,
}

_GUARDS = {
    "require_admin_role": ADMIN,
    "get_current_admin": STAFF,
    "get_current_trainee": TRAINEE,
    "get_current_account": ACCOUNT,
}

OTHER_TRAINING, OTHER_TRAINEE = uid("S_S1"), "TR-S_S1-0"  # trainer2's training and trainee
PHOTO = {"photo": ("p.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 64, "image/jpeg")}


def _walk(routes):
    for route in routes:
        if type(route).__name__ == "_IncludedRouter":
            yield from _walk(route.original_router.routes)
        else:
            yield route


def _dependency_names(dependant) -> set:
    names = set()
    for dep in dependant.dependencies:
        if dep.call is not None:
            names.add(getattr(dep.call, "__name__", ""))
        names |= _dependency_names(dep)
    return names


def inventory(app) -> dict:
    found = {}
    for route in _walk(app.routes):
        if isinstance(route, APIRoute):
            names = _dependency_names(route.dependant)
            guard = next((cls for name, cls in _GUARDS.items() if name in names), PUBLIC)
            for method in route.methods:
                found[(method, route.path)] = guard
        elif isinstance(route, APIWebSocketRoute):
            found[("WS", route.path)] = WS
    return found


def concrete(path: str) -> str:
    return (path.replace("{conference_uid}", OTHER_TRAINING).replace("{trainee_uid}", OTHER_TRAINEE)
            .replace("{module_key}", "ATTENDANCE").replace("{suite_uid}", "SUITE-1").replace("{question_id}", "1")
            .replace("{username}", "trainer2").replace("{code}", OTHER_TRAINING).replace("{file_path:path}", "x/y.png"))


def valid_request(method: str, path: str) -> dict:
    """A request that passes validation, so a refusal can only come from authorization."""
    if path.endswith("/start") and "{module_key}" not in path:
        return {"files": PHOTO, "data": {"latitude": "0", "longitude": "0"}}
    if path.endswith("/end"):
        return {"files": {**PHOTO, "attendanceSheet": ("s.pdf", b"%PDF-1.4", "application/pdf")}, "data": {"totalPax": "1"}}
    if path.endswith("/photo") or path.endswith("/aadhar"):
        return {"files": {"file": PHOTO["photo"]}}
    if "/attendance/{trainee_uid}" in path:
        return {"json": {"reason": "audit"} if method == "DELETE" or path.endswith("/unlock") else {"status": "Present", "reason": "audit"}}
    if path.endswith("/broadcast"):
        return {"json": {"questionId": 1}}
    if path.endswith("/approve") or path.endswith("/reject"):
        return {"json": {"reason": "audit"}}
    if method == "PATCH" and "{conference_uid}" in path:
        return {"json": {"trainingStatus": "Cancelled"}}
    if method in ("POST", "PATCH", "DELETE"):
        return {"json": {}}
    return {}


class RouteCoverage(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.routes = inventory(self.w.app)

    def call(self, method, path, headers=None, **kwargs):
        return self.w.client.request(method, concrete(path), headers=headers or {}, **kwargs)

    def trainee_headers(self, trainee_uid="TR-S_N1-0", tenant=ALPHA):
        phone = self.w.tenant_db[ALPHA].query(Trainee).filter_by(traineeUid=trainee_uid).one().phone
        return {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=tenant, role='trainee')}"}

    def of(self, *classes):
        return sorted(key for key, cls in self.routes.items() if cls in classes and key[0] != "WS")

    # ---------------------------------------------------------------- 1. the inventory is locked
    def test_every_route_is_classified_and_guarded_as_reviewed(self):
        self.assertEqual(set(self.routes) - set(ROUTES), set(), "new, unreviewed routes")
        self.assertEqual(set(ROUTES) - set(self.routes), set(), "reviewed routes that no longer exist")
        changed = {key: (ROUTES[key], cls) for key, cls in self.routes.items() if ROUTES[key] != cls}
        self.assertEqual(changed, {}, "routes whose guard changed")

    # ------------------------------------------------------------- 2. who may call what, at all
    def test_anonymous_callers_are_refused_everywhere_but_the_public_routes(self):
        for method, path in self.of(STAFF, ADMIN, TRAINEE, ACCOUNT):
            with self.subTest(method=method, path=path):
                self.assertEqual(self.call(method, path, **valid_request(method, path)).status_code, 401)

    def test_trainee_tokens_are_refused_on_staff_routes(self):
        headers = self.trainee_headers()
        for method, path in self.of(STAFF, ADMIN):
            with self.subTest(method=method, path=path):
                self.assertIn(self.call(method, path, headers, **valid_request(method, path)).status_code, (401, 403))

    def test_staff_tokens_are_refused_on_trainee_routes(self):
        for who in ("trainer1", "super"):
            for method, path in self.of(TRAINEE):
                with self.subTest(who=who, method=method, path=path):
                    response = self.call(method, path, self.w.headers(who), **valid_request(method, path))
                    self.assertIn(response.status_code, (401, 403))

    def test_trainers_are_refused_on_admin_only_routes(self):
        for who in ("trainer1", "adm_trainer"):
            for method, path in self.of(ADMIN):
                with self.subTest(who=who, method=method, path=path):
                    self.assertEqual(self.call(method, path, self.w.headers(who), **valid_request(method, path)).status_code, 403)

    # ------------------------------------------------ 3. another trainer's training: refused, unchanged
    def snapshot(self):
        db = self.w.tenant_db[ALPHA]
        db.expire_all()
        conference = db.query(Conference).filter_by(conferenceUid=OTHER_TRAINING).one()
        rows = db.query(Attendance).filter_by(conferenceUid=OTHER_TRAINING).order_by(Attendance.id).all()
        return (
            {c.key: getattr(conference, c.key) for c in Conference.__table__.columns},
            [{c.key: getattr(r, c.key) for c in Attendance.__table__.columns} for r in rows],
        )

    def test_a_trainer_cannot_read_or_change_another_trainers_training(self):
        self.w.tenant_db[ALPHA].query(Conference).filter_by(conferenceUid=OTHER_TRAINING).update(
            {"status": "Approved", "conferenceStatus": "Ongoing", "activeModuleId": "ATTENDANCE"})
        self.w.tenant_db[ALPHA].commit()
        before = self.snapshot()
        on_a_training = [key for key in self.of(STAFF) if "{conference_uid}" in key[1]]
        self.assertEqual(len(on_a_training), 19)  # every one of them is probed below
        for method, path in on_a_training:
            with self.subTest(method=method, path=path):
                response = self.call(method, path, self.w.headers("trainer1"), **valid_request(method, path))
                self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(self.snapshot(), before)

    def test_the_trainings_own_trainer_passes_the_same_requests_authorization(self):
        # The control for the test above: the same valid requests are NOT refused as "not found"
        # for trainer2, whose training it is (they may still fail a business rule, e.g. 409).
        self.w.tenant_db[ALPHA].query(Conference).filter_by(conferenceUid=OTHER_TRAINING).update(
            {"status": "Approved", "conferenceStatus": "Ongoing"})
        self.w.tenant_db[ALPHA].commit()
        for method, path in [k for k in self.of(STAFF) if "{conference_uid}" in k[1] and k[0] == "GET"]:
            with self.subTest(method=method, path=path):
                response = self.call(method, path, self.w.headers("trainer2"), **valid_request(method, path))
                self.assertNotIn(response.status_code, (401, 403, 404), response.text)

    # ------------------------------------------ 4. other tenant, demoted, deactivated, revoked
    def assert_refused_on_staff_routes(self, headers, allowed=(401, 403)):
        for method, path in self.of(STAFF, ADMIN):
            with self.subTest(method=method, path=path):
                self.assertIn(self.call(method, path, headers, **valid_request(method, path)).status_code, allowed)

    def test_a_token_for_another_tenant_is_refused(self):
        self.assert_refused_on_staff_routes(self.w.headers("trainer1", tenant=BETA))

    def test_a_demoted_trainer_is_refused(self):
        db = self.w.tenant_db[ALPHA]
        db.query(AgencyTeam).filter_by(username="trainer1").update({"role": "manager"})
        db.commit()
        self.assert_refused_on_staff_routes(self.w.headers("trainer1"))

    def test_an_admin_with_a_deactivated_grant_sees_nothing(self):
        self.w.common.query(AdminAccess).filter(AdminAccess.admin_id == self.w.admins["coadmin"].id).update(
            {"active": 0, "company_admin_key": None})
        self.w.common.commit()
        headers = self.w.headers("coadmin")
        for path in ("/admin/trainings/page", "/admin/attendance/page", "/admin/trainees/page", "/admin/dashboard/stats",
                     "/admin/trainers", "/admin/trainings/facets"):
            with self.subTest(path=path):
                response = self.w.client.get(path, headers=headers)
                if response.status_code == 200:
                    body = response.json()
                    items = body.get("items", body if isinstance(body, list) else None)
                    if items is not None:
                        self.assertEqual(items, [], path)
                    elif "training" in body:
                        self.assertEqual(body["training"]["planned"], 0)
                    else:
                        self.assertEqual(body, {"trainingHubs": [], "trainingTypes": []})
                else:
                    self.assertIn(response.status_code, (401, 403))

    def test_a_revoked_token_is_refused(self):
        headers = self.w.headers("trainer1")
        self.assertEqual(self.w.client.post("/admin/logout", headers=headers).status_code, 204)  # revokes every token
        self.assert_refused_on_staff_routes(headers, allowed=(401,))


if __name__ == "__main__":
    unittest.main()
