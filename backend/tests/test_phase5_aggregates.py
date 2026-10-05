"""Phase 5 - dashboard statistics, reports, dropdowns and aggregates: authorization and queries.

Synthetic TenantWorld only (in-memory SQLite). In the fixture, trainer1 and trainer2 are Samsung
India trainers and trainer3 is Other Co; coadmin holds a Samsung India grant on ALPHA; BETA is a
separate tenant database.
"""

import json
import random
import unittest

from sqlalchemy import event

from app.models.admin_access import AdminAccess
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.models.trainee import Trainee
from app.repositories import attendance_repository, assessment_repository, dashboard_repository
from app.services import trainee_dashboard_service as dashboard
from tests import _legacy_trainee_dashboard as legacy
from tests.tenant_fixtures import ALPHA, BETA, TenantWorld, uid
from tests.test_trainer_authorization import TrainerWorldTestCase
from tests import _legacy_queries as legacy_queries


class Phase5TestCase(TrainerWorldTestCase):
    def get_json(self, who, path, tenant=ALPHA):
        response = self.w.client.get(path, headers=self.w.headers(who, tenant))
        self.assertEqual(response.status_code, 200, f"{who} {path}: {response.text}")
        return response.json()

    def update_conference(self, key, **values):
        self.alpha.query(Conference).filter(Conference.conferenceUid == uid(key)).update(values)
        self.alpha.commit()

    def count_statements(self, call):
        statements = []

        def on_execute(conn, cursor, statement, *args):
            statements.append(statement)

        event.listen(self.w.alpha_engine, "before_cursor_execute", on_execute)
        try:
            call()
        finally:
            event.remove(self.w.alpha_engine, "before_cursor_execute", on_execute)
        return len(statements)


# --------------------------------------------------------------------------- trainer Home summary
class TrainerSummaryIsTheTrainersOwn(Phase5TestCase):
    RANGE = "/admin/trainings/summary?start=2026-01-01&end=2026-12-31"

    def test_counts_only_the_trainers_trainings_and_trainees(self):
        # trainer1 owns S_N1, S_DEL, S_N1V; each has one Present trainee who also submitted.
        body = self.get_json("trainer1", self.RANGE)
        self.assertEqual((body["totalSessions"], body["totalTrainees"]), (3, 3))
        self.assertEqual(self.get_json("trainer3", self.RANGE)["totalSessions"], 1)   # O_N1 only

    def test_other_trainers_and_tenants_cannot_move_the_numbers(self):
        before = self.get_json("trainer1", self.RANGE)
        self.update_conference("S_S1", conferenceStatus="Completed", status="Approved")      # trainer2's
        self.update_conference("O_N1", conferenceStatus="Ongoing", status="Approved")        # trainer3's
        beta = self.w.tenant_db[BETA]
        beta.query(Conference).update({"conferenceStatus": "Completed", "trainerEmployeeId": "trainer1"})
        beta.commit()
        self.alpha.add(Attendance(attendanceUid="ATT-X", conferenceUid=uid("S_S1"), traineeUid="TR-S_N1-1", status="Present"))
        self.alpha.commit()
        self.assertEqual(self.get_json("trainer1", self.RANGE), before)

    def test_status_breakdown(self):
        self.update_conference("S_N1", conferenceStatus="Completed", status="Approved")
        self.update_conference("S_DEL", conferenceStatus="Ongoing", status="Approved")
        self.update_conference("S_N1V", conferenceStatus="Scheduled", status="Approved", conferenceDate="2026-12-01")
        body = self.get_json("trainer1", self.RANGE)
        self.assertEqual((body["completed"], body["ongoing"], body["pending"]), (1, 1, 1))
        self.assertEqual(body["executedPercentage"], 33)

    def test_a_trainer_with_no_trainings_gets_zeros(self):
        self.alpha.query(Conference).filter(Conference.trainerEmployeeId == "trainer3").delete()
        self.alpha.commit()
        body = self.get_json("trainer3", self.RANGE)
        self.assertEqual(
            (body["totalSessions"], body["totalTrainees"], body["completed"], body["pending"], body["recentCompleted"]),
            (0, 0, 0, 0, []),
        )


