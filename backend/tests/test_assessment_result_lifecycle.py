"""assessment_results: started -> submitted, and Surveys never scored.

Standard Test / Survey: opening the questions writes one "Started" row (startedAt, attempt number,
opening device); the submit completes that same row (scores, submittedAt, durationSeconds,
submitting device) instead of adding another. Live Quiz: the first answer (or timeout) writes it,
started when that question went live. A Survey's row records only that it was submitted: 0 / 0,
and it never counts toward a score, pass / fail, average or the trainee's Recent Sessions."""

import json
import time
from datetime import datetime
from unittest.mock import patch

from app.models.conference import Conference
from app.models.quiz import AssessmentResult, Question
from app.utils.date_utils import utc_from_epoch_ms
from tests.test_phase4_operations import PRESENT, S_N1, Phase4TestCase

OPENED = datetime(2026, 10, 12, 4, 30, 0)
SUBMITTED = datetime(2026, 10, 12, 4, 45, 30)


class ResultLifecycleTestCase(Phase4TestCase):
    def setUp(self):
        super().setUp()
        settings_patch = patch("app.services.session_service.get_proctoring_settings", return_value=(True, 3))
        settings_patch.start()
        self.addCleanup(settings_patch.stop)

    def at(self, moment):
        return patch("app.services.assessment_service.utc_now", return_value=moment)

    def open_questions(self, suite="SUITE-1"):
        return self.as_trainee(PRESENT, "GET", f"/assessments/{suite}/questions?conferenceUid={S_N1}")

    def submit(self, answers, suite="SUITE-1"):
        return self.as_trainee(PRESENT, "POST", f"/assessments/{suite}/submit", json={"conferenceUid": S_N1, "answers": answers})

    def rows(self, suite="SUITE-1"):
        self.alpha.expire_all()
        return self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=PRESENT, assessmentSuiteUid=suite).all()


class StartedThenSubmitted(ResultLifecycleTestCase):
    def test_opening_the_questions_records_the_start_once(self):
        self.open_module()
        with self.at(OPENED):
            self.assertEqual(self.open_questions().status_code, 200)
        with self.at(SUBMITTED):
            self.assertEqual(self.open_questions().status_code, 200)   # an app restart reopens it
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt, row.submittedAt), ("Started", OPENED, None))
        self.assertEqual(row.deviceInfo, "testclient")

    def test_the_submit_completes_the_same_row_with_the_real_duration(self):
        self.open_module()
        with self.at(OPENED):
            self.open_questions()
        started_attempt = self.rows()[0].attemptNumber
        with self.at(SUBMITTED):
            response = self.submit(self.answers("a", "b", "x"))
        self.assertEqual(response.status_code, 200, response.text)
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt, row.submittedAt), ("Completed", OPENED, SUBMITTED))
        self.assertEqual(row.durationSeconds, 15 * 60 + 30)
        self.assertEqual((float(row.totalScore), float(row.maxScore), row.attemptNumber), (2, 3, started_attempt))

    def test_an_opened_test_is_not_a_result_yet(self):
        self.open_module()
        self.open_questions()
        modules = {m["key"]: m for m in self.as_trainee(PRESENT, "GET", f"/sessions/current?conference_uid={S_N1}").json()["modules"]}
        self.assertFalse(modules["STANDARD_TEST"]["isCompleted"])
        self.assertIsNone(modules["STANDARD_TEST"]["score"])
        self.assertEqual(self.as_trainee(PRESENT, "GET", "/sessions/history").json()[0]["score"], None)

    def test_opening_a_submitted_test_again_adds_nothing(self):
        self.open_module()
        self.open_questions()
        self.submit(self.answers("a", "b", "c"))
        self.open_questions()
        self.assertEqual([row.status for row in self.rows()], ["Completed"])

    def test_a_submit_with_no_recorded_start_leaves_the_start_unknown(self):
        self.open_module()
        with self.at(SUBMITTED):
            self.assertEqual(self.submit(self.answers("a", "b", "c")).status_code, 200)
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt, row.submittedAt, row.durationSeconds), ("Completed", None, SUBMITTED, 0))


