"""Live Quiz - one answer per question (review finding, 2026-10-19).

The first thing recorded for a question stands. An accepted answer's response already names the
correct option, and the blank row a reported timeout leaves unlocks the reveal - so a later answer
must never replace either. The app locks the options after the first tap (src/hooks/useLiveQuiz.ts);
this is the same rule on the server, for anyone sending the request themselves. A repeat changes
nothing and is answered with what is recorded.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture."""

from app.services import answer_numbers
from tests.test_live_quiz_pause import LiveQuizPauseTestCase
from tests.test_phase4_operations import PRESENT, S_N1

WRONG, RIGHT = "b", "a"  # the first question's options are a / b / c, and "a" is correct


class TheFirstAnswerStands(LiveQuizPauseTestCase):
    def setUp(self):
        super().setUp()
        self.broadcast()

    def stored_option_id(self):
        return answer_numbers.option_id(self.question, self.stored_answer().selectedOption)

    def test_a_second_answer_cannot_replace_a_wrong_first_one(self):
        first = self.answer(WRONG)
        self.assertEqual((first["accepted"], first["correct"], first["correctOptionId"]), (True, False, RIGHT))
        second = self.answer(RIGHT)  # the correct option, read off the first response
        self.assertEqual(second, first)
        self.assertEqual(self.stored_option_id(), WRONG)

    def test_the_first_answers_response_time_is_kept(self):
        self.wait(2_000)
        self.answer(WRONG)
        self.wait(3_000)
        self.answer(RIGHT)
        self.assertEqual(self.stored_answer().remarks, "2000")

    def test_repeating_the_same_answer_gets_the_same_result(self):
        first = self.answer(RIGHT)
        self.assertEqual((first["accepted"], first["correct"]), (True, True))
        self.assertEqual(self.answer(RIGHT), first)
        self.assertEqual(self.stored_option_id(), RIGHT)

    def test_an_answer_after_a_reported_timeout_cannot_replace_the_blank(self):
        # Reported while the question is still live: the blank row unlocks the reveal, so the
        # correct option is known - answering it now must not count.
        timeout = self.as_trainee(PRESENT, "POST", "/sessions/live-quiz/timeout",
                                  json={"conferenceUid": S_N1, "questionId": self.question.id})
        self.assertEqual(timeout.status_code, 200, timeout.text)
        self.assertEqual(self.reveal_status(), 200)
        late = self.answer(RIGHT)
        self.assertEqual((late["accepted"], late["paused"], late["correctOptionId"]), (False, False, None))
        self.assertIsNone(self.stored_answer().selectedOption)