# ------------------------------------------------------------------ list headcounts and facets
class HeadcountsAreCountedInSql(Phase5TestCase):
    def test_equal_to_the_distinct_present_or_submitted_trainees(self):
        rng = random.Random(5)
        uids = [uid(key) for key in ("S_N1", "S_DEL", "S_S1", "S_BLANK", "S_N1V", "O_N1")]
        for n in range(60):
            conference_uid, trainee = rng.choice(uids), f"TR-HC-{rng.randrange(15)}"
            if rng.random() < 0.5:
                self.alpha.add(Attendance(attendanceUid=f"ATT-HC-{n}", conferenceUid=conference_uid, traineeUid=trainee,
                                          status=rng.choice(["Present", "Absent", "Pending"])))
            else:
                self.alpha.add(AssessmentResult(resultUid=f"RES-HC-{n}", conferenceUid=conference_uid, traineeUid=trainee,
                                                assessmentSuiteUid="SUITE-1", attemptNumber=1,
                                                status=rng.choice(["Submitted", "InProgress"])))
        self.alpha.commit()

        expected: dict[str, set] = {}
        for conference_uid, trainee in legacy_queries.list_present_pairs(self.alpha, uids):
            expected.setdefault(conference_uid, set()).add(trainee)
        for conference_uid, trainee in legacy_queries.list_submitted_pairs(self.alpha, uids):
            expected.setdefault(conference_uid, set()).add(trainee)
        counted = dashboard_repository.count_trained_by_conference(self.alpha, uids)
        self.assertEqual(counted, {c: len(t) for c, t in expected.items()})
        self.assertEqual(dashboard_repository.count_trained_by_conference(self.alpha, []), {})

    def test_the_training_list_shows_them(self):
        items = self.get_json("trainer1", "/admin/trainings/page")["items"]
        self.assertEqual({item["conferenceUid"]: item["traineeCount"] for item in items},
                         {uid("S_N1"): 1, uid("S_DEL"): 1, uid("S_N1V"): 1})


class FilterOptionsOnlyComeFromAuthorizedTrainings(Phase5TestCase):
    def test_facets(self):
        self.update_conference("S_S1", trainingHub="Hub Of Trainer2", trainingType="Secret Type")
        self.update_conference("S_N1", trainingHub="Hub Of Trainer1")
        mine = self.get_json("trainer1", "/admin/trainings/facets")
        self.assertIn("Hub Of Trainer1", mine["trainingHubs"])
        self.assertNotIn("Hub Of Trainer2", mine["trainingHubs"])
        self.assertNotIn("Secret Type", mine["trainingTypes"])
        self.assertIn("Hub Of Trainer2", self.get_json("super", "/admin/trainings/facets")["trainingHubs"])
        self.assertEqual(self.get_json("betaonly", "/admin/trainings/facets", tenant=BETA)["trainingHubs"],
                         [h for h in self.get_json("betaonly", "/admin/trainings/facets", tenant=BETA)["trainingHubs"]
                          if h not in ("Hub Of Trainer1", "Hub Of Trainer2")])


