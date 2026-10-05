"""Phase 4 - trainee/trainer detail endpoints, attendance, assessments, mutations.

Synthetic TenantWorld (in-memory SQLite) only. In the fixture, CONF-S_N1 (trainer1) has TR-S_N1-0
marked Present and TR-S_N1-1 on the roster as Pending; every fixture training's post-test is
SUITE-1. TR-S_S1-0 is on trainer2's CONF-S_S1 only; TR-OTHER-TRAINER is on no roster at all.
"""

import json
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.dialects import mysql

from app.core.security import create_access_token
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.models.quiz import AssessmentResult, Question
from app.models.trainee import Trainee
from app.repositories import conference_repository
from tests.tenant_fixtures import ALPHA, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

S_N1 = uid("S_N1")
PRESENT, ROSTERED, ELSEWHERE, NOWHERE = "TR-S_N1-0", "TR-S_N1-1", "TR-S_S1-0", "TR-OTHER-TRAINER"


class Phase4TestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        self.questions = []
        for n, correct in enumerate(("a", "b", "c")):
            q = Question(assessmentSuiteUid="SUITE-1", question=f"Q{n}", options=json.dumps([{"id": o, "text": o} for o in "abc"]),
                         correct_answer=correct, points=1, sort_order=n)
            self.alpha.add(q)
            self.questions.append(q)
        other = Question(assessmentSuiteUid="SUITE-OTHER", question="Elsewhere", options="[]", correct_answer="a", points=5)
        self.alpha.add(other)
        # The fixture's Present trainee has already submitted SUITE-1; start before that submission.
        self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=PRESENT).delete()
        self.alpha.commit()
        self.other_question = other

    def trainee_headers(self, trainee_uid):
        phone = self.alpha.query(Trainee).filter(Trainee.traineeUid == trainee_uid).one().phone
        return {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=ALPHA, role='trainee')}"}

    def as_trainee(self, trainee_uid, method, path, **kwargs):
        return self.w.client.request(method, path, headers=self.trainee_headers(trainee_uid), **kwargs)

    def open_module(self, module="STANDARD_TEST", conference=S_N1):
        self.alpha.query(Conference).filter(Conference.conferenceUid == conference).update(
            {"conferenceStatus": "Ongoing", "activeModuleId": module}
        )
        self.alpha.commit()

    def results(self, trainee_uid=PRESENT):
        return self.alpha.query(AssessmentResult).filter_by(conferenceUid=S_N1, traineeUid=trainee_uid, assessmentSuiteUid="SUITE-1").count()

    def answers(self, *picks):
        return [{"questionId": q.id, "selectedOption": pick} for q, pick in zip(self.questions, picks)]


