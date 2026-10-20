"""Answers saved as option NUMBERS (services/answer_numbers.py, user 2026-10-16): a Standard Test or
Live Quiz answer, and a question's answer key, are stored as the option's position - 1 = the first
option shown. The app keeps sending and seeing option ids, scores don't change, an answer key saved as
a letter before numbering still works, and Survey answers keep their own value.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture, whose
SUITE-1 questions have options a, b, c with letter answer keys a, b, c.
"""

import json
import unittest
from types import SimpleNamespace

from app.models.conference import Conference
from app.models.quiz import Assessment, AssessmentSuite, Question
from app.services import answer_numbers
from tests.test_assessment_result_lifecycle import ResultLifecycleTestCase
from tests.test_live_quiz_pause import LiveQuizPauseTestCase
from tests.test_phase4_operations import PRESENT, S_N1, Phase4TestCase
from tests.test_training_detail_review import TrainingDetailReviewTestCase


def question(ids, correct=None):
    return SimpleNamespace(options=json.dumps([{"id": i, "text": f"Option {i}"} for i in ids]), correct_answer=correct)


class TheNumberingRule(unittest.TestCase):
    def test_an_option_id_is_saved_as_its_position_from_one(self):
        q = question("ABCD")
        self.assertEqual([answer_numbers.number_for(q, i) for i in "ABCD"], ["1", "2", "3", "4"])
        self.assertIsNone(answer_numbers.number_for(q, "Z"))       # not one of its options
        self.assertIsNone(answer_numbers.number_for(q, None))      # nothing picked

    def test_the_position_not_the_id_even_when_ids_are_numbers_out_of_order(self):
        q = question(["1", "3", "4"])                             # an option removed in the builder
        self.assertEqual(answer_numbers.number_for(q, "4"), "3")
        self.assertEqual(answer_numbers.option_id(q, "3"), "4")

    def test_a_saved_number_or_a_letter_saved_before_numbering_both_read_back(self):
        q = question("ABCD", correct="B")
        self.assertEqual((answer_numbers.option_id(q, "2"), answer_numbers.option_id(q, "B")), ("B", "B"))
        self.assertTrue(answer_numbers.is_correct(q, "2"))        # numbered answer, letter answer key
        self.assertTrue(answer_numbers.is_correct(q, "B"))        # letter answer saved before numbering
        q.correct_answer = "2"
        self.assertTrue(answer_numbers.is_correct(q, "2"))        # both numbered
        self.assertFalse(answer_numbers.is_correct(q, "1"))
        self.assertFalse(answer_numbers.is_correct(q, None))
        self.assertIsNone(answer_numbers.option_id(q, "5"))       # no fifth option

    def test_a_question_without_a_readable_option_list_keeps_values_as_written(self):
        q = SimpleNamespace(options="[]", correct_answer="a")
        self.assertEqual(answer_numbers.number_for(q, "a"), "a")
        self.assertTrue(answer_numbers.is_correct(q, "a"))


class StandardTestAnswers(TrainingDetailReviewTestCase):
    def saved(self):
        rows = self.alpha.query(Assessment).filter_by(conferenceUid=S_N1, traineeUid=PRESENT, assessmentSuiteUid="SUITE-1")
        by_question = {int(row.questionId): row.selectedOption for row in rows}
        return [by_question[q.id] for q in self.questions]

    def test_are_saved_as_numbers_and_scored_as_before(self):
        self.open_module("STANDARD_TEST")
        body = {"conferenceUid": S_N1, "answers": self.answers("a", "b", "x")}   # x is no option
        response = self.as_trainee(PRESENT, "POST", "/assessments/SUITE-1/submit", json=body)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()["correctCount"], response.json()["totalScore"]), (2, 2))
        self.assertEqual(self.saved(), ["1", "2", None])

    def test_the_review_shows_option_ids_not_numbers(self):
        self.open_module("STANDARD_TEST")
        self.submit_post_test()                                                    # a, b, x
        questions = self.module("STANDARD_TEST")["questions"]
        self.assertEqual([q["selectedOptionId"] for q in questions], ["a", "b", None])
        self.assertEqual([q["correctOptionId"] for q in questions], ["a", "b", "c"])
        self.assertEqual([q["isCorrect"] for q in questions], [True, True, False])


class LiveQuizAnswers(LiveQuizPauseTestCase):
    def test_are_saved_as_numbers_while_the_app_sees_option_ids(self):
        self.question = self.questions[1]                                          # options a, b, c - key "b"
        self.broadcast()
        result = self.answer("b")
        self.assertEqual((result["correct"], result["correctOptionId"]), (True, "b"))
        self.assertEqual(self.stored_answer().selectedOption, "2")
        path = f"/sessions/live-quiz/reveal?conferenceUid={S_N1}&questionId={self.question.id}"
        reveal = self.as_trainee(PRESENT, "GET", path).json()
        self.assertEqual((reveal["yourOptionId"], reveal["correctOptionId"]), ("b", "b"))

    def test_the_trainers_finish_scores_numbered_answers(self):
        self.question = self.questions[1]
        self.broadcast()
        self.answer("b")
        self.trainer("finish")
        summary = self.as_trainee(PRESENT, "GET", f"/sessions/live-quiz/results?conferenceUid={S_N1}").json()
        self.assertEqual((summary["you"]["score"], summary["correctCount"]), (1, 1))


class SurveyAnswersKeepTheirValue(ResultLifecycleTestCase):
    def test_a_survey_answer_is_saved_as_a_number_and_reads_as_the_option(self):
        survey = Question(assessmentSuiteUid="SURVEY-1", question="S0", options=json.dumps([{"id": "very_good", "text": "Very good"}]),
                          correct_answer=None, points=1, sort_order=0)
        self.alpha.add(survey)
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"surveyUid": "SURVEY-1"})
        self.alpha.commit()
        self.open_module("SURVEY")
        self.open_questions("SURVEY-1")
        response = self.submit([{"questionId": survey.id, "selectedOption": "very_good"}], suite="SURVEY-1")
        self.assertEqual(response.status_code, 200, response.text)
        row = self.alpha.query(Assessment).filter_by(assessmentSuiteUid="SURVEY-1", traineeUid=PRESENT).one()
        # Saved as option position since 2026-10-17 (user)
        self.assertEqual(row.selectedOption, "1")
        self.assertEqual(answer_numbers.option_id(survey, row.selectedOption), "very_good")


class TheQuestionBuilder(Phase4TestCase):
    def test_saves_the_answer_key_as_a_number_and_shows_it_as_the_option(self):
        self.alpha.add(AssessmentSuite(assessmentSuiteUid="SUITE-B", examTitle="Builder Test", status="Approved"))
        self.alpha.commit()
        body = {"question": "Which one?", "questionType": "multiple_choice", "points": 1, "correctAnswer": "B",
                "options": [{"id": "A", "text": "First"}, {"id": "B", "text": "Second"}]}
        response = self.w.client.post("/admin/assessment-suites/SUITE-B/questions", json=body, headers=self.w.headers("super"))
        self.assertEqual(response.status_code, 200, response.text)
        added = next(q for q in response.json()["questions"] if q["question"] == "Which one?")
        # Stored the other system's way: options are plain text whose ids are their positions ("1", "2")
        self.assertEqual(added["correctAnswer"], "2")
        self.alpha.expire_all()
        self.assertEqual(self.alpha.query(Question).filter_by(question="Which one?").one().correct_answer, '["2"]')