# ------------------------------------------------------------------------- trainer dropdowns
class TrainerPickersFollowTheAssignmentRule(Phase5TestCase):
    def names(self, who, query=""):
        return {option["value"] for option in self.get_json(who, f"/admin/trainers{query}")}

    def test_an_admin_sees_only_trainers_of_granted_companies(self):
        self.assertEqual(self.names("coadmin"), {"trainer1", "trainer2"})               # not Other Co's trainer3
        self.assertEqual(self.names("coadmin", "?company=Other%20Co"), set())
        self.assertEqual(self.names("coadmin", "?company=Samsung%20India"), {"trainer1", "trainer2"})
        self.assertEqual(self.names("coord"), {"trainer1", "trainer2"})                 # zone can't narrow trainers
        self.assertEqual(self.names("super"), {"trainer1", "trainer2", "trainer3", "adm_trainer"})
        self.assertEqual(self.w.client.get("/admin/trainers", headers=self.w.headers("ungranted")).status_code, 403)

    def test_a_trainer_sees_their_own_company(self):
        self.assertEqual(self.names("trainer1"), {"trainer1", "trainer2"})
        self.assertEqual(self.names("trainer3"), {"trainer3"})

    def test_a_trainer_name_is_only_resolved_for_pickable_trainers(self):
        def status(who, username):
            return self.w.client.get(f"/admin/trainers/{username}", headers=self.w.headers(who)).status_code

        self.assertEqual(status("trainer1", "trainer2"), 200)
        self.assertEqual(status("trainer1", "trainer3"), 404)       # another company's trainer
        self.assertEqual(status("coadmin", "trainer3"), 404)        # outside the grant
        self.assertEqual(status("coadmin", "trainer1"), 200)
        self.assertEqual(status("super", "trainer3"), 200)
        self.assertEqual(status("trainer1", "nobody"), 404)


# ---------------------------------------------------------------- admin dashboard stats + cache
class AdminDashboardStats(Phase5TestCase):
    PATH = "/admin/dashboard/stats"

    def approve_all(self):
        self.alpha.query(Conference).update({"status": "Approved"})
        self.alpha.commit()

    def test_counts_follow_the_grant_and_the_tenant(self):
        self.approve_all()
        # ALPHA: 6 fixture trainings + the base class's ADM (Samsung India, North Zone).
        self.assertEqual(self.get_json("super", self.PATH)["training"]["planned"], 7)
        self.assertEqual(self.get_json("coadmin", self.PATH)["training"]["planned"], 6)     # not Other Co's O_N1
        self.assertEqual(self.get_json("coord", self.PATH)["training"]["planned"], 4)       # North Zone (with variant)
        self.assertEqual(self.get_json("betaonly", self.PATH, tenant=BETA)["training"]["planned"], 0)  # BETA's own (Pending)
        self.assertEqual(self.get_json("coadmin", self.PATH)["trainers"]["pool"], 2)        # trainer1, trainer2

    def test_trainers_cannot_open_it(self):
        self.assertEqual(self.w.client.get(self.PATH, headers=self.w.headers("trainer1")).status_code, 403)

    def test_an_empty_scope_is_all_zeros(self):
        self.alpha.query(AssessmentResult).delete()
        self.alpha.commit()
        body = self.get_json("subcoord", self.PATH)   # Delhi NCR: S_DEL only, still Pending approval, no results
        self.assertEqual((body["training"]["planned"], body["assessment"]["attempts"], body["audience"]["present"]), (0, 0, 1))

    def test_only_the_grants_results_are_counted(self):
        self.assertEqual(self.get_json("subcoord", self.PATH)["assessment"]["attempts"], 1)   # S_DEL's own result
        self.assertEqual(self.get_json("coadmin", self.PATH)["assessment"]["attempts"], 5)    # not O_N1's

    def test_new_data_shows_on_the_next_open(self):
        self.approve_all()
        first = self.get_json("coadmin", self.PATH)["audience"]["present"]
        self.alpha.add(Attendance(attendanceUid="ATT-NEW", conferenceUid=uid("S_N1"), traineeUid="TR-S_N1-1", status="Present"))
        self.alpha.query(Attendance).filter(Attendance.attendanceUid == "ATT-S_N1-1").delete()
        self.alpha.commit()
        self.assertEqual(self.get_json("coadmin", self.PATH)["audience"]["present"], first + 1)   # no fresh=true needed

    def test_a_changed_grant_applies_on_the_next_open(self):
        self.approve_all()
        self.assertEqual(self.get_json("coadmin", self.PATH)["training"]["planned"], 6)
        self.w.common.query(AdminAccess).filter(AdminAccess.admin_id == self.w.admins["coadmin"].id).update(
            {"active": 0, "company_admin_key": None})
        self.w.common.commit()
        response = self.w.client.get(self.PATH, headers=self.w.headers("coadmin"))
        self.assertTrue(response.status_code == 403 or response.json()["training"]["planned"] == 0, response.text)


