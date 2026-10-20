"""The trainee home screen's session (GET /sessions/current) is only ever one the trainee is on
(user, 2026-10-13): the training their QR / share link names, else their own - one they joined or
were marked at - running now, else today's. A trainee who signs in without a QR and has no such
training gets "No Session" (404): never another trainer's live training, an approved / old one
they aren't on, nor their own trainer's they haven't joined - and opening the home screen never
joins them to anything.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture."""

from unittest.mock import patch

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.utils.date_utils import ist_now
from tests.tenant_fixtures import uid
from tests.test_phase4_operations import PRESENT, ROSTERED, S_N1, Phase4TestCase

S_S1 = uid("S_S1")       # trainer2's training
NOBODYS = "TR-ASSIGNED-ONLY"  # trainer1's trainee, on no training's roster


class HomeSessionSelection(Phase4TestCase):
    def setUp(self):
        super().setUp()
        # proctoring_settings_service binds CommonSessionLocal at import, outside TenantWorld's patch.
        settings_patch = patch("app.services.session_service.get_proctoring_settings", return_value=(True, 3))
        settings_patch.start()
        self.addCleanup(settings_patch.stop)

    def current(self, trainee_uid, conference_uid=None):
        query = f"?conference_uid={conference_uid}" if conference_uid else ""
        return self.as_trainee(trainee_uid, "GET", f"/sessions/current{query}")

    def set_status(self, conference_uid, status, **fields):
        self.alpha.query(Conference).filter(Conference.conferenceUid == conference_uid).update({"conferenceStatus": status, **fields})
        self.alpha.commit()

    def rows(self, trainee_uid):
        return self.alpha.query(Attendance).filter_by(traineeUid=trainee_uid).count()

    def todays_training(self, key, status="Scheduled"):
        conference_uid = uid(key)
        self.alpha.add(Conference(conferenceUid=conference_uid, company="Samsung India", zone="North Zone", region="North 1",
                                  trainerEmployeeId="trainer1", trainerName="Trainer1", conferenceDate=ist_now().strftime("%Y-%m-%d"),
                                  conferenceTime="23:59", conferenceStatus=status, status="Approved", postAssessmentUid="SUITE-1"))
        self.alpha.add(Attendance(attendanceUid=f"ATT-{key}", conferenceUid=conference_uid, traineeUid=PRESENT, status="Joined"))
        self.alpha.commit()
        return conference_uid

    def test_no_training_of_their_own_is_no_session_even_with_others_live_and_approved(self):
        self.set_status(S_S1, "Ongoing")  # another trainer's live training; the fixture's ADM one is Approved
        self.assertEqual(self.current(NOBODYS).status_code, 404)
        self.assertEqual(self.rows(NOBODYS), 0)  # and never joined to anything

    def test_their_own_trainers_live_training_they_havent_joined_is_no_session(self):
        self.set_status(S_N1, "Ongoing")
        self.assertEqual(self.current(NOBODYS).status_code, 404)
        self.assertEqual(self.rows(NOBODYS), 0)

    def test_a_pre_assigned_roster_row_not_activated_by_qr_is_no_session(self):
        self.set_status(S_N1, "Ongoing")  # ROSTERED is "Pending" on it
        self.assertEqual(self.current(ROSTERED).status_code, 404)

    def test_the_training_a_qr_names_is_shown(self):
        self.set_status(S_N1, "Ongoing")
        response = self.current(ROSTERED, conference_uid=S_N1)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conferenceUid"], S_N1)

    def test_their_own_running_training_is_shown_without_a_qr(self):
        self.set_status(S_N1, "Ongoing")
        response = self.current(PRESENT)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conferenceUid"], S_N1)

    def test_an_older_training_they_were_present_at_never_hides_todays(self):
        todays = self.todays_training("TODAY")  # PRESENT was Present at S_N1 (an older day), joined today's
        response = self.current(PRESENT)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conferenceUid"], todays)

    def test_a_cancelled_training_is_no_session(self):
        self.todays_training("CANCELLED", status="Cancelled")
        self.assertEqual(self.current(PRESENT).status_code, 404)  # S_N1 is an older day, not running

    def test_the_dashboard_shows_no_active_session_either(self):
        self.set_status(S_S1, "Ongoing")
        response = self.as_trainee(NOBODYS, "GET", "/sessions/dashboard?limit=5")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual((body["conferenceUid"], body["hasActiveSession"]), (None, False))