class AssessmentQuestionsAndSubmission(Phase4TestCase):
    def questions_status(self, trainee_uid, suite="SUITE-1", conference=S_N1):
        return self.as_trainee(trainee_uid, "GET", f"/assessments/{suite}/questions?conferenceUid={conference}").status_code

    def submit(self, trainee_uid=PRESENT, answers=None, suite="SUITE-1", conference=S_N1):
        body = {"conferenceUid": conference, "answers": answers if answers is not None else self.answers("a", "b", "x")}
        return self.as_trainee(trainee_uid, "POST", f"/assessments/{suite}/submit", json=body)

    def test_questions_only_for_an_open_module_of_the_trainees_own_session(self):
        self.assertEqual(self.questions_status(PRESENT), 409)                  # module not open yet
        self.open_module()
        self.assertEqual(self.questions_status(PRESENT), 200)
        self.assertEqual(self.questions_status(ROSTERED), 403)                 # on the roster, not Present
        self.assertEqual(self.questions_status(ELSEWHERE), 404)                # another session's trainee
        self.assertEqual(self.questions_status(NOWHERE), 404)
        self.assertEqual(self.questions_status(PRESENT, suite="SUITE-OTHER"), 404)  # not this session's test
        self.assertEqual(self.as_trainee(PRESENT, "GET", "/assessments/SUITE-1/questions").status_code, 422)

    def test_the_questions_never_carry_the_answers(self):
        self.open_module()
        body = self.as_trainee(PRESENT, "GET", f"/assessments/SUITE-1/questions?conferenceUid={S_N1}").json()
        self.assertNotIn("correct_answer", json.dumps(body))

    def test_a_valid_submission_is_scored_once(self):
        self.open_module()
        response = self.submit()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual((response.json()["totalScore"], response.json()["maxScore"], response.json()["correctCount"]), (2, 3, 2))
        self.assertEqual(self.results(), 1)

    def test_a_repeat_returns_the_stored_result_and_saves_nothing(self):
        self.open_module()
        first = self.submit().json()
        again = self.submit(answers=self.answers("a", "b", "c"))  # a "better" retry is still the same submission
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json(), first)
        self.assertEqual(self.results(), 1)

    def test_a_question_answered_twice_or_from_another_test_is_refused(self):
        self.open_module()
        q = self.questions[0]
        doubled = [{"questionId": q.id, "selectedOption": "a"}, {"questionId": q.id, "selectedOption": "a"}]
        self.assertEqual(self.submit(answers=doubled).status_code, 400)       # used to score the points twice
        foreign = [{"questionId": self.other_question.id, "selectedOption": "a"}]
        self.assertEqual(self.submit(answers=foreign).status_code, 400)
        self.assertEqual(self.results(), 0)

    def test_submissions_outside_the_rules_write_nothing(self):
        self.assertEqual(self.submit().status_code, 409)                       # module not open
        self.open_module("SURVEY")
        self.assertEqual(self.submit().status_code, 409)                       # another module is open
        self.open_module()
        self.assertEqual(self.submit(ROSTERED).status_code, 403)
        self.assertEqual(self.submit(ELSEWHERE).status_code, 404)
        self.assertEqual(self.submit(suite="SUITE-OTHER").status_code, 404)   # a test from another session
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"conferenceStatus": "Completed"})
        self.alpha.commit()
        self.assertEqual(self.submit().status_code, 409)                       # session over
        self.assertEqual(self.alpha.query(AssessmentResult).filter_by(assessmentSuiteUid="SUITE-1", conferenceUid=S_N1).count(), 0)

    def test_the_submission_locks_the_trainees_attendance_row(self):
        from app.repositories import attendance_repository

        with patch.object(attendance_repository, "get_for_conference_and_trainee", wraps=attendance_repository.get_for_conference_and_trainee) as spy:
            self.open_module()
            self.submit()
        self.assertTrue(any(call.kwargs.get("lock") for call in spy.call_args_list))
        query = self.alpha.query(Attendance).filter(Attendance.conferenceUid == S_N1).with_for_update()
        self.assertIn("FOR UPDATE", str(query.statement.compile(dialect=mysql.dialect())))

    def test_the_unused_leaderboard_is_gone(self):
        self.assertEqual(self.as_trainee(PRESENT, "GET", "/assessments/SUITE-1/leaderboard").status_code, 404)


class LiveQuizIsForTheSessionsPresentTrainees(Phase4TestCase):
    ENDPOINTS = [
        ("GET", "/sessions/live-quiz?conferenceUid={c}", None),
        ("GET", "/sessions/live-quiz/summary?conferenceUid={c}", None),
        ("GET", "/sessions/live-quiz/results?conferenceUid={c}", None),
        ("GET", "/sessions/live-quiz/reveal?conferenceUid={c}&questionId=1", None),
        ("POST", "/sessions/live-quiz/submit?conferenceUid={c}", None),
        ("POST", "/sessions/live-quiz/answer", {"conferenceUid": "{c}", "questionId": 1, "selectedOption": "a"}),
        ("POST", "/sessions/live-quiz/timeout", {"conferenceUid": "{c}", "questionId": 1}),
    ]

    def call(self, trainee_uid, method, path, body):
        if body:
            body = {k: (v.format(c=S_N1) if isinstance(v, str) else v) for k, v in body.items()}
        return self.as_trainee(trainee_uid, method, path.format(c=S_N1), json=body)

    def test_anyone_not_on_the_roster_gets_404_and_not_present_gets_403(self):
        for method, path, body in self.ENDPOINTS:
            with self.subTest(path=path):
                self.assertEqual(self.call(ELSEWHERE, method, path, body).status_code, 404)
                self.assertEqual(self.call(NOWHERE, method, path, body).status_code, 404)
                self.assertEqual(self.call(ROSTERED, method, path, body).status_code, 403)

    def test_a_present_trainee_reaches_the_view(self):
        self.assertEqual(self.call(PRESENT, "GET", "/sessions/live-quiz?conferenceUid={c}", None).status_code, 200)


