"""Trainer Flow Phase 2.1 - security closeout.

Uploaded files (per-tenant folders + per-resource authorization), admin placement of trainings
(edit and create stay inside the caller's grant), trainee registration against every rule of a
grant, trainer-role-only agency login, and the attendance-reset audit entry.

Same synthetic TenantWorld (in-memory SQLite, temporary media folder) - never a real database or
the real media disk.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from app.core import rate_limit
from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.logs_master import LogsMaster
from app.models.trainee import Trainee
from tests.tenant_fixtures import ALPHA, BETA, PASSWORD, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

PDF = ("aadhar.pdf", b"%PDF-1.4 synthetic", "application/pdf")


class MediaTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for target in ("app.routers.media.MEDIA_ROOT", "app.core.media.MEDIA_ROOT"):
            p = patch(target, self.root)
            p.start()
            self.addCleanup(p.stop)

    def put(self, relative, tenant=ALPHA, content=b"synthetic"):
        path = self.root / tenant / relative if tenant else self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def status(self, who, relative, tenant=ALPHA):
        return self.w.client.get(f"/media/{relative}", headers=self.headers_for(who, tenant)).status_code

    def headers_for(self, who, tenant=ALPHA):
        if who.startswith("TR-"):  # a trainee, by traineeUid
            db = self.w.tenant_db[tenant]
            phone = db.query(Trainee).filter(Trainee.traineeUid == who).one().phone
            return {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=tenant, role='trainee')}"}
        return self.w.headers(who, tenant)

    def update(self, model, key_column, key, **values):
        self.alpha.query(model).filter(key_column == key).update(values)
        self.alpha.commit()


class UploadsAreStoredPerTenant(MediaTestCase):
    def test_an_upload_lands_in_the_uploaders_tenant_folder(self):
        response = self.w.client.post("/admin/profile/aadhar", files={"file": PDF}, headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        agent_id = self.w.agency["trainer1"].id
        self.assertTrue((self.root / ALPHA / f"trainer_documents/aadhar/agency_{agent_id}.pdf").is_file())
        self.assertFalse((self.root / "trainer_documents").exists())

    def test_same_named_uploads_in_two_tenants_never_collide(self):
        beta = self.w.tenant_db[BETA]
        twin = AgencyTeam(agencyTeamUid="g-beta", username="beta_agent", name="Beta Agent", password=hash_password(PASSWORD),
                          role="trainer", company="Samsung India")
        beta.add(twin)
        beta.commit()
        self.assertEqual(twin.id, self.w.agency["trainer1"].id)  # same row id in each tenant database
        for who, tenant, body in (("trainer1", ALPHA, b"%PDF alpha"), ("beta_agent", BETA, b"%PDF beta")):
            response = self.w.client.post("/admin/profile/aadhar", files={"file": ("a.pdf", body, "application/pdf")},
                                          headers=self.w.headers(who, tenant))
            self.assertEqual(response.status_code, 200, response.text)
        path = f"trainer_documents/aadhar/agency_{twin.id}.pdf"
        own = self.w.client.get(f"/media/{path}", headers=self.w.headers("trainer1"))
        self.assertEqual(own.content, b"%PDF alpha")


class FilesFollowTheirOwnersRule(MediaTestCase):
    def test_an_aadhaar_document_is_readable_by_its_owner_only(self):
        self.w.client.post("/admin/profile/aadhar", files={"file": PDF}, headers=self.w.headers("trainer1"))
        path = f"trainer_documents/aadhar/agency_{self.w.agency['trainer1'].id}.pdf"
        self.assertEqual(self.status("trainer1", path), 200)
        for who in ("trainer2", "coadmin", "super", "TR-S_N1-0"):
            with self.subTest(who=who):
                self.assertEqual(self.status(who, path), 404)

    def test_a_trainee_photo_follows_the_trainee_scope(self):
        path = "trainee_photos/TR-ASSIGNED-ONLY.jpg"
        self.put(path)
        self.update(Trainee, Trainee.traineeUid, "TR-ASSIGNED-ONLY", profilePhoto=path)
        expected = {"TR-ASSIGNED-ONLY": 200, "trainer1": 200, "coadmin": 200, "coord": 200,
                    "TR-S_N1-0": 404, "trainer2": 404, "trainer3": 404, "subcoord": 404}
        for who, code in expected.items():
            with self.subTest(who=who):
                self.assertEqual(self.status(who, path), code)

    def test_session_files_follow_the_conference_scope(self):
        path = f"trainer_checkin_photos/{uid('S_N1')}.jpg"
        self.put(path)
        self.update(Conference, Conference.conferenceUid, uid("S_N1"), startConferenceImage=path)
        expected = {"trainer1": 200, "coord": 200, "super": 200, "trainer2": 404, "subcoord": 404, "TR-S_N1-0": 404}
        for who, code in expected.items():
            with self.subTest(who=who):
                self.assertEqual(self.status(who, path), code)

    def test_a_check_in_photo_is_readable_by_its_trainee_and_the_sessions_staff(self):
        path = "attendance_photos/legacy-flat-name.jpg"  # the older, conference-less naming
        self.put(path)
        self.update(Attendance, Attendance.attendanceUid, "ATT-S_N1-0", checkInPhoto=path)
        expected = {"TR-S_N1-0": 200, "trainer1": 200, "coord": 200, "TR-S_N1-1": 404, "trainer2": 404}
        for who, code in expected.items():
            with self.subTest(who=who):
                self.assertEqual(self.status(who, path), code)

    def test_a_file_no_record_owns_is_refused(self):
        self.put("trainee_photos/orphan.jpg")
        self.put("trainer_documents/aadhar/agency_999.pdf")
        for path in ("trainee_photos/orphan.jpg", "trainer_documents/aadhar/agency_999.pdf"):
            with self.subTest(path=path):
                self.assertEqual(self.status("super", path), 404)

    def test_the_default_avatars_are_shared(self):
        self.put("trainer_photos/default_male.png", tenant=None)
        for who in ("trainer1", "super", "TR-S_N1-0"):
            with self.subTest(who=who):
                self.assertEqual(self.status(who, "trainer_photos/default_male.png"), 200)


class MediaCannotBeProbedOrEscaped(MediaTestCase):
    def test_another_tenants_file_is_never_served(self):
        path = "trainee_photos/TR-B_N1-0.jpg"
        self.put(path, tenant=BETA)
        self.w.tenant_db[BETA].query(Trainee).filter(Trainee.traineeUid == "TR-B_N1-0").update({"profilePhoto": path})
        self.w.tenant_db[BETA].commit()
        self.assertEqual(self.status("betaonly", path, BETA), 200)
        for who in ("super", "coadmin", "trainer1"):
            with self.subTest(who=who):
                self.assertEqual(self.status(who, path), 404)
                self.assertEqual(self.status(who, f"{BETA}/{path}"), 404)

    def test_path_tricks_and_unknown_folders_are_refused(self):
        self.put("trainee_photos/x.jpg", tenant=BETA)
        for path in ("attendance_photos/..%2F..%2FBETA/trainee_photos/x.jpg", "attendance_photos/%2e%2e/%2e%2e/x.jpg",
                     "ALPHA/trainee_photos/x.jpg", "somewhere/else.jpg", ""):
            with self.subTest(path=path):
                self.assertEqual(self.status("super", path), 404)

    def test_an_anonymous_or_forged_request_is_refused(self):
        self.put("trainer_photos/default_male.png", tenant=None)
        self.assertIn(self.w.client.get("/media/trainer_photos/default_male.png").status_code, (401, 403))
        forged = {"Authorization": "Bearer not.a.token"}
        self.assertEqual(self.w.client.get("/media/trainer_photos/default_male.png", headers=forged).status_code, 401)

    def test_pre_split_uploads_are_served_to_the_default_tenant_only(self):
        path = "trainee_photos/TR-ASSIGNED-ONLY.jpg"
        self.put(path, tenant=None)  # an upload from before the per-tenant folders
        self.update(Trainee, Trainee.traineeUid, "TR-ASSIGNED-ONLY", profilePhoto=path)
        self.assertEqual(self.status("trainer1", path), 404)
        with patch.object(settings, "DEFAULT_TENANT_ID", ALPHA):
            self.assertEqual(self.status("trainer1", path), 200)


class AdminTrainingPlacement(TrainerWorldTestCase):
    def form(self, key="S_N1", **overrides):
        row = self.alpha.query(Conference).filter(Conference.conferenceUid == uid(key)).one()
        body = {"company": row.company, "zone": row.zone, "region": row.region, "trainerEmployeeId": row.trainerEmployeeId,
                "trainerName": row.trainerName, "conferenceDate": "2026-10-05", "conferenceTime": "11:00 AM"}
        body.update(overrides)
        return body

    def patch(self, who, key, body):
        return self.w.client.patch(f"/admin/trainings/{uid(key)}", json=body, headers=self.w.headers(who))

    def company_of(self, key):
        self.alpha.expire_all()
        return self.alpha.query(Conference).filter(Conference.conferenceUid == uid(key)).one().company

    def test_a_full_edit_inside_the_grant_still_works(self):
        self.assertEqual(self.patch("coord", "S_N1", self.form()).status_code, 200)
        self.assertEqual(self.patch("coadmin", "S_S1", self.form("S_S1", zone="North Zone", region="North 1")).status_code, 200)

    def test_an_edit_cannot_move_a_training_outside_the_grant(self):
        cases = [("coadmin", "S_S1", {"company": "Other Co"}), ("coord", "S_N1", {"zone": "South Zone"}),
                 ("subcoord", "S_DEL", {"region": "North 1"})]
        for who, key, change in cases:
            with self.subTest(who=who, change=change):
                self.assertEqual(self.patch(who, key, self.form(key, **change)).status_code, 403)
        self.assertEqual(self.company_of("S_S1"), "Samsung India")

    def test_a_partial_edit_cannot_blank_the_place_of_a_training(self):
        # Rule 3 (Phase 2.2): a PATCH changes only what it sends, so leaving company/zone out keeps them.
        response = self.patch("coadmin", "S_S1", {"conferenceDate": "2026-10-05", "conferenceTime": "11:00 AM"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.company_of("S_S1"), "Samsung India")

    def test_a_trainer_must_be_an_active_trainer_of_this_tenant(self):
        beta_trainer = Admin(adminUid="a-bt", username="beta_trainer", name="Beta Trainer", password=hash_password(PASSWORD),
                             role="trainer", company="Samsung India")
        self.w.common.add(beta_trainer)
        self.w.common.flush()
        self.w.grant(beta_trainer, "trainer", BETA)
        self.w.common.commit()
        for trainer in ("beta_trainer", "ghost"):
            with self.subTest(trainer=trainer):
                self.assertEqual(self.patch("super", "S_N1", self.form(trainerEmployeeId=trainer)).status_code, 403)
        self.assertEqual(self.patch("super", "S_N1", self.form(trainerEmployeeId="trainer2")).status_code, 200)

    def test_an_unchanged_legacy_trainer_does_not_block_an_edit(self):
        self.alpha.query(Conference).filter(Conference.conferenceUid == uid("S_N1")).update({"trainerEmployeeId": "legacy_x"})
        self.alpha.commit()
        self.assertEqual(self.patch("coord", "S_N1", self.form()).status_code, 200)

    def test_a_super_admin_may_place_a_training_anywhere(self):
        self.assertEqual(self.patch("super", "S_N1", self.form(company="Other Co", zone="South Zone")).status_code, 200)

    def test_creation_follows_the_same_rule(self):
        base = {"conferenceDate": "2026-10-01", "conferenceTime": "10:00 AM", "trainerEmployeeId": "trainer1"}
        refused = [("coadmin", {"company": "Other Co"}), ("coord", {"company": "Samsung India", "zone": "South Zone"})]
        for who, place in refused:
            with self.subTest(who=who, place=place):
                response = self.w.client.post("/admin/trainings", json={**base, **place}, headers=self.w.headers(who))
                self.assertEqual(response.status_code, 403)
        self.assertEqual(self.alpha.query(Conference).filter(Conference.conferenceDate == "2026-10-01").count(), 0)


class TraineeRegistrationAgainstEveryRule(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        # A grant spanning two companies: Company Admin of Other Co + Coordinator of Samsung India / North Zone.
        two = Admin(adminUid="a-two", username="twoco", name="Two Co", password=hash_password(PASSWORD), role="admin")
        self.w.common.add(two)
        self.w.common.flush()
        self.w.grant(two, "company_admin", ALPHA, "Other Co")
        self.w.grant(two, "coordinator", ALPHA, "Samsung India", zone="North Zone")
        self.w.common.commit()
        self.w.admins["twoco"] = two

    def register(self, n, company, zone):
        body = {"traineeUid": f"TR-NEW-{n}", "fullName": "New Person", "designation": "Promoter", "gender": "Male",
                "primaryEmail": f"new{n}@example.com", "primaryPhone": f"912345678{n}", "state": "Delhi", "zone": zone,
                "region": "North 1", "company": company, "requestedBy": "Quess", "trainerId": "trainer1",
                "trainerName": "Trainer One", "supervisorId": "sup1", "supervisorName": "Sup One", "jobStatus": "Active",
                "username": f"newperson{n}", "password": "Correct-Horse-9"}
        return self.w.client.post("/admin/trainees", json=body, headers=self.w.headers("twoco")).status_code

    def test_a_multi_company_grant_is_checked_rule_by_rule(self):
        self.assertEqual(self.register(1, "Third Co", "North Zone"), 403)      # used to pass: the company check was skipped
        self.assertEqual(self.register(2, "Samsung India", "South Zone"), 403)  # outside the coordinator's zone
        self.assertEqual(self.register(3, "Other Co", "South Zone"), 201)       # Company Admin of Other Co: any zone
        self.assertEqual(self.register(4, "Samsung India", "North Zone"), 201)


class TrainerRoleOnlyLogin(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        rate_limit.reset()  # the login rate limiter is process-wide; start each test fresh

    def login(self, username, password=PASSWORD):
        return self.w.client.post("/admin/login", json={"username": username, "password": password}, headers={"X-Tenant-ID": ALPHA})

    def test_only_the_trainer_role_can_sign_in_as_a_trainer(self):
        self.assertEqual(self.login("trainer1").status_code, 200)
        for role in (None, "", "manager"):
            with self.subTest(role=role):
                self.set_agency_role("trainer1", role)
                self.assertEqual(self.login("trainer1").status_code, 403)

    def test_a_wrong_password_is_still_a_401_whatever_the_role(self):
        self.set_agency_role("trainer1", None)
        self.assertEqual(self.login("trainer1", "wrong").status_code, 401)

    def test_the_role_is_compared_like_everywhere_else_and_returned_as_trainer(self):
        self.set_agency_role("trainer1", " Trainer ")
        body = self.login("trainer1").json()
        self.assertEqual(body["admin"]["role"], "trainer")

    def test_a_token_issued_before_the_role_changed_stops_working(self):
        headers = self.w.headers("trainer1")
        self.set_agency_role("trainer1", None)
        self.assertEqual(self.w.client.get("/admin/profile", headers=headers).status_code, 403)


class AttendanceResetIsAudited(TrainerWorldTestCase):
    def resets(self):
        return [r.remarks for r in self.alpha.query(LogsMaster).filter(LogsMaster.action == "RESET_ATTENDANCE")]

    REASON = {"reason": "Marked the wrong person"}

    def reset(self, key, trainee):
        # Rule 4 (Phase 2.2): a reset carries a reason and only works while the session runs.
        return self.w.client.request("DELETE", f"/admin/trainings/{uid(key)}/attendance/{trainee}",
                                     json=self.REASON, headers=self.w.headers("trainer1"))

    def test_a_reset_writes_who_cleared_whose_record(self):
        self.set_status(uid("S_N1"), "Ongoing")
        self.assertEqual(self.reset("S_N1", "TR-S_N1-0").status_code, 200)
        self.assertEqual(self.resets(), [f"Reset attendance of TR-S_N1-0 for {uid('S_N1')}: Marked the wrong person"])
        self.reset("S_N1", "TR-S_N1-0")  # nothing left to reset
        self.assertEqual(len(self.resets()), 1)

    def test_a_refused_reset_writes_nothing(self):
        self.set_status(uid("S_S1"), "Ongoing")
        self.assertEqual(self.reset("S_S1", "TR-S_S1-0").status_code, 404)  # trainer2's session
        self.assertEqual(self.resets(), [])
