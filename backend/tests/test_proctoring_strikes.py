"""Proctoring strikes, recorded and enforced on the server (services/proctoring_strikes.py).

- Every strike the app reports (each with its own ID) is counted under its reason
  (attendance.securityDetails JSON), takes one off the theftAttemptsLeft countdown and adds a
  theftRemarks line.
- The server counts strikes since the last unlock itself and locks the trainee out once they
  reach the company's warning limit - an app restarted mid-test can't delay it - and a locked
  trainee can neither open nor submit the Standard Test until a trainer unlocks them.
- A strike or lock report sent twice counts once; a strike arriving late still counts; every write
  holds the trainee's attendance row, so concurrent ones run one after another.
- An unlock (at most 2) adds 3 to the countdown and keeps every count, total, strike ID and log
  line; the unlock count is stored, and older rows still count their " -> UNLOCK: " lines.
- An older app - no strike reports, only the final lockout, without an ID and with its own reason
  text - keeps working."""

import json
from itertools import count
from unittest.mock import patch

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult, Question
from app.repositories import attendance_repository
from tests.test_phase4_operations import ELSEWHERE, NOWHERE, PRESENT, ROSTERED, S_N1, Phase4TestCase

SIDE_LOOK, NO_FACE, TILT = "SIDE-LOOK DETECTED", "NO FACE DETECTED", "EXCESSIVE HEAD TILT"
UNLOCK = f"/admin/trainings/{S_N1}/attendance/{PRESENT}/unlock"


class ProctoringStrikesTestCase(Phase4TestCase):
    WARNING_LIMIT = 3

    def setUp(self):
        super().setUp()
        settings_patch = patch(
            "app.services.session_service.get_proctoring_settings", return_value=(True, self.WARNING_LIMIT)
        )
        settings_patch.start()
        self.addCleanup(settings_patch.stop)
        self._ids = count(1)

    def new_id(self) -> str:
        return f"strike-{next(self._ids):04d}"

    def strike(self, strike_id=None, reason=SIDE_LOOK, trainee=PRESENT):
        body = {"conferenceUid": S_N1, "violationType": reason, "strikeId": strike_id or self.new_id()}
        return self.as_trainee(trainee, "POST", "/sessions/proctoring-violation", json=body)

    def lockout(self, number=3, reason=SIDE_LOOK, strike_id=None):
        body = {"conferenceUid": S_N1, "violationType": reason, "strikeNumber": number}
        if strike_id:
            body["strikeId"] = strike_id
        return self.as_trainee(PRESENT, "POST", "/sessions/proctoring-lock", json=body)

    def unlock(self, reason="Camera glare, not cheating"):
        return self.post("trainer1", UNLOCK, {"reason": reason})

    def row(self, trainee=PRESENT) -> Attendance:
        self.alpha.expire_all()
        return self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=trainee).one()

    def set_row(self, **values):
        self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=PRESENT).update(values)
        self.alpha.commit()

    def state(self) -> dict:
        return json.loads(self.row().securityDetails or "{}").get("proctoring", {})

    def log(self) -> list[str]:
        return (self.row().theftRemarks or "").splitlines()

    def lock_with_three_strikes(self):
        """What the current app sends: two warning strikes, then the lockout with the third's ID."""
        self.strike(reason=SIDE_LOOK)
        self.strike(reason=NO_FACE)
        self.lockout(3, SIDE_LOOK, strike_id=self.new_id())


class StrikesAreCounted(ProctoringStrikesTestCase):
    def test_each_strike_is_counted_under_its_reason(self):
        self.assertEqual(self.strike(reason=SIDE_LOOK).json(), {"counted": True, "attemptsLeft": 2, "locked": False})
        self.assertEqual(self.strike(reason=NO_FACE).json(), {"counted": True, "attemptsLeft": 1, "locked": False})
        self.assertEqual((self.state()["reasons"], self.state()["total"]), ({SIDE_LOOK: 1, NO_FACE: 1}, 2))
        self.assertEqual((self.row().isTheftLocked, self.row().theftAttemptsLeft), (0, 1))
        self.assertTrue(self.log()[0].endswith(f"STRIKE #2: {NO_FACE}") and self.log()[1].endswith(f"STRIKE #1: {SIDE_LOOK}"))

    def test_an_app_restarted_mid_test_cant_delay_the_lock(self):
        # The app keeps its own strike count in memory: after a restart it starts over, but each
        # strike still has a new ID, and the server counts them itself.
        self.strike()
        self.strike()
        # ... app restarted here ...
        self.assertTrue(self.strike().json()["locked"])
        self.assertEqual(self.state()["total"], 3)


