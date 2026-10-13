"""assessment_results.ipAddress / deviceInfo: the device that submitted the result.

A trainee's own submission (Standard Test, Survey, Live Quiz Final Submit) records the caller's IP
(the address our proxy appended - utils.helpers.client_ip) and user agent, trimmed to the columns'
45 / 255 characters. A Live Quiz result the trainer's Finish scored for a trainee who never
pressed Final Submit keeps the device of the trainee's own first answer - never the trainer's."""

import json
import time

from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from tests.test_phase4_operations import PRESENT, S_N1, Phase4TestCase

PHONE = "Mozilla/5.0 (Linux; Android 14; SM-A546E) TOPS/1.0"
TRAINEE_IP = "203.0.113.7"


class ResultDeviceTestCase(Phase4TestCase):
    def from_phone(self, method, path, user_agent=PHONE, **kwargs):
        headers = {**self.trainee_headers(PRESENT), "User-Agent": user_agent, "X-Forwarded-For": TRAINEE_IP}
        return self.w.client.request(method, path, headers=headers, **kwargs)

    def result(self, suite="SUITE-1"):
        self.alpha.expire_all()
        return self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=PRESENT, assessmentSuiteUid=suite).one()


class StandardTestSubmission(ResultDeviceTestCase):
    def submit(self, user_agent=PHONE):
        body = {"conferenceUid": S_N1, "answers": self.answers("a", "b", "c")}
        return self.from_phone("POST", "/assessments/SUITE-1/submit", user_agent=user_agent, json=body)

    def test_the_submitting_device_is_recorded(self):
        self.open_module()
        self.assertEqual(self.submit().status_code, 200)
        result = self.result()
        self.assertEqual((result.ipAddress, result.deviceInfo), (TRAINEE_IP, PHONE))

    def test_a_long_user_agent_is_trimmed_to_the_column(self):
        self.open_module()
        self.assertEqual(self.submit(user_agent="x" * 400).status_code, 200)
        self.assertEqual(self.result().deviceInfo, "x" * 255)


class LiveQuizSubmission(ResultDeviceTestCase):
    def setUp(self):
        super().setUp()
        question = self.questions[0]
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({
            "conferenceStatus": "Ongoing", "activeModuleId": "LIVE_QUIZ",
            "sessionConfig": json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-1"}}),
            "liveQuizState": "QUESTION_LIVE", "liveQuestionId": str(question.id),
            "liveTimerEndsAt": int(time.time() * 1000) + 60_000, "liveTimerRemainingMs": None,
        })
        self.alpha.commit()
        answer = {"conferenceUid": S_N1, "questionId": question.id, "selectedOption": "a"}
        self.assertEqual(self.from_phone("POST", "/sessions/live-quiz/answer", json=answer).status_code, 200)

    def test_final_submit_records_the_trainees_device(self):
        self.assertEqual(self.from_phone("POST", f"/sessions/live-quiz/submit?conferenceUid={S_N1}").status_code, 200)
        result = self.result()
        self.assertEqual((result.ipAddress, result.deviceInfo), (TRAINEE_IP, PHONE))

    def test_a_result_scored_by_the_trainers_finish_keeps_the_trainees_device(self):
        response = self.w.client.post(
            f"/admin/trainings/{S_N1}/live-quiz/finish",
            headers={**self.w.headers("trainer1"), "User-Agent": "trainer-tablet", "X-Forwarded-For": "198.51.100.9"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        result = self.result()
        self.assertEqual(result.status, "Submitted")
        # The device of the trainee's own answer (recorded with their start) - never the trainer's.
        self.assertEqual((result.ipAddress, result.deviceInfo), (TRAINEE_IP, PHONE))
