"""A training is stored the other system's way (user, 2026-10-17) - created, edited, started, run and
ended through the API - while the app is still answered in its own words, and a training stored either
way is reachable by exactly the same people:

  - company = its agency ID (a name for an unregistered company), trainer = their account ID and
    "Name (username)"; admin grants (by company name) and trainer ownership (by login name) still match
  - Scheduled / Started / Session Completed; Attendance_0 / Assessment_<set> / Quiz_<set> / ""; quiz
    WAITING / CLOSED; the clock as an India date-time; sessionConfig as their list; times "14:00"
  - their creation values: "Not Assigned", "defaultfile.png", radius 100, enableCheckIn 0, the planned
    last day, "Pending", the masterRemarks note, capitals for state / district, India start /
    end times, uploads in the training's own folder

Synthetic TenantWorld (in-memory SQLite) only - see tests/tenant_fixtures.py."""

import json
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from app.models.agency import Agency
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.utils.date_utils import ist_now
from tests.tenant_fixtures import ALPHA, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

PHOTO = ("p.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 64, "image/jpeg")
SHEET = ("s.pdf", b"%PDF-1.4", "application/pdf")
SAMSUNG_ID = "AGEN2497849"


class StoredTheirWayTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        self.w.common.add(Agency(agencyUid=SAMSUNG_ID, companyName="Samsung India", name="Contact", status="Approved"))
        self.w.common.commit()

    def conference(self, conference_uid):
        self.alpha.expire_all()
        return self.alpha.query(Conference).filter(Conference.conferenceUid == conference_uid).one()


class ANewTraining(StoredTheirWayTestCase):
    def create(self, who="coadmin", **overrides):
        body = {
            "zone": "North", "region": "North 1", "trainerEmployeeId": "trainer2",
            "trainerName": "Trainer2", "conferenceDate": "2026-10-20", "conferenceTime": "02:00 PM",
            "state": "Delhi", "district": "New Delhi",
            "sessionFlow": {
                "attendance": {"checkInOpens": "02:00 PM", "checkOutCloses": "05:00 PM", "geoFencing": True},
                "liveQuiz": {"assessmentSuiteUid": "SUITE-Q", "questionCount": 3, "startTime": "03:00 PM",
                             "unlockCondition": "Manual Broadcast"},
            },
            **overrides,
        }
        response = self.post(who, "/admin/trainings", body)
        self.assertEqual(response.status_code, 200, response.text)
        return self.conference(response.json()["conferenceUid"])

    def detail(self, who, conference_uid):
        response = self.get(who, f"/admin/trainings/{conference_uid}/detail")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_it_is_stored_their_way(self):
        c = self.create()
        self.assertRegex(c.conferenceUid, r"^CONF\d{7}$")
        self.assertEqual(
            (c.company, c.trainerEmployeeId, c.trainerName, c.updatedBy),
            (SAMSUNG_ID, "g2", "Trainer2 (trainer2)", "a-coadmin"),
        )
        self.assertEqual(
            (c.conferenceStatus, c.conferenceType, c.conferenceEndsOn, c.conferenceTime, c.activeModuleId),
            ("Scheduled", "Non-Residential Conference", "2026-10-20", "14:00", None),
        )
        self.assertEqual((c.trainingHub, c.venueUid, c.geoRadius, c.enableCheckIn), ("Not Assigned", "Not Assigned", 100, 0))
        self.assertEqual((c.attendanceSheet, c.hotelBill, c.conferenceImage, c.startConferenceImage),
                         ("defaultfile.png", "defaultfile.png", "defaultfile.png", None))
        self.assertEqual((c.state, c.district), ("DELHI", "NEW DELHI"))
        self.assertEqual((c.status, c.remarks), ("Pending", None))
        self.assertEqual(c.masterRemarks, f"New Non Residential Conference added by Coadmin (a-coadmin) | UID: {c.conferenceUid}")
        self.assertIsNotNone(c.token)                                      # the login's fingerprint, as on attendance
        self.assertEqual(json.loads(c.sessionConfig), [
            {"type": "Attendance", "config": {"date": "2026-10-20", "checkInTime": "14:00", "checkOutTime": "17:00", "geoFencing": "1"}},
            {"type": "Quiz", "linkedUid": "SUITE-Q", "questionCount": "3",
             "config": {"date": "2026-10-20", "startTime": "15:00", "endTime": "", "unlockCondition": "Manual"}},
        ])

    def test_the_app_reads_it_back_in_its_own_words(self):
        c = self.create()
        detail = self.detail("coadmin", c.conferenceUid)
        self.assertEqual(
            {key: detail[key] for key in ("company", "trainerEmployeeId", "trainerName", "conferenceTime", "state", "district",
                                          "trainingHub", "venue", "conferenceStatus", "remarks", "checkOutPhoto", "attendanceSheet",
                                          "isResidential")},
            {"company": "Samsung India", "trainerEmployeeId": "trainer2", "trainerName": "Trainer2 (trainer2)",
             "conferenceTime": "02:00 PM", "state": "Delhi", "district": "New Delhi", "trainingHub": None, "venue": None,
             "conferenceStatus": "Scheduled", "remarks": None, "checkOutPhoto": None, "attendanceSheet": None,
             "isResidential": False},
        )
        self.assertEqual(detail["sessionFlow"]["attendance"],
                         {"checkInOpens": "02:00 PM", "checkOutCloses": "05:00 PM", "geoFencing": True, "geoRadius": 100})
        quiz = detail["sessionFlow"]["liveQuiz"]
        self.assertEqual((quiz["assessmentSuiteUid"], quiz["startTime"], quiz["unlockCondition"], quiz["questionCount"]),
                         ("SUITE-Q", "03:00 PM", "Manual Broadcast", 3))

    def test_the_assigned_trainer_reaches_it_by_their_id_and_no_other_trainer_does(self):
        c = self.create()
        self.assertEqual(self.get("trainer2", f"/admin/trainings/{c.conferenceUid}").status_code, 200)
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{c.conferenceUid}").status_code, 404)
        self.assertIn(c.conferenceUid, {i["conferenceUid"] for i in self.get("trainer2", "/admin/trainings/page?limit=200").json()["items"]})
        self.assertNotIn(c.conferenceUid, {i["conferenceUid"] for i in self.get("trainer1", "/admin/trainings/page?limit=200").json()["items"]})

    def test_a_grant_on_the_company_name_covers_it_stored_by_agency_id(self):
        c = self.create()
        for who, sees in (("coadmin", True), ("coord", True), ("subcoord", False)):
            with self.subTest(who=who):
                items = self.get(who, "/admin/trainings/page?limit=200").json().get("items", [])
                self.assertEqual(c.conferenceUid in {i["conferenceUid"] for i in items}, sees)
                self.assertEqual(self.get(who, f"/admin/trainings/{c.conferenceUid}").status_code, 200 if sees else 404)

    def test_the_trainer_filter_finds_it_by_login_name(self):
        c = self.create()
        items = self.get("coadmin", "/admin/trainings/page?limit=200&trainers=trainer2").json()["items"]
        self.assertIn(c.conferenceUid, {i["conferenceUid"] for i in items})

    def test_the_company_is_the_tenants_and_a_form_cannot_name_one(self):
        c = self.create(who="super", trainerEmployeeId="trainer3", trainerName="Trainer3")
        self.assertEqual((c.company, c.trainerEmployeeId), (SAMSUNG_ID, "g3"))
        body = {"company": "Other Co", "conferenceDate": "2026-10-20", "conferenceTime": "02:00 PM"}
        self.assertEqual(self.post("super", "/admin/trainings", body).status_code, 422)

    def test_a_tenant_linked_to_its_agency_stores_that_id(self):
        self.w.common.query(Tenant).filter(Tenant.tenant_uid == ALPHA).update({"agency_uid": "AGY2687355"})
        self.w.common.commit()
        self.assertEqual(self.create().company, "AGY2687355")

    def test_an_unregistered_company_keeps_its_name(self):
        self.w.common.query(Agency).delete()
        self.w.common.commit()
        self.assertEqual(self.create().company, "Samsung India")

    def test_a_tenant_missing_from_the_registry_cannot_create(self):
        self.w.common.query(Tenant).filter(Tenant.tenant_uid == ALPHA).delete()
        self.w.common.commit()
        response = self.post("super", "/admin/trainings", {"conferenceDate": "2026-10-20", "conferenceTime": "02:00 PM"})
        self.assertEqual(response.status_code, 409, response.text)

    def test_an_admin_table_trainer_is_stored_by_their_admin_id(self):
        c = self.create(who="super", trainerEmployeeId="adm_trainer", trainerName="Adm Trainer")
        self.assertEqual((c.trainerEmployeeId, c.trainerName), ("a-adm_trainer", "Adm_Trainer (adm_trainer)"))
        self.assertEqual(self.get("adm_trainer", f"/admin/trainings/{c.conferenceUid}").status_code, 200)

    def test_a_residential_training_stores_its_last_day(self):
        c = self.create(isResidential=True, trainingEndDate="2026-10-23")
        self.assertEqual((c.conferenceType, c.conferenceEndsOn), ("Residential Conference", "2026-10-23"))
        self.assertTrue(c.masterRemarks.startswith("New Residential Conference added by Coadmin (a-coadmin)"))
        self.assertEqual(self.detail("coadmin", c.conferenceUid)["trainingEndDate"], "2026-10-23")

    def test_an_edit_keeps_their_format(self):
        c = self.create()
        response = self.w.client.patch(f"/admin/trainings/{c.conferenceUid}", headers=self.w.headers("coadmin"),
                                       json={"conferenceDate": "2026-10-21", "message": "Re check <ok>"})
        self.assertEqual(response.status_code, 200, response.text)
        c = self.conference(c.conferenceUid)
        self.assertEqual((c.conferenceEndsOn, c.trainerEmployeeId, c.company), ("2026-10-21", "g2", SAMSUNG_ID))
        self.assertEqual({module["config"]["date"] for module in json.loads(c.sessionConfig)}, {"2026-10-21"})
        self.assertEqual(c.remarks, "<p>Re check &lt;ok&gt;</p>")

        response = self.w.client.patch(f"/admin/trainings/{c.conferenceUid}", headers=self.w.headers("coadmin"),
                                       json={"trainerEmployeeId": "trainer1", "trainerName": "Trainer1", "trainingHub": "Delhi"})
        self.assertEqual(response.status_code, 200, response.text)
        c = self.conference(c.conferenceUid)
        self.assertEqual((c.trainerEmployeeId, c.trainerName, c.trainingHub), ("g1", "Trainer1 (trainer1)", "Delhi"))

    def test_a_trainer_creating_their_own_is_stored_by_their_id(self):
        c = self.create(who="trainer1", trainerEmployeeId="trainer1", trainerName="Trainer1")
        self.assertEqual((c.company, c.trainerEmployeeId, c.updatedBy), (SAMSUNG_ID, "g1", "g1"))
        self.assertEqual(c.masterRemarks, f"New Non Residential Conference added by Trainer1 (g1) | UID: {c.conferenceUid}")
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{c.conferenceUid}").status_code, 200)

    def test_an_edit_without_the_company_keeps_it_inside_the_grant(self):
        c = self.create()
        response = self.w.client.patch(f"/admin/trainings/{c.conferenceUid}", headers=self.w.headers("coadmin"),
                                       json={"conferenceTime": "04:00 PM"})
        self.assertEqual(response.status_code, 200, response.text)
        c = self.conference(c.conferenceUid)
        self.assertEqual((c.conferenceTime, c.company), ("16:00", SAMSUNG_ID))

    def test_not_assigned_is_never_a_training_hub_option(self):
        self.create()
        options = self.get("coadmin", "/admin/training-hubs").json()
        self.assertNotIn("Not Assigned", [option["value"] for option in options])


class ASessionRun(StoredTheirWayTestCase):
    """Start -> modules -> Live Quiz -> End, as trainer1 on their own S_N1."""

    S_N1 = uid("S_N1")

    def setUp(self):
        super().setUp()
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for target in ("app.routers.media.MEDIA_ROOT", "app.core.media.MEDIA_ROOT"):
            self.enterContext(patch(target, root))
        self.root = root
        flow = [{"type": "Attendance", "config": {"date": "2026-09-20", "checkInTime": "10:00", "checkOutTime": "", "geoFencing": "0"}},
                {"type": "Quiz", "linkedUid": "SUITE-Q", "questionCount": "1", "config": {"date": "2026-09-20", "startTime": "11:00", "endTime": "", "unlockCondition": "Manual"}}]
        self.alpha.query(Conference).filter(Conference.conferenceUid == self.S_N1).update({
            "status": "Approved", "conferenceTime": "09:00", "sessionConfig": json.dumps(flow),
        })
        self.alpha.commit()
        self.headers = self.w.headers("trainer1")

    def act(self, path, **kwargs):
        response = self.w.client.post(f"/admin/trainings/{self.S_N1}{path}", headers=self.headers, **kwargs)
        self.assertEqual(response.status_code, 200, response.text)
        return response

    def dashboard(self):
        return self.get("trainer1", f"/admin/trainings/{self.S_N1}").json()

    def test_every_step_is_stored_their_way_and_read_in_the_apps_words(self):
        self.act("/start", files={"photo": PHOTO}, data={"latitude": "28.4967", "longitude": "77.1615", "scheduleOverrideReason": "late"})
        c = self.conference(self.S_N1)
        self.assertEqual(c.conferenceStatus, "Started")
        self.assertRegex(c.startConferenceImage, rf"^{self.S_N1}/Host_CHECKIN_START_\d{{14}}\.jpg$")
        self.assertTrue(any(self.root.rglob(c.startConferenceImage.split("/")[-1])))       # written to disk
        self.assertLess(abs(c.actualStartedAt - ist_now()), timedelta(minutes=1))     # India time
        self.assertEqual((float(c.geoLatitude), float(c.geoLongitude)), (28.4967, 77.1615))   # no venue: the trainer's
        self.assertEqual(self.dashboard()["conferenceStatus"], "Ongoing")

        self.act("/modules/ATTENDANCE/start")
        self.assertEqual(self.conference(self.S_N1).activeModuleId, "Attendance_0")
        self.assertEqual(self.dashboard()["activeModuleId"], "ATTENDANCE")

        # Run order is by planned time: Attendance 10:00, Quiz 11:00, then the Standard Test (no time).
        self.act("/advance-module")
        c = self.conference(self.S_N1)
        self.assertEqual((c.activeModuleId, c.liveQuizState), ("Quiz_SUITE-Q", "WAITING"))
        dashboard = self.dashboard()
        self.assertEqual((dashboard["activeModuleId"], dashboard["liveStudio"]["state"]), ("LIVE_QUIZ", "IDLE"))

        self.act("/advance-module")                                     # the quiz is finished as the flow leaves it
        c = self.conference(self.S_N1)
        self.assertEqual((c.activeModuleId, c.liveQuizState), ("Assessment_SUITE-1", "CLOSED"))

        self.act("/end", files={"photo": PHOTO, "attendanceSheet": SHEET}, data={"totalPax": "2"})
        c = self.conference(self.S_N1)
        self.assertEqual((c.conferenceStatus, c.activeModuleId, c.liveQuizState), ("Session Completed", "", "CLOSED"))
        self.assertRegex(c.conferenceImage, rf"^{self.S_N1}/Host_CHECKIN_CLOSE_\d{{14}}\.jpg$")
        self.assertRegex(c.attendanceSheet, rf"^{self.S_N1}/Host_AttendanceSheet_\d{{14}}\.pdf$")
        self.assertLess(abs(c.actualEndedAt - ist_now()), timedelta(minutes=1))
        self.assertIsNone(c.conferenceEndsOn)                           # the planned last day - never the end time
        self.assertEqual(self.dashboard()["conferenceStatus"], "Completed")
        self.assertEqual(self.get("trainer1", f"/admin/trainings/{self.S_N1}/report").status_code, 200)

    def test_the_uploads_are_served_to_who_may_open_the_training_only(self):
        self.act("/start", files={"photo": PHOTO}, data={"scheduleOverrideReason": "late"})
        path = self.conference(self.S_N1).startConferenceImage
        self.assertEqual(self.get("trainer1", f"/media/{path}").status_code, 200)
        self.assertEqual(self.get("coadmin", f"/media/{path}").status_code, 200)
        self.assertEqual(self.get("trainer2", f"/media/{path}").status_code, 404)
        self.assertEqual(self.get("trainer1", f"/media/{self.S_N1}/someone-elses.jpg").status_code, 404)

    def test_a_venue_location_is_never_replaced_by_the_trainers(self):
        self.alpha.query(Conference).filter(Conference.conferenceUid == self.S_N1).update({"geoLatitude": 28.6139, "geoLongitude": 77.2090})
        self.alpha.commit()
        self.act("/start", files={"photo": PHOTO}, data={"latitude": "28.4967", "longitude": "77.1615", "scheduleOverrideReason": "late"})
        c = self.conference(self.S_N1)
        self.assertEqual((float(c.geoLatitude), float(c.geoLongitude)), (28.6139, 77.2090))

    def test_a_started_training_cannot_be_started_or_ended_twice(self):
        self.act("/start", files={"photo": PHOTO}, data={"scheduleOverrideReason": "late"})
        self.act("/end", files={"photo": PHOTO, "attendanceSheet": SHEET}, data={"totalPax": "1"})
        again = self.w.client.post(f"/admin/trainings/{self.S_N1}/end", headers=self.headers,
                                   files={"photo": PHOTO, "attendanceSheet": SHEET}, data={"totalPax": "1"})
        self.assertEqual(again.status_code, 409)
        restart = self.w.client.post(f"/admin/trainings/{self.S_N1}/start", headers=self.headers,
                                     files={"photo": PHOTO}, data={"scheduleOverrideReason": "late"})
        self.assertEqual(restart.status_code, 409)