# ------------------------------------------------------------------------- per-session reports
class SessionReportsAreTheTrainersOwn(Phase5TestCase):
    def test_other_trainers_sessions_are_not_found(self):
        self.update_conference("S_S1", conferenceStatus="Completed")
        for path in ("", "/performers", "/report"):
            with self.subTest(path=path):
                self.assertEqual(self.w.client.get(f"/admin/trainings/{uid('S_S1')}{path}",
                                                   headers=self.w.headers("trainer1")).status_code, 404)
        # /detail is admin-only: every trainer gets 403 whatever the id (so it reveals nothing).
        for conference in (uid("S_S1"), uid("S_N1"), "CONF-NOPE"):
            self.assertEqual(self.w.client.get(f"/admin/trainings/{conference}/detail",
                                               headers=self.w.headers("trainer1")).status_code, 403)
        self.assertEqual(self.get_json("trainer2", f"/admin/trainings/{uid('S_S1')}/performers")[0]["traineeUid"], "TR-S_S1-0")


# -------------------------------------------------------------------------- trainee dashboard
class TraineeRanking(unittest.TestCase):
    """The SQL ranking (dashboard_repository.trainee_rank) gives exactly the ranks the old
    whole-tenant Python pool gave, and is computed on every request."""

    STATES = ["Delhi", "Punjab", "Kerala", None]

    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.db = self.w.tenant_db[ALPHA]

    def seed(self, seed):
        rng = random.Random(seed)
        trainees = [f"TR-RK-{n}" for n in range(30)]
        for n, trainee_uid in enumerate(trainees):
            self.db.add(Trainee(traineeUid=trainee_uid, name=trainee_uid, email=f"rk{n}@example.test", phone=8_000_000_000 + n,
                                state=rng.choice(self.STATES), company="Samsung India"))
        for c in range(12):
            config = rng.choice([
                json.dumps({"liveQuiz": {"assessmentSuiteUid": f"QUIZ-{c}"}}),
                json.dumps({"liveQuiz": {"assessmentSuiteUid": f"QUIZ-{c}"}, "survey": {"assessmentSuiteUid": "SURVEY"}}),
                json.dumps({"survey": {"assessmentSuiteUid": "SURVEY"}}),
                json.dumps({"liveQuiz": {"assessmentSuiteUid": 7}}),      # a number never matches a text id
                json.dumps({"liveQuiz": None}), json.dumps(["liveQuiz"]), "not json", "", None,
            ])
            self.db.add(Conference(conferenceUid=f"CONF-RK-{c}", trainerEmployeeId="trainer1", conferenceDate=f"2026-08-{c + 1:02d}",
                                   conferenceStatus=rng.choice(["Completed", "Completed", "cancelled", "CANCELLED", "Ongoing", None]),
                                   postAssessmentUid=rng.choice([f"POST-{c}", None]), sessionConfig=config))
            for trainee_uid in rng.sample(trainees, 8):
                self.db.add(Attendance(attendanceUid=f"ATT-RK-{c}-{trainee_uid}", conferenceUid=f"CONF-RK-{c}", traineeUid=trainee_uid,
                                       status=rng.choice(["Present", "Present", "Absent"])))
                for suite in (f"POST-{c}", f"QUIZ-{c}", "SURVEY", "OTHER", "7"):
                    if rng.random() < 0.6:
                        maximum = rng.choice([10, 20])
                        self.db.add(AssessmentResult(
                            resultUid=f"RES-RK-{c}-{trainee_uid}-{suite}", conferenceUid=f"CONF-RK-{c}", traineeUid=trainee_uid,
                            assessmentSuiteUid=suite, attemptNumber=1, totalScore=rng.randint(0, maximum), maxScore=maximum,
                            percentage=rng.randint(0, 100), status=rng.choice(["Submitted", "Submitted", "InProgress"])))
        self.db.commit()

    def reset(self):
        for model in (AssessmentResult, Attendance, Conference, Trainee):
            self.db.query(model).delete()
        self.db.commit()

    def legacy_ranks(self, trainee_uid, state):
        pool = legacy._ranking_pool(self.db)
        in_state = {t.traineeUid for t in self.db.query(Trainee).filter(Trainee.state == state)} if state else set()
        return legacy._rank_in(pool, trainee_uid), legacy._rank_in([p for p in pool if p[0] in in_state], trainee_uid)

    @staticmethod
    def as_tuple(position):
        return position.rank, position.total, position.percentile

    def test_same_ranks_as_before(self):
        for seed in (1, 2, 3, 4):
            with self.subTest(seed=seed):
                self.reset()
                self.seed(seed)
                for trainee in self.db.query(Trainee).all():
                    expected_global, expected_state = self.legacy_ranks(trainee.traineeUid, trainee.state)
                    global_position, state_position = dashboard_repository.trainee_rank(self.db, trainee.traineeUid, trainee.state)
                    self.assertEqual(self.as_tuple(global_position), expected_global, trainee.traineeUid)
                    self.assertEqual(self.as_tuple(state_position), expected_state, trainee.traineeUid)

    def test_two_statements_and_every_change_counts_at_once(self):
        self.seed(5)
        trainee = next(t for t in self.db.query(Trainee) if dashboard_repository.trainee_rank(self.db, t.traineeUid, t.state)[0].rank)
        statements = []
        listener = lambda conn, cursor, statement, *a: statements.append(statement)
        event.listen(self.w.alpha_engine, "before_cursor_execute", listener)
        try:
            before = dashboard_repository.trainee_rank(self.db, trainee.traineeUid, trainee.state)[0]
        finally:
            event.remove(self.w.alpha_engine, "before_cursor_execute", listener)
        self.assertEqual(len(statements), 2)
        self.db.add(Attendance(attendanceUid="ATT-NEWCOMER", conferenceUid="CONF-RK-0", traineeUid="TR-NEWCOMER", status="Present"))
        self.db.commit()
        self.assertEqual(dashboard_repository.trainee_rank(self.db, trainee.traineeUid, trainee.state)[0].total, before.total + 1)

    def test_live_quiz_id_is_read_from_the_json(self):
        self.reset()
        self.db.add(Trainee(traineeUid="TR-J", name="J", email="j@example.test", phone=8_100_000_000, state="Delhi"))
        configs = {
            "OK": json.dumps({"liveQuiz": {"assessmentSuiteUid": "QZ"}}),
            "NUM": json.dumps({"liveQuiz": {"assessmentSuiteUid": 5}}),
            "NULL": json.dumps({"liveQuiz": {"assessmentSuiteUid": None}}),
            "BAD": "{not json",
            "EMPTY": "",
        }
        for key, config in configs.items():
            self.db.add(Conference(conferenceUid=f"CONF-J-{key}", conferenceStatus="Completed", sessionConfig=config))
            self.db.add(Attendance(attendanceUid=f"ATT-J-{key}", conferenceUid=f"CONF-J-{key}", traineeUid="TR-J", status="Present"))
            suite = {"NUM": "5", "NULL": "null"}.get(key, "QZ")
            self.db.add(AssessmentResult(resultUid=f"RES-J-{key}", conferenceUid=f"CONF-J-{key}", traineeUid="TR-J",
                                         assessmentSuiteUid=suite, attemptNumber=1, totalScore=10 if key == "OK" else 0,
                                         maxScore=10, percentage=0, status="Submitted"))
        self.db.add(Trainee(traineeUid="TR-K", name="K", email="k@example.test", phone=8_100_000_001, state="Delhi"))
        self.db.add(Attendance(attendanceUid="ATT-K", conferenceUid="CONF-J-OK", traineeUid="TR-K", status="Present"))
        self.db.commit()
        # Only the valid config's quiz counts for TR-J: 10/10 = 100% -> first; TR-K has no marks -> 0%.
        self.assertEqual(self.as_tuple(dashboard_repository.trainee_rank(self.db, "TR-J", "Delhi")[0]), (1, 2, 50.0))
        self.assertEqual(self.as_tuple(dashboard_repository.trainee_rank(self.db, "TR-K", "Delhi")[1]), (2, 2, 100.0))
        self.assertEqual(self.legacy_ranks("TR-J", "Delhi")[0], (1, 2, 50.0))

    def test_each_tenant_ranks_its_own_trainees(self):
        self.seed(6)
        beta = self.w.tenant_db[BETA]
        beta_present = beta.query(Attendance.traineeUid).filter(Attendance.status == "Present").distinct().count()
        self.assertEqual(dashboard_repository.trainee_rank(beta, "TR-B_N1-0", None)[0].total, beta_present)
        self.assertIsNone(dashboard_repository.trainee_rank(beta, "TR-RK-0", None)[0].rank)

    def test_the_mysql_query_compiles(self):
        # Syntax only; the behaviour on a real MySQL is checked separately (see the Phase 5 report).
        from sqlalchemy.dialects import mysql

        sql = str(dashboard_repository._ranked().compile(dialect=mysql.dialect()))
        self.assertIn("JSON_VALID", sql)
        self.assertIn("CAST(JSON_QUOTE(", sql)


