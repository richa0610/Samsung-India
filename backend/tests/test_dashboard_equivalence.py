"""The admin dashboard now counts in SQL (repositories/dashboard_repository.py).
`_legacy_admin_service.py` is the previous implementation, which loaded every
row and counted in Python. This runs both on the same randomised data and
requires identical responses, across a spread of filters - so the rewrite can
change how the numbers are computed but never what they are."""

import json
import random
import unittest
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import CommonBase, TenantBase
from app.dependencies.filters import ConferenceFilters
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.services import admin_service
from tests import _legacy_admin_service as legacy

ZONES = ["North Zone", "South Zone", "East Zone", " west zone "]
TYPES = ["Webinar", "Classroom Training", "Product Training", "", None, "Workshop"]
CONF_STATUS = ["Scheduled", "Ongoing", "Completed", "Cancelled", "completed", "scheduled", None]
APPROVAL = ["Approved", "Pending", "Rejected", "approved"]
COMPANIES = ["Samsung India", "samsung india ", "Other Co"]
TRAINERS = ["t1", "t2", "t3", "t4", "ghost"]


def _memory_engine():
    return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)


class DashboardEquivalenceTests(unittest.TestCase):
    def setUp(self):
        rng = random.Random(7)
        common_engine, tenant_engine = _memory_engine(), _memory_engine()
        CommonBase.metadata.create_all(bind=common_engine)
        TenantBase.metadata.create_all(bind=tenant_engine)
        self.common = sessionmaker(bind=common_engine)()
        self.db = sessionmaker(bind=tenant_engine)()

        self.common.add(Admin(adminUid="a1", username="t1", password="x", role="trainer", company="Samsung India"))
        self.common.add(Admin(adminUid="a2", username="t2", password="x", role="trainer", company="Other Co"))
        self.db.add(AgencyTeam(agencyTeamUid="g3", username="t3", password="x", role="trainer", company="Samsung India"))
        self.db.add(AgencyTeam(agencyTeamUid="g4", username="t4", password="x", role="trainer", company="Samsung India"))
        self.common.commit()

        start = date(2026, 8, 1)
        uids = []
        for n in range(300):
            uid = f"conf{n}"
            uids.append(uid)
            self.db.add(
                Conference(
                    conferenceUid=uid,
                    zone=rng.choice(ZONES),
                    region=rng.choice(["North 1", "South 2", None]),
                    company=rng.choice(COMPANIES),
                    trainerEmployeeId=rng.choice(TRAINERS),
                    conferenceDate=(start + timedelta(days=rng.randint(0, 60))).isoformat(),
                    conferenceStatus=rng.choice(CONF_STATUS) or "Scheduled",
                    status=rng.choice(APPROVAL),
                    sessionType=rng.choice(["Online", "Offline", None]),
                    trainingType=rng.choice(TYPES),
                    confirmedPax=rng.choice(["0", "12", "25", "abc", None, " 7 "]),
                )
            )
        self.db.commit()

        for n in range(1500):
            conf = rng.choice(uids + ["orphan"])
            trainee = f"tr{rng.randint(0, 400)}"
            self.db.add(
                Attendance(
                    attendanceUid=f"att{n}",
                    conferenceUid=conf,
                    traineeUid=trainee,
                    status=rng.choice(["Present", "Present", "Absent", "Pending"]),
                    sessionMeta=rng.choice(
                        [None, json.dumps({"audience": "FRESH"}), json.dumps({"audience": "ASSIGNED"}), "not json"]
                    ),
                )
            )
        for n in range(900):
            self.db.add(
                AssessmentResult(
                    resultUid=f"res{n}",
                    conferenceUid=rng.choice(uids + ["orphan"]),
                    traineeUid=f"tr{rng.randint(0, 400)}",
                    assessmentSuiteUid=rng.choice(["s1", "s2"]),
                    percentage=rng.choice([0, 20, 49.5, 50, 75.25, 100]),
                    status=rng.choice(["Submitted", "Submitted", "Started"]),
                )
            )
        self.db.commit()

    def _assert_same(self, filters):
        old = legacy.build_admin_dashboard_stats(self.common, self.db, filters).model_dump()
        new = admin_service.build_admin_dashboard_stats(self.common, self.db, filters).model_dump()
        self.assertEqual(old, new)

    def test_no_filter(self):
        self._assert_same(ConferenceFilters())

    def test_date_range(self):
        self._assert_same(ConferenceFilters(start="2026-08-15", end="2026-09-10"))
        self._assert_same(ConferenceFilters(start="2026-09-24", end="2026-09-24"))

    def test_zone_trainer_and_types(self):
        self._assert_same(ConferenceFilters(zones=["north zone", "west zone"]))
        self._assert_same(ConferenceFilters(trainers=["t1", "t3"]))
        self._assert_same(ConferenceFilters(regions=["north 1"], session_types=["online"]))
        self._assert_same(ConferenceFilters(training_types=["webinar", "workshop"]))

    def test_company_scope_with_filters(self):
        self._assert_same(ConferenceFilters(company="Samsung India"))
        self._assert_same(
            ConferenceFilters(company="samsung india", zones=["south zone"], start="2026-08-01", end="2026-10-01")
        )

    def test_nothing_matches(self):
        self._assert_same(ConferenceFilters(zones=["mars zone"]))


if __name__ == "__main__":
    unittest.main()
