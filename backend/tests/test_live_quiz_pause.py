"""Live Quiz - the trainer's Stop Timer pauses the question for the trainees too.

Approved rule (2026-10-01): while stopped, the trainee's clock is frozen AND answers are locked
until the trainer presses Play; time spent stopped never counts against anyone.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture. The
server clock is replaced with a controllable one so the tests never wait in real time.
"""

import json
from unittest.mock import patch

from app.core.constants import LIVE_QUIZ_DEFAULT_TIMER_SECONDS
from app.models.conference import Conference
from app.repositories import assessment_repository
from tests.test_phase4_operations import PRESENT, S_N1, Phase4TestCase

DURATION_MS = LIVE_QUIZ_DEFAULT_TIMER_SECONDS * 1000


class LiveQuizPauseTestCase(Phase4TestCase):
    def setUp(self):
        super().setUp()
        self.now_ms = 1_800_000_000_000
        clock = patch("app.services.live_quiz_service._now_ms", side_effect=lambda: self.now_ms)
        clock.start()
        self.addCleanup(clock.stop)
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({
            "conferenceStatus": "Ongoing",
            "activeModuleId": "LIVE_QUIZ",
            "sessionConfig": json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-1"}}),
        })
        self.alpha.commit()
        self.question = self.questions[0]

    def wait(self, ms):
        self.now_ms += ms

    def trainer(self, action, json=None):
        response = self.post("trainer1", f"/admin/trainings/{S_N1}/live-quiz/{action}", json=json)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def broadcast(self):
        self.trainer("broadcast", {"questionId": self.question.id})

    def trainee_view(self):
        response = self.as_trainee(PRESENT, "GET", f"/sessions/live-quiz?conferenceUid={S_N1}")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def answer(self, option="a"):
        body = {"conferenceUid": S_N1, "questionId": self.question.id, "selectedOption": option}
        response = self.as_trainee(PRESENT, "POST", "/sessions/live-quiz/answer", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def reveal_status(self):
        path = f"/sessions/live-quiz/reveal?conferenceUid={S_N1}&questionId={self.question.id}"
        return self.as_trainee(PRESENT, "GET", path).status_code

    def stored_answer(self):
        self.alpha.expire_all()
        return assessment_repository.get_answer(self.alpha, S_N1, PRESENT, self.question.id)


class TheTraineeClockFollowsTheTrainer(LiveQuizPauseTestCase):
    def test_a_running_question_counts_down_normally(self):
        self.broadcast()
        view = self.trainee_view()
        self.assertEqual(view["timerEndsAt"], self.now_ms + DURATION_MS)
        self.assertIsNone(view["timerRemainingMs"])

    def test_stop_freezes_the_trainee_clock_even_past_the_original_deadline(self):
        self.broadcast()
        self.wait(5_000)
        self.trainer("stop-timer")
        self.wait(DURATION_MS * 3)  # well past when the question would have ended
        view = self.trainee_view()
        self.assertEqual(view["state"], "QUESTION_LIVE")
        self.assertIsNone(view["timerEndsAt"])
        self.assertEqual(view["timerRemainingMs"], DURATION_MS - 5_000)

    def test_play_resumes_from_where_it_stopped(self):
        self.broadcast()
        self.wait(5_000)
        self.trainer("stop-timer")
        self.wait(60_000)
        self.trainer("stop-timer")  # the same button is Play while stopped
        view = self.trainee_view()
        self.assertEqual(view["timerEndsAt"], self.now_ms + DURATION_MS - 5_000)
        self.assertIsNone(view["timerRemainingMs"])


class AnswersAreLockedWhileStopped(LiveQuizPauseTestCase):
    def test_an_answer_while_stopped_is_refused_as_paused_and_not_saved(self):
        self.broadcast()
        self.trainer("stop-timer")
        result = self.answer()
        self.assertEqual((result["accepted"], result["paused"]), (False, True))
        self.assertIsNone(self.stored_answer())

    def test_it_stays_paused_not_timed_out_after_the_original_deadline(self):
        self.broadcast()
        self.trainer("stop-timer")
        self.wait(DURATION_MS * 3)
        result = self.answer()
        self.assertEqual((result["accepted"], result["paused"]), (False, True))

    def test_answers_are_accepted_again_after_play(self):
        self.broadcast()
        self.trainer("stop-timer")
        self.wait(DURATION_MS * 3)
        self.trainer("stop-timer")
        result = self.answer("a")
        self.assertEqual((result["accepted"], result["paused"], result["correct"]), (True, False, True))
        self.assertEqual(self.stored_answer().selectedOption, "a")

    def test_the_answer_cannot_be_peeked_while_stopped(self):
        self.broadcast()
        self.trainer("stop-timer")
        self.wait(DURATION_MS * 3)  # used to unlock the reveal: the stale deadline had passed
        self.assertEqual(self.reveal_status(), 409)

    def test_time_spent_stopped_does_not_count_toward_answer_speed(self):
        self.broadcast()
        self.wait(4_000)
        self.trainer("stop-timer")
        self.wait(60_000)
        self.trainer("stop-timer")
        self.wait(1_000)
        self.answer()
        self.assertEqual(self.stored_answer().remarks, "5000")  # 4 s + 1 s; the minute stopped is excluded


class AClockStoppedWithNoTimeLeftIsTimeUp(LiveQuizPauseTestCase):
    def test_stopping_after_the_deadline_does_not_reopen_the_question(self):
        self.broadcast()
        self.wait(DURATION_MS + 1_000)
        self.trainer("stop-timer")
        result = self.answer()
        self.assertEqual((result["accepted"], result["paused"]), (False, False))  # a plain time-up
        self.assertIsNone(self.stored_answer())
        self.assertEqual(self.reveal_status(), 200)


class StopAndPlayDoWhatTheButtonSays(LiveQuizPauseTestCase):
    """The app sends the button pressed, so a press from a stale screen - or a second trainer/admin
    pressing the same button - can't flip the clock the other way."""

    def test_stop_on_a_stopped_clock_keeps_it_stopped(self):
        self.broadcast()
        self.wait(5_000)
        self.trainer("stop-timer", {"paused": True})
        self.wait(10_000)
        self.trainer("stop-timer", {"paused": True})
        view = self.trainee_view()
        self.assertIsNone(view["timerEndsAt"])
        self.assertEqual(view["timerRemainingMs"], DURATION_MS - 5_000)

    def test_play_on_a_running_clock_leaves_it_running(self):
        self.broadcast()
        ends_at = self.now_ms + DURATION_MS
        self.wait(5_000)
        self.trainer("stop-timer", {"paused": False})
        view = self.trainee_view()
        self.assertEqual(view["timerEndsAt"], ends_at)
        self.assertIsNone(view["timerRemainingMs"])

    def test_play_resumes_a_stopped_clock_from_where_it_stopped(self):
        self.broadcast()
        self.wait(5_000)
        self.trainer("stop-timer", {"paused": True})
        self.wait(60_000)
        self.trainer("stop-timer", {"paused": False})
        view = self.trainee_view()
        self.assertEqual(view["timerEndsAt"], self.now_ms + DURATION_MS - 5_000)
        self.assertIsNone(view["timerRemainingMs"])


class TheTrainerCardFollowsTheClock(LiveQuizPauseTestCase):
    def test_the_trainer_sees_the_same_frozen_time_as_the_trainees(self):
        self.broadcast()
        self.wait(5_000)
        studio = self.trainer("stop-timer", {"paused": True})["liveStudio"]
        self.assertEqual(studio["timerRemainingMs"], DURATION_MS - 5_000)
        self.assertEqual(studio["timerRemainingMs"], self.trainee_view()["timerRemainingMs"])
        studio = self.trainer("stop-timer", {"paused": False})["liveStudio"]
        self.assertIsNone(studio["timerRemainingMs"])

    def test_a_quiz_finished_while_stopped_is_not_left_paused(self):
        self.broadcast()
        self.wait(5_000)
        self.trainer("stop-timer", {"paused": True})
        studio = self.trainer("finish")["liveStudio"]
        self.assertEqual(studio["state"], "FINISHED")
        self.assertIsNone(studio["timerRemainingMs"])
        self.wait(DURATION_MS)  # past the question's original deadline
        self.assertEqual(self.reveal_status(), 200)