class TraineeDashboardRows(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.db = self.w.tenant_db[ALPHA]
        self.trainee = self.db.query(Trainee).filter(Trainee.traineeUid == "TR-S_N1-0").one()

    def add_sessions(self, count, start=0):
        rng = random.Random(count)
        for c in range(start, start + count):
            conference_uid = f"CONF-ROW-{c}"
            self.db.add(Conference(conferenceUid=conference_uid, trainerEmployeeId="trainer1", conferenceDate=f"2026-07-{c % 28 + 1:02d}",
                                   conferenceStatus="Completed", postAssessmentUid=f"POST-ROW-{c}",
                                   sessionConfig=json.dumps({"liveQuiz": {"assessmentSuiteUid": f"QUIZ-ROW-{c}"}})))
            self.db.add(Attendance(attendanceUid=f"ATT-ROW-{c}", conferenceUid=conference_uid, traineeUid="TR-S_N1-0", status="Present"))
            for n, percentage in enumerate(rng.sample(range(0, 101), 5)):   # distinct scores: rank order is defined
                trainee_uid = "TR-S_N1-0" if n == 0 else f"TR-ROW-{c}-{n}"
                self.db.add(AssessmentResult(resultUid=f"RES-ROW-{c}-{n}", conferenceUid=conference_uid, traineeUid=trainee_uid,
                                             assessmentSuiteUid=f"POST-ROW-{c}", attemptNumber=1, totalScore=percentage, maxScore=100,
                                             percentage=percentage, status="Submitted"))
        self.db.commit()

    def inputs(self):
        attendance = {a.conferenceUid: a for a in attendance_repository.list_for_trainee(self.db, "TR-S_N1-0")}
        results: dict[str, list] = {}
        for row in assessment_repository.list_results_for_trainee(self.db, "TR-S_N1-0"):
            results.setdefault(row.conferenceUid, []).append(row)
        from app.repositories import conference_repository

        conferences = {c.conferenceUid: c for c in conference_repository.list_by_uids(self.db, set(attendance) | set(results))}
        return attendance, results, conferences

    def test_same_rows_as_before(self):
        self.add_sessions(12)
        attendance, results, conferences = self.inputs()
        for limit in (1, 5, 500):
            with self.subTest(limit=limit):
                new = dashboard._build_training_rows(self.db, self.trainee, attendance, results, conferences, limit)
                old = legacy._build_training_rows(self.db, self.trainee, attendance, results, conferences, limit)
                self.assertEqual([r.model_dump() for r in new], [r.model_dump() for r in old])
                self.assertTrue(any(r.rank for r in new))

    def test_one_query_whatever_the_number_of_sessions(self):
        def statements_for(extra):
            self.add_sessions(extra, start=100 * extra)
            attendance, results, conferences = self.inputs()
            seen = []
            listener = lambda conn, cursor, statement, *a: seen.append(statement)
            event.listen(self.w.alpha_engine, "before_cursor_execute", listener)
            try:
                dashboard._build_training_rows(self.db, self.trainee, attendance, results, conferences, 500)
            finally:
                event.remove(self.w.alpha_engine, "before_cursor_execute", listener)
            return len(seen)

        self.assertEqual(statements_for(3), statements_for(25))

    def test_equal_scores_share_a_rank_and_each_trainee_counts_once(self):
        self.db.add(Conference(conferenceUid="CONF-TIE", trainerEmployeeId="trainer1", conferenceDate="2026-07-01",
                               conferenceStatus="Completed", postAssessmentUid="POST-TIE"))
        self.db.add(Attendance(attendanceUid="ATT-TIE", conferenceUid="CONF-TIE", traineeUid="TR-S_N1-0", status="Present"))
        results = [
            ("TR-S_N1-0", 1, 80), ("TR-TIE-A", 1, 80),                 # tied with me
            ("TR-TIE-B", 1, 95), ("TR-TIE-B", 2, 60),                  # latest attempt (60) counts, not 95
            ("TR-TIE-C", 1, 90),                                       # higher
        ]
        for n, (trainee_uid, attempt, percentage) in enumerate(results):
            self.db.add(AssessmentResult(resultUid=f"RES-TIE-{n}", conferenceUid="CONF-TIE", traineeUid=trainee_uid,
                                         assessmentSuiteUid="POST-TIE", attemptNumber=attempt, totalScore=percentage,
                                         maxScore=100, percentage=percentage, status="Submitted"))
        self.db.commit()
        self.assertEqual(dashboard_repository.session_ranks(self.db, "TR-S_N1-0", {"CONF-TIE": "POST-TIE"}), {"CONF-TIE": 2})
        self.assertEqual(dashboard_repository.session_ranks(self.db, "TR-TIE-A", {"CONF-TIE": "POST-TIE"}), {"CONF-TIE": 2})
        self.assertEqual(dashboard_repository.session_ranks(self.db, "TR-TIE-B", {"CONF-TIE": "POST-TIE"}), {"CONF-TIE": 4})
        self.assertEqual(dashboard_repository.session_ranks(self.db, "TR-NOBODY", {"CONF-TIE": "POST-TIE"}), {})

    def test_the_row_limit_is_bounded(self):
        from app.core.security import create_access_token

        headers = {"Authorization": f"Bearer {create_access_token(subject=str(self.trainee.phone), tenant_id=ALPHA, role='trainee')}"}
        for limit, expected in ((0, 422), (501, 422), (500, 200), (5, 200)):
            with self.subTest(limit=limit):
                self.assertEqual(self.w.client.get(f"/sessions/dashboard?limit={limit}", headers=headers).status_code, expected)
        self.assertEqual(self.w.client.get("/sessions/history?limit=100000", headers=headers).status_code, 422)