class TraineeDetailsAndSessionIds(Phase4TestCase):
    def setUp(self):
        super().setUp()
        # proctoring_settings_service binds CommonSessionLocal at import, outside TenantWorld's patch.
        settings_patch = patch("app.services.session_service.get_proctoring_settings", return_value=(True, 3))
        settings_patch.start()
        self.addCleanup(settings_patch.stop)

    def test_training_detail_only_for_the_trainees_own_sessions(self):
        self.assertEqual(self.as_trainee(PRESENT, "GET", f"/sessions/{S_N1}/detail").status_code, 200)
        self.assertEqual(self.as_trainee(ROSTERED, "GET", f"/sessions/{S_N1}/detail").status_code, 200)
        self.assertEqual(self.as_trainee(ELSEWHERE, "GET", f"/sessions/{S_N1}/detail").status_code, 404)
        self.assertEqual(self.as_trainee(PRESENT, "GET", "/sessions/CONF-NOPE/detail").status_code, 404)

    def test_a_requested_session_is_honoured_only_for_its_trainees(self):
        mine = self.as_trainee(ELSEWHERE, "GET", f"/sessions/current?conference_uid={uid('S_S1')}")
        self.assertEqual(mine.json().get("conferenceUid"), uid("S_S1"))
        probe = self.as_trainee(ELSEWHERE, "GET", f"/sessions/current?conference_uid={S_N1}")
        self.assertNotEqual(probe.json().get("conferenceUid") if probe.status_code == 200 else None, S_N1)

    def test_a_proctoring_report_never_puts_a_trainee_on_a_roster(self):
        body = {"conferenceUid": S_N1, "violationType": "face_missing", "strikeNumber": 3}
        self.assertEqual(self.as_trainee(NOWHERE, "POST", "/sessions/proctoring-lock", json=body).status_code, 404)
        self.assertIsNone(self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=NOWHERE).first())
        self.assertEqual(self.as_trainee(PRESENT, "POST", "/sessions/proctoring-lock", json=body).status_code, 200)


class CheckInFollowsTheSession(Phase4TestCase):
    def check_in(self, trainee_uid, conference=S_N1):
        return self.as_trainee(trainee_uid, "POST", "/attendance/check-in", json={"conferenceUid": conference})

    def test_check_in_only_while_the_attendance_module_is_open(self):
        self.assertEqual(self.check_in(ROSTERED).status_code, 409)                 # session not running
        self.open_module("STANDARD_TEST")
        self.assertEqual(self.check_in(ROSTERED).status_code, 409)                 # another module is open
        self.assertEqual(self.check_in(ROSTERED, "CONF-NOPE").status_code, 404)
        self.open_module("ATTENDANCE")
        self.assertEqual(self.check_in(ROSTERED).status_code, 200)
        row = self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=ROSTERED).one()
        self.assertEqual(row.status, "Present")

    def test_repeated_check_ins_keep_one_row(self):
        self.open_module("ATTENDANCE")
        for _ in range(3):
            self.assertEqual(self.check_in(NOWHERE).status_code, 200)
        self.assertEqual(self.alpha.query(Attendance).filter_by(conferenceUid=S_N1, traineeUid=NOWHERE).count(), 1)

    def test_check_in_takes_the_per_session_lock(self):
        with patch.object(conference_repository, "lock_for_roster_change", wraps=conference_repository.lock_for_roster_change) as spy:
            self.open_module("ATTENDANCE")
            self.check_in(ROSTERED)
        spy.assert_called_once()
        statement = select(Conference).where(Conference.conferenceUid == S_N1).with_for_update()
        self.assertIn("FOR UPDATE", str(statement.compile(dialect=mysql.dialect())))


