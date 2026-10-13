"""Session Dashboard participant rows carry their Post Test score and whether it passes - the same
pass mark (PASS_THRESHOLD_PERCENT) the dashboard's own pass / fail counts use - so the app shows a
green or red score without a pass mark of its own."""

from app.core.constants import PASS_THRESHOLD_PERCENT
from app.models.attendance import Attendance
from app.models.quiz import AssessmentResult
from tests.tenant_fixtures import uid
from tests.test_trainer_authorization import TrainerWorldTestCase


class ParticipantRowsCarryTheirScore(TrainerWorldTestCase):
    def rows(self):
        response = self.get("trainer1", f"/admin/trainings/{uid('S_N1')}")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        return {row["traineeUid"]: row for row in body["trainees"]}, body["assessment"]

    def set_percentage(self, percentage):
        self.alpha.query(AssessmentResult).filter(AssessmentResult.resultUid == "RES-S_N1").update({"percentage": percentage})
        self.alpha.commit()

    def test_a_score_at_or_above_the_pass_mark_passes_and_below_it_fails(self):
        for percentage, passed in ((100, True), (PASS_THRESHOLD_PERCENT, True), (PASS_THRESHOLD_PERCENT - 0.5, False), (0, False)):
            with self.subTest(percentage=percentage):
                self.set_percentage(percentage)
                row = self.rows()[0]["TR-S_N1-0"]
                self.assertEqual(row["score"], f"{float(percentage):g}%")
                self.assertIs(row["scorePassed"], passed)

    def test_the_rows_and_the_pass_fail_counts_agree(self):
        self.set_percentage(PASS_THRESHOLD_PERCENT - 10)
        rows, assessment = self.rows()
        passed = sum(1 for row in rows.values() if row["scorePassed"] is True)
        failed = sum(1 for row in rows.values() if row["scorePassed"] is False)
        self.assertEqual((passed, failed), (assessment["pass"], assessment["fail"]))

    def test_no_score_yet_means_neither_pass_nor_fail(self):
        self.alpha.query(Attendance).filter(Attendance.attendanceUid == "ATT-S_N1-1").update({"status": "Present"})
        self.alpha.commit()
        row = self.rows()[0]["TR-S_N1-1"]  # present, no test submitted
        self.assertIsNone(row["score"])
        self.assertIsNone(row["scorePassed"])