class ServerSideLockout(ProctoringStrikesTestCase):
    def test_the_strike_that_reaches_the_warning_limit_locks_the_trainee(self):
        self.strike(reason=SIDE_LOOK)
        self.strike(reason=NO_FACE)
        self.assertEqual(self.strike(reason=TILT).json(), {"counted": True, "attemptsLeft": 0, "locked": True})
        row = self.row()
        self.assertEqual((row.isTheftLocked, row.theftAttemptsLeft, self.state()["total"]), (1, 0, 3))
        self.assertTrue(self.log()[0].endswith(f"LOCKED strike #3: {TILT}"))
        current = self.as_trainee(PRESENT, "GET", f"/sessions/current?conference_uid={S_N1}").json()
        self.assertTrue(current["proctoringLocked"])

    def test_a_locked_trainee_cannot_open_or_submit_the_test_until_unlocked(self):
        self.open_module("STANDARD_TEST")
        self.lock_with_three_strikes()
        questions = f"/assessments/SUITE-1/questions?conferenceUid={S_N1}"
        submit = {"conferenceUid": S_N1, "answers": self.answers("a", "b", "c")}
        self.assertEqual(self.as_trainee(PRESENT, "GET", questions).status_code, 403)
        self.assertEqual(self.as_trainee(PRESENT, "POST", "/assessments/SUITE-1/submit", json=submit).status_code, 403)
        self.assertEqual(self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=PRESENT).count(), 0)
        self.assertEqual(self.unlock().status_code, 200)
        self.assertEqual(self.as_trainee(PRESENT, "GET", questions).status_code, 200)

    def test_the_lock_is_for_the_test_only_not_the_survey(self):
        self.alpha.add(Question(assessmentSuiteUid="SURVEY-1", question="Useful?", options="[]", points=0))
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"surveyUid": "SURVEY-1"})
        self.alpha.commit()
        self.lock_with_three_strikes()
        self.open_module("SURVEY")
        self.assertEqual(self.as_trainee(PRESENT, "GET", f"/assessments/SURVEY-1/questions?conferenceUid={S_N1}").status_code, 200)


class CompanyWarningLimit(ProctoringStrikesTestCase):
    WARNING_LIMIT = 5

    def test_the_lock_follows_the_companys_warning_limit(self):
        for _ in range(4):
            self.assertFalse(self.strike().json()["locked"])
        self.assertTrue(self.strike().json()["locked"])
        self.assertEqual(self.row().isTheftLocked, 1)


class DuplicatesAndConcurrency(ProctoringStrikesTestCase):
    def test_a_resent_strike_counts_once(self):
        strike_id = self.new_id()
        self.strike(strike_id)
        self.assertEqual(self.strike(strike_id).json(), {"counted": False, "attemptsLeft": 2, "locked": False})
        self.assertEqual((self.state()["total"], len(self.log())), (1, 1))

    def test_a_repeated_lock_report_is_recorded_once(self):
        strike_id = self.new_id()
        self.lockout(3, strike_id=strike_id)
        self.assertEqual(self.lockout(3, strike_id=strike_id).status_code, 200)
        self.assertEqual((self.state()["total"], len(self.log())), (1, 1))

    def test_a_lock_report_for_a_strike_the_server_already_locked_on_counts_once(self):
        self.strike()
        self.strike()
        last = self.new_id()
        self.strike(last)                                                      # the server locks here
        self.lockout(3, strike_id=last)                                        # the app's own report of it
        self.assertEqual(self.state()["total"], 3)
        self.assertEqual(sum("LOCKED" in line for line in self.log()), 1)

    def test_a_lost_strike_report_still_ends_in_a_lock(self):
        self.strike()
        # strike 2's report never arrived; the app then reports strike 3 - and its lockout.
        last = self.new_id()
        self.assertFalse(self.strike(last).json()["locked"])                   # the server only has 2
        self.lockout(3, strike_id=last)
        row = self.row()
        self.assertEqual((row.isTheftLocked, self.state()["total"]), (1, 2))

    def test_a_late_strike_after_the_lock_still_counts_and_stays_locked(self):
        self.strike(reason=SIDE_LOOK)
        late = self.new_id()
        self.lockout(3, SIDE_LOOK, strike_id=self.new_id())
        self.assertTrue(self.strike(late, reason=NO_FACE).json()["counted"])   # delayed on the network
        row = self.row()
        self.assertEqual((row.isTheftLocked, row.theftAttemptsLeft, self.state()["total"]), (1, 0, 3))

    def test_every_write_holds_the_trainees_row(self):
        self.open_module("STANDARD_TEST")
        calls = {
            "strike": lambda: self.strike(),
            "lockout": lambda: self.lockout(3),
            "unlock": lambda: self.unlock(),
            "submit": lambda: self.as_trainee(PRESENT, "POST", "/assessments/SUITE-1/submit",
                                              json={"conferenceUid": S_N1, "answers": self.answers("a", "b", "c")}),
        }
        for name, call in calls.items():
            with self.subTest(name), patch.object(
                attendance_repository, "get_for_conference_and_trainee", wraps=attendance_repository.get_for_conference_and_trainee
            ) as spy:
                call()
                self.assertTrue(any(c.kwargs.get("lock") for c in spy.call_args_list))


