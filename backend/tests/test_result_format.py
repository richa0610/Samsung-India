"""Results and answers saved in the other system's format (user, 2026-10-16):

- a finished result says "Completed" (one saved "Submitted" before still counts as finished);
- answersSnapshot lists every question of the set - {"<id>": {"answer", "is_correct", "points"}} -
  with the answer as saved ("" when unanswered); a Survey's entries are false / 0, a Live Quiz's also
  carry "responseMs", which the leaderboard's tie-break adds up;
- result and answer IDs are SUB (a test or survey) or LIVE (the Live Quiz) + the IST date + a count.

Synthetic TenantWorld (in-memory SQLite) only - see test_phase4_operations for the fixture, whose
SUITE-1 questions have options a, b, c with answer keys a, b, c (1 point each).
"""

import json
import re
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine

from app.database.connection import TenantBase
from app.models.conference import Conference
from app.models.quiz import Assessment, AssessmentResult, Question
from app.services.live_quiz_service import _result_response_ms
from app.utils.uid import next_daily_uid
from tests.test_assessment_result_lifecycle import ResultLifecycleTestCase
from tests.test_live_quiz_pause import LiveQuizPauseTestCase
from tests.test_phase4_operations import PRESENT, S_N1

TODAY = datetime(2026, 10, 16, 10, 0)


def frozen_day(test: unittest.TestCase) -> None:
    clock = patch("app.utils.uid.ist_now", return_value=TODAY)
    clock.start()
    test.addCleanup(clock.stop)


class AStandardTestResult(ResultLifecycleTestCase):
    def setUp(self):
        super().setUp()
        frozen_day(self)

    def submitted(self):
        self.open_module()
        response = self.submit(self.answers("a", "c"))                       # right, wrong, third unanswered
        self.assertEqual(response.status_code, 200, response.text)
        [row] = self.rows()
        return row

    def test_is_completed_with_every_question_in_its_answer_details(self):
        row = self.submitted()
        q = [str(question.id) for question in self.questions]
        self.assertEqual(row.status, "Completed")
        self.assertEqual(json.loads(row.answersSnapshot), {
            q[0]: {"answer": "1", "is_correct": True, "points": 1},
            q[1]: {"answer": "3", "is_correct": False, "points": 0},
            q[2]: {"answer": "", "is_correct": False, "points": 0},
        })

    def test_it_and_its_answers_get_sub_ids_of_the_day(self):
        row = self.submitted()
        answer_ids = [a.assessmentUid for a in self.alpha.query(Assessment).filter_by(conferenceUid=S_N1, traineeUid=PRESENT)]
        for uid in [row.resultUid, *answer_ids]:
            self.assertRegex(uid, r"^SUB261016\d{4}$")
        self.assertEqual(len({row.resultUid, *answer_ids}), 3)                # never two alike


class ASurveyResult(ResultLifecycleTestCase):
    def test_lists_its_answers_unscored(self):
        survey = Question(assessmentSuiteUid="SURVEY-1", question="S0", options=json.dumps([{"id": "very_good", "text": "Very good"}]),
                          correct_answer=None, points=1, sort_order=0)
        self.alpha.add(survey)
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"surveyUid": "SURVEY-1"})
        self.alpha.commit()
        self.open_module("SURVEY")
        self.open_questions("SURVEY-1")
        self.submit([{"questionId": survey.id, "selectedOption": "very_good"}], suite="SURVEY-1")
        [row] = self.rows("SURVEY-1")
        # Saved as option position since 2026-10-17 (user)
        self.assertEqual(json.loads(row.answersSnapshot), {str(survey.id): {"answer": "1", "is_correct": False, "points": 0}})


class ALiveQuizResult(LiveQuizPauseTestCase):
    def setUp(self):
        super().setUp()
        frozen_day(self)

    def test_answer_details_carry_the_answer_time_the_leaderboard_adds_up(self):
        self.question = self.questions[1]                                          # answer key "b"
        self.broadcast()
        self.wait(1_500)
        self.answer("b")
        self.trainer("finish")
        self.alpha.expire_all()
        result = self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=PRESENT, assessmentSuiteUid="SUITE-1").one()
        self.assertEqual(result.status, "Completed")
        details = json.loads(result.answersSnapshot)
        self.assertEqual(details[str(self.question.id)], {"answer": "2", "is_correct": True, "points": 1, "responseMs": 1_500})
        self.assertEqual(details[str(self.questions[0].id)], {"answer": "", "is_correct": False, "points": 0})
        board = self.as_trainee(PRESENT, "GET", f"/sessions/live-quiz/results?conferenceUid={S_N1}").json()
        self.assertEqual(board["you"]["totalResponseMs"], 1_500)

    def test_its_answers_and_result_get_live_ids(self):
        self.broadcast()
        self.answer("a")
        self.trainer("finish")
        self.alpha.expire_all()
        self.assertRegex(self.stored_answer().assessmentUid, r"^LIVE261016\d{4}$")
        result = self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=PRESENT, assessmentSuiteUid="SUITE-1").one()
        self.assertRegex(result.resultUid, r"^LIVE261016\d{4}$")


class ResultsScoredBeforeTheNewFormat(unittest.TestCase):
    def test_a_live_quiz_total_saved_the_old_way_still_breaks_ties(self):
        self.assertEqual(_result_response_ms(SimpleNamespace(answersSnapshot='{"totalResponseMs": 4000}')), 4000)
        self.assertEqual(_result_response_ms(SimpleNamespace(answersSnapshot=None)), 0)


class DailyIds(unittest.TestCase):
    def test_count_up_per_kind_and_start_over_each_day(self):
        engine = create_engine("sqlite://")
        TenantBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        days = iter([TODAY, TODAY, TODAY, datetime(2026, 10, 17, 9, 0)])
        with patch("app.utils.uid.ist_now", side_effect=lambda: next(days)), engine.begin() as connection:
            made = [next_daily_uid(connection, kind) for kind in ("SUB", "SUB", "LIVE", "SUB")]
        self.assertEqual(made, ["SUB2610160001", "SUB2610160002", "LIVE2610160001", "SUB2610170001"])
        self.assertTrue(all(re.fullmatch(r"(SUB|LIVE)\d{10}", uid) for uid in made))