class TrainerStateChangesAreAtomic(Phase4TestCase):
    def post(self, path):
        return self.w.client.post(path, headers=self.w.headers("trainer1"))

    def modules_logged(self, action):
        return self.alpha.query(ConferenceActivityLog).filter_by(conferenceUid=S_N1, action=action).count()

    def test_only_one_of_two_racing_claims_wins(self):
        self.assertTrue(conference_repository.claim_active_module(self.alpha, S_N1, None, "ATTENDANCE"))
        self.assertFalse(conference_repository.claim_active_module(self.alpha, S_N1, None, "STANDARD_TEST"))
        self.assertTrue(conference_repository.claim_active_module(self.alpha, S_N1, "ATTENDANCE", None))
        self.assertTrue(conference_repository.claim_end(self.alpha, S_N1, "2026-10-01 10:00:00"))
        self.assertFalse(conference_repository.claim_end(self.alpha, S_N1, "2026-10-01 10:05:00"))
        self.alpha.rollback()

    def test_a_losing_advance_changes_and_logs_nothing(self):
        self.open_module("ATTENDANCE")
        with patch.object(conference_repository, "claim_active_module", return_value=False):
            self.assertEqual(self.post(f"/admin/trainings/{S_N1}/advance-module").status_code, 409)
            self.assertEqual(self.post(f"/admin/trainings/{S_N1}/modules/stop-active").status_code, 409)
        self.assertEqual(self.modules_logged("STOPPED"), 0)
        self.alpha.expire_all()
        self.assertEqual(self.alpha.query(Conference).filter_by(conferenceUid=S_N1).one().activeModuleId, "ATTENDANCE")

    def test_a_losing_end_writes_nothing(self):
        self.open_module(None)
        files = {"photo": ("p.jpg", b"img", "image/jpeg"), "attendanceSheet": ("s.pdf", b"%PDF", "application/pdf")}
        with patch.object(conference_repository, "claim_end", return_value=False):
            response = self.w.client.post(f"/admin/trainings/{S_N1}/end", data={"totalPax": "2"}, files=files,
                                          headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 409)
        self.alpha.expire_all()
        row = self.alpha.query(Conference).filter_by(conferenceUid=S_N1).one()
        self.assertEqual((row.conferenceStatus, row.conferenceEndsOn), ("Ongoing", None))