class UnlockKeepsTheHistory(ProctoringStrikesTestCase):
    def test_an_unlock_adds_three_and_keeps_every_count_and_line(self):
        self.lock_with_three_strikes()
        lines_before = self.log()
        self.assertEqual(self.unlock().status_code, 200)
        row = self.row()
        self.assertEqual((row.isTheftLocked, row.theftAttemptsLeft), (0, 3))
        self.assertEqual((self.state()["reasons"], self.state()["total"]), ({SIDE_LOOK: 2, NO_FACE: 1}, 3))
        self.assertEqual(self.log()[1:], lines_before)                         # every earlier line kept
        self.assertIn(" -> UNLOCK: Camera glare, not cheating", self.log()[0])
        # The next round starts over: its first strike counts and doesn't lock.
        self.assertEqual(self.strike(reason=NO_FACE).json(), {"counted": True, "attemptsLeft": 2, "locked": False})
        self.assertEqual((self.state()["total"], self.state()["reasons"][NO_FACE]), (4, 2))

    def test_a_strike_from_before_the_unlock_resent_after_it_still_counts_once(self):
        early = self.new_id()
        self.strike(early)
        self.strike()
        self.lockout(3, strike_id=self.new_id())
        self.unlock()
        self.assertFalse(self.strike(early).json()["counted"])
        self.assertEqual(self.state()["total"], 3)

    def test_an_unlock_adds_to_what_was_left_instead_of_resetting(self):
        self.set_row(isTheftLocked=1, theftAttemptsLeft=1)
        self.assertEqual(self.unlock().status_code, 200)
        self.assertEqual(self.row().theftAttemptsLeft, 4)

    def test_the_unlock_count_is_stored_and_only_two_are_allowed(self):
        for used in (1, 2):
            self.lock_with_three_strikes()
            self.assertEqual(self.unlock().status_code, 200)
            self.assertEqual(self.state()["unlocks"], used)
        self.lock_with_three_strikes()
        self.assertEqual(self.unlock().status_code, 409)
        self.assertEqual(self.row().isTheftLocked, 1)

    def test_an_older_row_still_counts_its_unlock_lines(self):
        legacy = "[2026-10-06 10:05:00] trainer1 -> UNLOCK: first\n[2026-10-06 10:00:00] LOCKED strike #3: NO_FACE"
        self.set_row(isTheftLocked=1, theftAttemptsLeft=0, theftRemarks=legacy)
        self.assertEqual(self.unlock().status_code, 200)                     # 2nd unlock
        self.assertEqual(self.state()["unlocks"], 2)
        self.set_row(isTheftLocked=1)
        self.assertEqual(self.unlock().status_code, 409)                     # a 3rd is refused


class OlderAppVersions(ProctoringStrikesTestCase):
    def test_an_app_that_only_reports_the_lockout_still_works(self):
        # Older builds send no strikes, only the final lock - no ID, their own reason text.
        response = self.lockout(3, reason="face_missing")
        self.assertEqual(response.json(), {"locked": True})
        row = self.row()
        self.assertEqual((row.isTheftLocked, row.theftAttemptsLeft), (1, 0))
        self.assertEqual(self.state()["reasons"], {"face_missing": 1})
        self.assertEqual(self.lockout(3, reason="face_missing").status_code, 200)  # its retry
        self.assertEqual((self.state()["total"], len(self.log())), (1, 1))
        self.assertEqual(self.unlock().status_code, 200)
        self.assertEqual(self.row().isTheftLocked, 0)
        self.lockout(3, reason="face_missing")                                 # locked again after the unlock
        self.assertEqual((self.row().isTheftLocked, self.state()["total"]), (1, 2))


class WhoMayReport(ProctoringStrikesTestCase):
    def test_only_a_present_trainee_on_that_training_with_a_known_reason_and_a_valid_id(self):
        self.assertEqual(self.strike(trainee=ROSTERED).status_code, 403)       # on the list, not Present
        self.assertEqual(self.strike(trainee=ELSEWHERE).status_code, 404)
        self.assertEqual(self.strike(trainee=NOWHERE).status_code, 404)
        self.assertEqual(self.strike(reason="LOOKED AT THE CEILING").status_code, 422)
        self.assertEqual(self.strike("bad id!").status_code, 422)
        self.assertIsNone(self.row().securityDetails)

    def test_anything_else_in_security_details_is_kept(self):
        self.set_row(securityDetails=json.dumps({"device": "SM-A546E"}))
        self.strike()
        self.assertEqual(json.loads(self.row().securityDetails)["device"], "SM-A546E")

    def test_old_plain_text_in_security_details_is_kept_as_notes(self):
        self.set_row(securityDetails="legacy note")
        self.strike()
        self.assertEqual(json.loads(self.row().securityDetails)["notes"], "legacy note")
