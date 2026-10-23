"""Retest of a missed session (user, 2026-10-22): a trainee who missed a session that ran - on its
roster, never marked Present or Absent - may retake its Standard Test and Survey, once each, with no
deadline. The retest is saved apart (status Retest): the session stays Missed for them, it isn't
counted as attended and its score is in no ranking.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture: on
CONF-S_N1, TR-S_N1-0 is Present and TR-S_N1-1 only on the roster (Pending)."""

import json

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult, Question
from app.repositories import assessment_repository
from tests.test_phase4_operations import ELSEWHERE, PRESENT, ROSTERED, S_N1, Phase4TestCase

MISSED = ROSTERED


class RetestTestCase(Phase4TestCase):
    def setUp(self):
        super().setUp()
        self.alpha.add(Question(assessmentSuiteUid="SURVEY-1", question="How was it?", points=0, sort_order=0,
                                options=json.dumps([{"id": o, "text": o} for o in ("good", "bad")])))
        self.set_session(conferenceStatus="Completed", activeModuleId=None, surveyUid="SURVEY-1")

    def set_session(self, **columns):
        self.alpha.query(Conference).filter_by(conferenceUid=S_N1).update(columns)
        self.alpha.commit()

    def open_retest(self, trainee=MISSED, suite="SUITE-1"):
        return self.as_trainee(trainee, "GET", f"/assessments/{suite}/questions?conferenceUid={S_N1}&retest=true")

    def submit_retest(self, trainee=MISSED, suite="SUITE-1", answers=None):
        body = {"conferenceUid": S_N1, "answers": self.answers("a", "b", "x") if answers is None else answers, "retest": True}
        return self.as_trainee(trainee, "POST", f"/assessments/{suite}/submit", json=body)

    def detail(self, trainee=MISSED):
        response = self.as_trainee(trainee, "GET", f"/sessions/{S_N1}/detail")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def stored(self, suite="SUITE-1"):
        self.alpha.expire_all()
        return self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=MISSED, assessmentSuiteUid=suite).all()


class AMissedTraineeRetakesTheTestAndSurvey(RetestTestCase):
    def test_the_missed_session_offers_its_test_and_survey(self):
        detail = self.detail()
        self.assertEqual(detail["status"], "Missed")
        self.assertEqual(
            [(m["key"], m["suiteUid"], m["done"], m["score"]) for m in detail["retest"]],
            [("STANDARD_TEST", "SUITE-1", False, None), ("SURVEY", "SURVEY-1", False, None)],
        )

    def test_the_retest_is_saved_apart_and_the_session_stays_missed(self):
        self.assertEqual(self.open_retest().status_code, 200)
        response = self.submit_retest()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()["totalScore"], response.json()["maxScore"]), (2, 3))

        [result] = self.stored()
        self.assertEqual(result.status, "Retest")
        self.assertIsNotNone(result.startedAt)   # opening the questions started it, as for any test
        detail = self.detail()
        self.assertEqual(detail["status"], "Missed")
        self.assertEqual((detail["retest"][0]["done"], detail["retest"][0]["score"]), (True, "2/3"))
        self.alpha.expire_all()
        attendance = self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=MISSED).one()
        self.assertEqual(attendance.status, "Pending")   # not attended,
        self.assertIsNone(attendance.checkOutTime)       # nor checked out

    def test_the_survey_is_retaken_too_and_never_scored(self):
        self.assertEqual(self.open_retest(suite="SURVEY-1").status_code, 200)
        survey_question = self.alpha.query(Question).filter_by(assessmentSuiteUid="SURVEY-1").one()
        response = self.submit_retest(suite="SURVEY-1", answers=[{"questionId": survey_question.id, "selectedOption": "good"}])
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.detail()["retest"][1], {
            "key": "SURVEY", "name": "Survey Module", "suiteUid": "SURVEY-1", "done": True, "score": None,
        })

    def test_once_per_test(self):
        first = self.submit_retest().json()
        again = self.submit_retest(answers=self.answers("a", "b", "c"))   # a repeat keeps the first
        self.assertEqual((again.status_code, again.json()), (200, first))
        self.assertEqual(len(self.stored()), 1)
        self.assertEqual(self.open_retest().status_code, 409)


class TheRetestCountsNowhere(RetestTestCase):
    def test_no_finished_result_reader_sees_it(self):
        self.submit_retest()
        self.assertEqual(assessment_repository.list_results_for_conference_suite(self.alpha, S_N1, "SUITE-1"), [])
        self.assertEqual(assessment_repository.list_results_for_trainee(self.alpha, MISSED), [])
        self.assertIsNone(assessment_repository.get_latest_result(self.alpha, S_N1, MISSED, "SUITE-1"))
        self.assertFalse(assessment_repository.has_submitted_result(self.alpha, S_N1, MISSED))


class OnlyAMissedSessionThatRanCanBeRetaken(RetestTestCase):
    def test_not_for_a_trainee_who_completed_the_module_or_was_marked_absent(self):
        # Already completed in the session: cannot retake
        self.alpha.add(AssessmentResult(conferenceUid=S_N1, traineeUid=PRESENT, assessmentSuiteUid="SUITE-1", status="Completed"))
        self.alpha.commit()
        self.assertEqual(self.open_retest(trainee=PRESENT).status_code, 409)
        self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=MISSED).update({"status": "Absent"})
        self.alpha.commit()
        self.assertEqual(self.open_retest().status_code, 409)
        self.assertEqual(self.submit_retest().status_code, 409)
        self.assertEqual(self.detail()["retest"], [])

    def test_an_attended_trainee_who_missed_a_module_can_retest_it(self):
        # PRESENT attended (status="Present") but didn't submit SUITE-1 in the session: they can retest it
        self.assertEqual(self.open_retest(trainee=PRESENT).status_code, 200)
        detail = self.detail(trainee=PRESENT)
        # Standard Test Module is Missed with canRetest=True
        std_mod = next(m for m in detail["modules"] if m["key"] == "STANDARD_TEST")
        self.assertEqual(std_mod["status"], "Missed")
        self.assertTrue(std_mod["canRetest"])

    def test_not_while_the_session_runs_nor_for_one_cancelled_or_never_run(self):
        for status in ("Ongoing", "Cancelled", "Scheduled"):
            with self.subTest(status=status):
                self.set_session(conferenceStatus=status, conferenceDate="2000-01-01")   # a past date: "missed"
                self.assertEqual(self.open_retest().status_code, 409)
                self.assertEqual(self.detail()["retest"], [])

    def test_not_another_sessions_trainee_nor_another_question_set(self):
        self.assertEqual(self.open_retest(trainee=ELSEWHERE).status_code, 404)
        self.assertEqual(self.open_retest(suite="SUITE-OTHER").status_code, 404)

    def test_a_plain_submission_after_the_session_is_still_refused(self):
        body = {"conferenceUid": S_N1, "answers": self.answers("a", "b", "c")}
        self.assertEqual(self.as_trainee(MISSED, "POST", "/assessments/SUITE-1/submit", json=body).status_code, 403)
        self.assertEqual(self.stored(), [])