class NoMassAssignment(Phase4TestCase):
    def test_profile_patch_cannot_set_file_paths_or_the_username(self):
        agent = self.w.agency["trainer1"]
        self.alpha.query(AgencyTeam).filter(AgencyTeam.id == agent.id).update({"profilePhoto": "trainer_photos/agency_1.png"})
        self.alpha.commit()
        body = {"name": "Renamed", "profilePicture": "trainer_documents/aadhar/agency_2.pdf", "username": "trainer9",
                "aadharFile": "trainer_documents/aadhar/agency_2.pdf"}
        response = self.w.client.patch("/admin/profile", json=body, headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        self.alpha.expire_all()
        row = self.alpha.query(AgencyTeam).filter(AgencyTeam.id == agent.id).one()
        self.assertEqual((row.name, row.username, row.profilePhoto), ("Renamed", "trainer1", "trainer_photos/agency_1.png"))

    def test_an_admin_account_cannot_repoint_its_aadhaar_either(self):
        admin = self.w.admins["adm_trainer"]
        response = self.w.client.patch("/admin/profile", json={"aadharFile": "trainer_documents/aadhar/agency_1.pdf"},
                                       headers=self.w.headers("adm_trainer"))
        self.assertEqual(response.status_code, 200)
        self.w.common.expire_all()
        self.assertIsNone(self.w.common.get(Admin, admin.id).aadharImage)

    def test_trainee_registration_ignores_a_supplied_photo_path(self):
        body = {"traineeUid": "TR-MA", "fullName": "New Person", "designation": "Promoter", "gender": "Male",
                "primaryEmail": "ma@example.com", "primaryPhone": "9123456700", "state": "Delhi", "zone": "North Zone",
                "region": "North 1", "company": "Samsung India", "requestedBy": "Quess", "trainerId": "trainer1",
                "trainerName": "Trainer One", "supervisorId": "s", "supervisorName": "S", "jobStatus": "Active",
                "username": "masspath", "password": "Correct-Horse-9", "profilePhoto": "trainee_photos/TR-S_S1-0.jpg"}
        self.assertEqual(self.w.client.post("/admin/trainees", json=body, headers=self.w.headers("trainer1")).status_code, 201)
        self.assertIsNone(self.alpha.query(Trainee).filter_by(traineeUid="TR-MA").one().profilePhoto)


class StatusRules(Phase4TestCase):
    def set_conference_status(self, status):
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"conferenceStatus": status})
        self.alpha.commit()

    def end(self):
        files = {"photo": ("p.jpg", b"img", "image/jpeg"), "attendanceSheet": ("s.pdf", b"%PDF", "application/pdf")}
        return self.w.client.post(f"/admin/trainings/{S_N1}/end", data={"totalPax": "2"}, files=files,
                                  headers=self.w.headers("trainer1"))

    def test_a_session_that_was_never_started_cannot_be_ended(self):
        response = self.end()                                                  # fixture session is Scheduled
        self.assertEqual(response.status_code, 409)
        self.assertIn("hasn't been started", response.json()["detail"])
        self.alpha.expire_all()
        row = self.alpha.query(Conference).filter_by(conferenceUid=S_N1).one()
        self.assertEqual((row.conferenceStatus, row.conferenceEndsOn), ("Scheduled", None))

    def patch_training(self, body):
        return self.w.client.patch(f"/admin/trainings/{S_N1}", json=body, headers=self.w.headers("super"))

    def test_a_completed_training_status_is_final(self):
        self.set_conference_status("Completed")
        for status in ("Scheduled", "Ongoing", "Cancelled"):
            with self.subTest(status=status):
                self.assertEqual(self.patch_training({"trainingStatus": status}).status_code, 409)
        self.alpha.expire_all()
        self.assertEqual(self.alpha.query(Conference).filter_by(conferenceUid=S_N1).one().conferenceStatus, "Completed")

    def test_finished_or_cancelled_trainings_cannot_be_approved_or_rejected(self):
        for status in ("Completed", "Cancelled"):
            self.set_conference_status(status)
            for action in ("approve", "reject"):
                with self.subTest(status=status, action=action):
                    response = self.w.client.post(f"/admin/trainings/{S_N1}/{action}", json={"reason": "r"},
                                                  headers=self.w.headers("super"))
                    self.assertEqual(response.status_code, 409, response.text)
            with self.subTest(status=status, action="patch"):
                self.assertEqual(self.patch_training({"approvalStatus": "Rejected", "message": "m"}).status_code, 409)

    def test_a_scheduled_training_can_still_be_approved(self):
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"status": "Pending"})
        self.alpha.commit()
        response = self.w.client.post(f"/admin/trainings/{S_N1}/approve", json={"reason": "ok"}, headers=self.w.headers("super"))
        self.assertEqual(response.status_code, 200, response.text)

    def test_other_status_edits_still_work(self):
        response = self.w.client.patch(f"/admin/trainings/{S_N1}", json={"trainingStatus": "Cancelled"},
                                       headers=self.w.headers("super"))
        self.assertEqual(response.status_code, 200, response.text)


class HrFieldsAreAdminManaged(Phase4TestCase):
    def test_a_trainer_cannot_change_their_own_hr_fields(self):
        admin = self.w.admins["adm_trainer"]
        self.w.common.query(Admin).filter(Admin.id == admin.id).update({"salary": "30000", "jobStatus": "Active", "designation": "Trainer"})
        self.w.common.commit()
        body = {"name": "Still Editable", "salary": "99999", "jobStatus": "Manager", "designation": "Head", "joinedOn": "2020-01-01"}
        response = self.w.client.patch("/admin/profile", json=body, headers=self.w.headers("adm_trainer"))
        self.assertEqual(response.status_code, 200, response.text)
        self.w.common.expire_all()
        row = self.w.common.get(Admin, admin.id)
        self.assertEqual((row.name, row.salary, row.jobStatus, row.designation), ("Still Editable", "30000", "Active", "Trainer"))

    def test_an_agency_trainer_cannot_change_their_designation(self):
        agent = self.w.agency["trainer1"]
        before = agent.designation
        self.w.client.patch("/admin/profile", json={"designation": "Head"}, headers=self.w.headers("trainer1"))
        self.alpha.expire_all()
        self.assertEqual(self.alpha.query(AgencyTeam).filter(AgencyTeam.id == agent.id).one().designation, before)


