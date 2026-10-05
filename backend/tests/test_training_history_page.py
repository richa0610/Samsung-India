"""GET /sessions/trainings - the trainee's Training History a page at a time (infinite scroll),
and the India-date "today" used by the trainer's Home and the start-of-session rule."""

import unittest
from datetime import datetime
from unittest.mock import patch

from app.core.security import create_access_token
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.services import session_service, trainee_dashboard_service
from tests.tenant_fixtures import ALPHA, TenantWorld

ME = "TR-HIST"


class TrainingHistoryPage(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.db = self.w.tenant_db[ALPHA]
        self.db.add(Trainee(traineeUid=ME, name="History", email="h@example.test", phone=8_200_000_000))
        # 45 trainings on distinct dates, newest = day 45; every 5th cancelled; Present on odd days.
        for day in range(1, 46):
            uid = f"CONF-H{day:02d}"
            date = f"2026-{(day - 1) // 28 + 7:02d}-{(day - 1) % 28 + 1:02d}"
            self.db.add(Conference(conferenceUid=uid, trainerEmployeeId="trainer1", conferenceDate=date,
                                   conferenceStatus="Cancelled" if day % 5 == 0 else "Completed"))
            self.db.add(Attendance(attendanceUid=f"ATT-H{day:02d}", conferenceUid=uid, traineeUid=ME,
                                   status="Present" if day % 2 else "Pending"))
        self.db.commit()
        phone = self.db.query(Trainee).filter_by(traineeUid=ME).one().phone
        self.headers = {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=ALPHA, role='trainee')}"}

    def get(self, query=""):
        response = self.w.client.get(f"/sessions/trainings{query}", headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_pages_walk_every_training_once_newest_first(self):
        first = self.get("?page=1&limit=10")
        self.assertEqual((first["total"], first["totalPages"], first["page"], first["pageSize"]), (36, 4, 1, 10))
        seen = []
        for page in range(1, 5):
            seen += [row["conferenceUid"] for row in self.get(f"?page={page}&limit=10")["items"]]
        self.assertEqual(len(seen), 36)
        self.assertEqual(len(set(seen)), 36)                                  # nothing twice
        self.assertNotIn("CONF-H05", seen)                                    # cancelled ones are left out
        self.assertEqual(seen[0], "CONF-H44")                                 # newest first (45 is cancelled)
        self.assertEqual(self.get("?page=5&limit=10")["items"], [])           # past the end

    def test_same_rows_as_the_dashboard_built_them(self):
        trainee = self.db.query(Trainee).filter_by(traineeUid=ME).one()
        dashboard = trainee_dashboard_service.build_trainee_dashboard(self.db, trainee, 500)
        walked = []
        for page in range(1, 3):
            walked += self.get(f"?page={page}&limit=20")["items"]
        self.assertEqual(walked, [row.model_dump() for row in dashboard.trainings])

    def test_the_status_filter_applies_before_paging(self):
        body = self.get("?status=Missed&limit=5")
        self.assertEqual(body["total"], 18)                                  # the Pending ones, cancelled excluded
        self.assertTrue(all(row["status"] == "Missed" for row in body["items"]))
        self.assertEqual(self.get("?status=Completed&limit=50")["total"], 18)

    def test_the_date_range_applies_before_paging(self):
        body = self.get("?start=2026-08-01&end=2026-08-10&limit=50")
        self.assertTrue(all("2026-08-01" <= row["rawDate"] <= "2026-08-10" for row in body["items"]))
        self.assertEqual(body["total"], len(body["items"]))

    def add_training(self, uid, date, status):
        self.db.add(Conference(conferenceUid=uid, trainerEmployeeId="trainer1", conferenceDate=date, conferenceStatus=status))
        self.db.add(Attendance(attendanceUid=f"ATT-{uid}", conferenceUid=uid, traineeUid=ME, status="Pending"))
        self.db.commit()

    def me(self):
        return self.db.query(Trainee).filter_by(traineeUid=ME).one()

    def test_a_dashboard_card_lists_exactly_the_trainings_it_counted(self):
        self.add_training("CONF-ON", "2026-09-01", "Ongoing")
        self.add_training("CONF-NS", "2020-01-01", "Scheduled")    # its day passed, never started
        self.add_training("CONF-UP", "2099-01-01", "Scheduled")
        metrics = trainee_dashboard_service.build_trainee_dashboard(self.db, self.me(), 5).metrics
        listed = {}
        for card in ("present", "absent", "ongoing", "notStarted", "scheduled"):
            body = self.get(f"?card={card}&limit=100")
            self.assertEqual(body["total"], getattr(metrics, card), card)
            listed[card] = {row["conferenceUid"] for row in body["items"]}
        self.assertEqual(listed["present"], {f"CONF-H{day:02d}" for day in range(1, 46, 2) if day % 5})
        self.assertEqual(listed["absent"], {f"CONF-H{day:02d}" for day in range(2, 46, 2) if day % 5})
        self.assertEqual((listed["ongoing"], listed["notStarted"], listed["scheduled"]), ({"CONF-ON"}, {"CONF-NS"}, {"CONF-UP"}))
        self.assertEqual(sum(map(len, listed.values())), metrics.totalTrainings)   # each training in one card

    def test_a_dashboard_card_keeps_the_dashboards_date_range(self):
        dates = "start=2026-07-01&end=2026-07-10"
        metrics = trainee_dashboard_service.build_trainee_dashboard(self.db, self.me(), 5, "2026-07-01", "2026-07-10").metrics
        self.assertEqual(self.get(f"?card=present&{dates}&limit=100")["total"], metrics.present)
        self.assertEqual(self.get(f"?card=absent&{dates}&limit=100")["total"], metrics.absent)
        self.assertEqual(self.get(f"?{dates}&limit=100")["total"], metrics.totalTrainings)   # the Total card

    def test_an_unknown_card_is_refused(self):
        response = self.w.client.get("/sessions/trainings?card=everything", headers=self.headers)
        self.assertEqual(response.status_code, 422)

    def test_the_dashboard_reports_the_current_session_not_the_last_training_counted(self):
        self.add_training("CONF-ON", "2026-09-01", "Ongoing")     # the live session - current
        self.add_training("CONF-UP", "2099-01-01", "Scheduled")   # counted after it
        current, started, _start_at = session_service._select_current_conference(self.db, trainee=self.me())
        self.assertEqual((current.conferenceUid, started), ("CONF-ON", True))
        dashboard = trainee_dashboard_service.build_trainee_dashboard(self.db, self.me(), 5)
        self.assertEqual((dashboard.conferenceUid, dashboard.hasActiveSession), ("CONF-ON", True))

    def test_limits_are_bounded(self):
        for query in ("?limit=0", "?limit=101", "?page=0"):
            with self.subTest(query=query):
                self.assertEqual(self.w.client.get(f"/sessions/trainings{query}", headers=self.headers).status_code, 422)

    def test_only_the_trainees_own_trainings(self):
        other = self.db.query(Trainee).filter_by(traineeUid="TR-S_N1-0").one()
        headers = {"Authorization": f"Bearer {create_access_token(subject=str(other.phone), tenant_id=ALPHA, role='trainee')}"}
        rows = self.w.client.get("/sessions/trainings?limit=100", headers=headers).json()["items"]
        self.assertFalse(any(row["conferenceUid"].startswith("CONF-H") for row in rows))
        self.assertEqual(self.w.client.get("/sessions/trainings").status_code, 401)


class TodayIsTheIndiaDate(unittest.TestCase):
    """00:30 IST on the 30th is still the 29th in UTC: "today" must be the 30th."""

    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        db = self.w.tenant_db[ALPHA]
        db.add(Conference(conferenceUid="CONF-TODAY", trainerEmployeeId="trainer1", conferenceDate="2026-09-30",
                          conferenceStatus="Scheduled", status="Approved"))
        db.commit()

    def test_the_trainer_home_counts_todays_trainings_in_india(self):
        with patch("app.services.training_service.ist_now", return_value=datetime(2026, 9, 30, 0, 30)):
            body = self.w.client.get("/admin/trainings/summary", headers=self.w.headers("trainer1")).json()
        self.assertEqual(body["totalSessions"], 1)
