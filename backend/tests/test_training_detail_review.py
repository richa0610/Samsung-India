"""Training Detail never shows a test's answers before the trainee has taken it.

Approved rule (2026-10-03): while a training is still on (upcoming or ongoing), a module's question
review - and its correct answers - appear only once the trainee has submitted that module; in the
Live Quiz, only the questions that reached them (answered or timed out). Once the training is over,
everything is reviewable as before.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture.
"""

import json

from app.models.conference import Conference
from app.models.quiz import Question
from app.repositories import assessment_repository
from tests.test_phase4_operations import PRESENT, S_N1, Phase4TestCase


class TrainingDetailReviewTestCase(Phase4TestCase):
    def set_conference(self, **fields):
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update(fields)
        self.alpha.commit()

    def module(self, key):
        response = self.as_trainee(PRESENT, "GET", f"/sessions/{S_N1}/detail")
        self.assertEqual(response.status_code, 200, response.text)
        return next(m for m in response.json()["modules"] if m["key"] == key)

    def reviewed_ids(self, key):
        return [q["id"] for q in self.module(key)["questions"]]

    def submit_post_test(self):
        body = {"conferenceUid": S_N1, "answers": self.answers("a", "b", "x")}
        response = self.as_trainee(PRESENT, "POST", "/assessments/SUITE-1/submit", json=body)
        self.assertEqual(response.status_code, 200, response.text)


class ThePostTestIsReviewableOnlyOnceSubmitted(TrainingDetailReviewTestCase):
    def test_an_upcoming_training_shows_no_questions_or_answers(self):
        self.set_conference(conferenceStatus="Scheduled", conferenceDate="2099-01-01")
        self.assertEqual(self.reviewed_ids("STANDARD_TEST"), [])

    def test_a_live_unsubmitted_post_test_shows_no_questions_or_answers(self):
        self.open_module("STANDARD_TEST")
        module = self.module("STANDARD_TEST")
        self.assertEqual(module["questions"], [])
        self.assertIsNone(module["score"])

    def test_once_submitted_it_is_reviewable_while_the_training_goes_on(self):
        self.open_module("STANDARD_TEST")
        self.submit_post_test()
        module = self.module("STANDARD_TEST")
        self.assertEqual((module["status"], module["score"]), ("Completed", "2/3"))
        self.assertEqual([q["correctOptionId"] for q in module["questions"]], ["a", "b", "c"])

    def test_after_the_training_ends_every_question_is_reviewable(self):
        self.set_conference(conferenceStatus="Completed")
        self.assertEqual(self.reviewed_ids("STANDARD_TEST"), [q.id for q in self.questions])


class TheLiveQuizShowsOnlyQuestionsThatReachedTheTrainee(TrainingDetailReviewTestCase):
    def setUp(self):
        super().setUp()
        self.quiz = [
            Question(assessmentSuiteUid="SUITE-LQ", question=f"LQ{n}", options=json.dumps([{"id": "a", "text": "a"}]),
                     correct_answer="a", points=1, sort_order=n)
            for n in range(3)
        ]
        self.alpha.add_all(self.quiz)
        self.alpha.commit()
        self.set_conference(sessionConfig=json.dumps({"liveQuiz": {"assessmentSuiteUid": "SUITE-LQ"}}))
        self.open_module("LIVE_QUIZ")
        for question, pick in ((self.quiz[0], "a"), (self.quiz[1], None)):   # answered; timed out
            assessment_repository.upsert_answer(
                self.alpha, conference_uid=S_N1, trainee_uid=PRESENT, suite_uid="SUITE-LQ",
                question_id=question.id, selected_option=pick,
            )
        self.alpha.commit()

    def test_while_the_training_goes_on_never_a_question_still_to_be_asked(self):
        self.assertEqual(self.reviewed_ids("LIVE_QUIZ"), [self.quiz[0].id, self.quiz[1].id])

    def test_after_the_training_ends_every_question_is_reviewable(self):
        self.set_conference(conferenceStatus="Completed")
        self.assertEqual(self.reviewed_ids("LIVE_QUIZ"), [q.id for q in self.quiz])