class NewTraineePhotoUpload(Phase4TestCase):
    JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64

    def setUp(self):
        super().setUp()
        import tempfile
        from pathlib import Path

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for target in ("app.routers.media.MEDIA_ROOT", "app.core.media.MEDIA_ROOT"):
            p = patch(target, self.root)
            p.start()
            self.addCleanup(p.stop)

    def upload(self, who, trainee_uid=ROSTERED, content=JPEG, content_type="image/jpeg"):
        return self.w.client.post(f"/admin/trainees/{trainee_uid}/photo", files={"file": ("p.jpg", content, content_type)},
                                  headers=self.w.headers(who))

    def photo_of(self, trainee_uid):
        self.alpha.expire_all()
        return self.alpha.query(Trainee).filter_by(traineeUid=trainee_uid).one().profilePhoto

    def test_the_trainees_trainer_uploads_it_and_the_trainee_sees_it(self):
        response = self.upload("trainer1")
        self.assertEqual(response.status_code, 200, response.text)
        path = self.photo_of(ROSTERED)
        self.assertEqual(path, f"trainee_photos/{ROSTERED}.jpg")
        self.assertEqual(response.json()["profilePhoto"], path)
        self.assertEqual((self.root / ALPHA / path).read_bytes(), self.JPEG)
        self.assertEqual(self.as_trainee(ROSTERED, "GET", f"/media/{path}").status_code, 200)   # shown after login
        self.assertEqual(self.as_trainee(ELSEWHERE, "GET", f"/media/{path}").status_code, 404)  # not to other trainees

    def test_another_trainers_trainee_is_not_found(self):
        self.assertEqual(self.upload("trainer2").status_code, 404)
        self.assertEqual(self.upload("trainer1", trainee_uid="TR-NOPE").status_code, 404)
        self.assertIsNone(self.photo_of(ROSTERED))
        self.assertFalse((self.root / ALPHA / "trainee_photos").exists() and any((self.root / ALPHA / "trainee_photos").iterdir()))

    def test_only_images_are_accepted(self):
        self.assertEqual(self.upload("trainer1", content=b"%PDF-1.4", content_type="application/pdf").status_code, 400)
        self.assertIsNone(self.photo_of(ROSTERED))

    def test_a_trainee_cannot_use_it(self):
        response = self.as_trainee(ROSTERED, "POST", f"/admin/trainees/{ROSTERED}/photo",
                                   files={"file": ("p.jpg", self.JPEG, "image/jpeg")})
        self.assertIn(response.status_code, (401, 403))


class RunningMeansOngoingOrLiveInAnyCase(Phase4TestCase):
    """The guards use the session screen's own rule (session_service.session_is_running)."""

    def set_status(self, status, module):
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update(
            {"conferenceStatus": status, "activeModuleId": module})
        self.alpha.commit()

    def test_questions_and_check_in_open_for_every_spelling_of_running(self):
        for status in ("Ongoing", "ongoing", "Live", "LIVE"):
            with self.subTest(status=status):
                self.set_status(status, "STANDARD_TEST")
                self.assertEqual(self.as_trainee(PRESENT, "GET", f"/assessments/SUITE-1/questions?conferenceUid={S_N1}").status_code, 200)
                self.set_status(status, "ATTENDANCE")
                self.assertEqual(self.as_trainee(ROSTERED, "POST", "/attendance/check-in", json={"conferenceUid": S_N1}).status_code, 200)

    def test_a_finished_session_stays_closed(self):
        for status in ("Completed", "completed", "Cancelled", "Scheduled"):
            with self.subTest(status=status):
                self.set_status(status, "STANDARD_TEST")
                self.assertEqual(self.as_trainee(PRESENT, "GET", f"/assessments/SUITE-1/questions?conferenceUid={S_N1}").status_code, 409)