class LiveQuizStartedThenSubmitted(ResultLifecycleTestCase):
    """A Live Quiz begins for a trainee when the first question they answer (or time out on) went
    live; their Final Submit or the trainer's Finish completes that same row."""

    def setUp(self):
        super().setUp()
        self.first_live_ms = int(time.time() * 1000) - 5_000

    def go_live(self, question, went_live_ms):
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({
            "conferenceStatus": "Ongoing", "activeModuleId": "LIVE_QUIZ",
            "sessionConfig": json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-1"}}),
            "liveQuizState": "QUESTION_LIVE", "liveQuestionId": str(question.id),
            # The fixture's questions have no timer of their own: the 30 s default.
            "liveTimerEndsAt": went_live_ms + 30_000, "liveTimerRemainingMs": None,
        })
        self.alpha.commit()

    def answer(self, question, option="a"):
        body = {"conferenceUid": S_N1, "questionId": question.id, "selectedOption": option}
        return self.as_trainee(PRESENT, "POST", "/sessions/live-quiz/answer", json=body)

    def answer_two_questions(self):
        self.go_live(self.questions[0], self.first_live_ms)
        self.assertTrue(self.answer(self.questions[0]).json()["accepted"])
        self.go_live(self.questions[1], self.first_live_ms + 20_000)
        self.assertTrue(self.answer(self.questions[1]).json()["accepted"])

    def test_the_first_answer_records_when_its_question_went_live(self):
        self.answer_two_questions()
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt, row.submittedAt), ("Started", utc_from_epoch_ms(self.first_live_ms), None))

    def test_a_timeout_first_records_the_start_too(self):
        self.go_live(self.questions[0], self.first_live_ms)
        body = {"conferenceUid": S_N1, "questionId": self.questions[0].id}
        self.assertEqual(self.as_trainee(PRESENT, "POST", "/sessions/live-quiz/timeout", json=body).status_code, 200)
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt), ("Started", utc_from_epoch_ms(self.first_live_ms)))

    def test_final_submit_completes_the_same_row(self):
        self.answer_two_questions()
        self.assertEqual(self.as_trainee(PRESENT, "POST", f"/sessions/live-quiz/submit?conferenceUid={S_N1}").status_code, 200)
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt), ("Completed", utc_from_epoch_ms(self.first_live_ms)))
        self.assertIsNotNone(row.submittedAt)
        self.assertEqual((float(row.totalScore), float(row.maxScore)), (1, 3))   # q0 "a" right, q1 "a" wrong

    def test_the_trainers_finish_completes_the_same_row(self):
        self.answer_two_questions()
        response = self.w.client.post(f"/admin/trainings/{S_N1}/live-quiz/finish", headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        [row] = self.rows()
        self.assertEqual((row.status, row.startedAt), ("Completed", utc_from_epoch_ms(self.first_live_ms)))


class SurveysAreNeverScored(ResultLifecycleTestCase):
    def setUp(self):
        super().setUp()
        self.survey_questions = []
        for n in range(2):
            # Built the way the question builder saves them by default: 1 point, no right answer.
            q = Question(assessmentSuiteUid="SURVEY-1", question=f"S{n}", options=json.dumps([{"id": o, "text": o} for o in "xy"]),
                         correct_answer=None, points=1, sort_order=n)
            self.alpha.add(q)
            self.survey_questions.append(q)
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"surveyUid": "SURVEY-1"})
        self.alpha.commit()

    def take_test_then_survey(self):
        self.open_module()
        self.submit(self.answers("a", "b", "c"))                                      # 3 / 3 = 100%
        self.open_module("SURVEY")
        self.open_questions("SURVEY-1")
        answers = [{"questionId": q.id, "selectedOption": "x"} for q in self.survey_questions]
        return self.submit(answers, suite="SURVEY-1")

    def test_a_survey_is_stored_and_answered_with_no_score(self):
        response = self.take_test_then_survey()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            {key: response.json()[key] for key in ("totalScore", "maxScore", "percentage", "correctCount")},
            {"totalScore": 0, "maxScore": 0, "percentage": 0, "correctCount": 0},
        )
        [row] = self.rows("SURVEY-1")
        self.assertEqual((row.status, float(row.maxScore)), ("Completed", 0))

    def test_the_survey_card_and_detail_show_no_score(self):
        self.take_test_then_survey()
        modules = {m["key"]: m for m in self.as_trainee(PRESENT, "GET", f"/sessions/current?conference_uid={S_N1}").json()["modules"]}
        self.assertTrue(modules["SURVEY"]["isCompleted"])
        self.assertIsNone(modules["SURVEY"]["score"])
        self.assertEqual(modules["STANDARD_TEST"]["score"], "3/3")
        detail = {m["key"]: m for m in self.as_trainee(PRESENT, "GET", f"/sessions/{S_N1}/detail").json()["modules"]}
        self.assertIsNone(detail["SURVEY"]["score"])

    def test_recent_sessions_show_the_test_not_the_later_survey(self):
        self.take_test_then_survey()
        [item] = [i for i in self.as_trainee(PRESENT, "GET", "/sessions/history").json() if i["conferenceUid"] == S_N1]
        self.assertEqual((item["score"], item["passed"]), ("100%", True))

    def test_the_admin_dashboard_counts_the_test_but_not_the_survey(self):
        def attempts():
            return self.w.client.get("/admin/dashboard/stats", headers=self.w.headers("super")).json()["assessment"]

        before = attempts()
        self.take_test_then_survey()
        after = attempts()
        self.assertEqual(after["attempts"] - before["attempts"], 1)
        self.assertEqual(after["passCount"] - before["passCount"], 1)
        self.assertEqual(after["failCount"], before["failCount"])
