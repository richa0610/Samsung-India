"""A trainer may lift one trainee's proctoring lockout at most MAX_PROCTORING_UNLOCKS (2) times in a
training. The server refuses the next unlock (the trainee stays locked), and every participant row
carries how many unlocks were used, of how many, for the app to show."""

from app.core.constants import MAX_PROCTORING_UNLOCKS
from app.models.attendance import Attendance
from tests.tenant_fixtures import uid
from tests.test_trainer_authorization import TrainerWorldTestCase

TRAINEE = "TR-S_N1-0"
UNLOCK = f"/admin/trainings/{uid('S_N1')}/attendance/{TRAINEE}/unlock"


class ProctoringUnlockLimit(TrainerWorldTestCase):
    def attendance(self):
        self.alpha.expire_all()
        return self.alpha.query(Attendance).filter(Attendance.attendanceUid == "ATT-S_N1-0").one()

    def lock(self, strike=3):
        # What the trainee's app reports when proctoring strikes out (session_service.report_proctoring_lock).
        row = self.attendance()
        row.isTheftLocked = 1
        row.theftAttemptsLeft = 0
        line = f"[2026-10-06 10:00:00] LOCKED strike #{strike}: NO_FACE"
        row.theftRemarks = f"{line}\n{row.theftRemarks}" if row.theftRemarks else line
        self.alpha.commit()

    def unlock(self, reason="Camera glitch"):
        return self.post("trainer1", UNLOCK, {"reason": reason})

    def my_row(self, body):
        return next(t for t in body["trainees"] if t["traineeUid"] == TRAINEE)

    def test_the_limit_is_two(self):
        self.assertEqual(MAX_PROCTORING_UNLOCKS, 2)

    def test_two_unlocks_then_the_next_is_refused_and_the_trainee_stays_locked(self):
        for used in range(1, MAX_PROCTORING_UNLOCKS + 1):
            self.lock()
            response = self.unlock()
            self.assertEqual(response.status_code, 200, response.text)
            row = self.my_row(response.json())
            self.assertFalse(row["isLocked"])
            self.assertEqual((row["proctoringUnlocks"], row["proctoringMaxUnlocks"]), (used, MAX_PROCTORING_UNLOCKS))

        self.lock()
        refused = self.unlock("One more time please")
        self.assertEqual(refused.status_code, 409, refused.text)
        self.assertIn("no more unlocks", refused.json()["detail"])
        attendance = self.attendance()
        self.assertEqual(attendance.isTheftLocked, 1)  # still locked
        self.assertNotIn("One more time please", attendance.theftRemarks)

        dashboard = self.get("trainer1", f"/admin/trainings/{uid('S_N1')}").json()
        row = self.my_row(dashboard)
        self.assertTrue(row["isLocked"])
        self.assertEqual((row["proctoringUnlocks"], row["proctoringMaxUnlocks"]), (2, 2))

    def test_lock_strikes_never_count_as_unlocks(self):
        for strike in (1, 2, 3):
            self.lock(strike)
        row = self.my_row(self.get("trainer1", f"/admin/trainings/{uid('S_N1')}").json())
        self.assertEqual(row["proctoringUnlocks"], 0)
        self.assertEqual(self.unlock().status_code, 200)
