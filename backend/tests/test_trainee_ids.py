"""A trainee's ID starts with their zone, as the other system's do (user, 2026-10-16): the zone's letters
in capitals + YY + a running number per zone (SOUTH2610001), TRN when there's no zone. The app makes it:
the New Trainee form no longer sends one (an older build's typed ID is ignored) and the trainee signs in
with it; a self-registering trainee picks a zone and region from the master list.

In-memory SQLite only."""

import unittest
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import rate_limit
from app.database.connection import TenantBase
from app.models.agency import Agency
from app.models.category import Category, SubCategory
from app.models.trainee import Trainee
from app.utils.zones import zone_code
from tests.tenant_fixtures import ALPHA
from tests.test_trainer_authorization import TrainerWorldTestCase


class TheZoneCode(unittest.TestCase):
    def test_letters_of_the_zone_in_capitals(self):
        cases = {"South": "SOUTH", "North Zone": "NORTH", " north east ": "NORTHEAST", "": "", None: ""}
        for zone, code in cases.items():
            with self.subTest(zone=zone):
                self.assertEqual(zone_code(zone), code)


class TheIdFollowsTheZone(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        TenantBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)
        clock = patch("app.utils.uid.ist_now", return_value=datetime(2026, 10, 16, 10, 0))
        clock.start()
        self.addCleanup(clock.stop)
        self.count = 0

    def saved(self, zone=None, uid=None):
        self.count += 1
        row = Trainee(name="T", email=f"t{self.count}@example.test", phone=9_000_000_000 + self.count, zone=zone, traineeUid=uid)
        self.db.add(row)
        self.db.commit()
        return row.traineeUid

    def test_zone_then_year_then_a_running_number_per_zone(self):
        self.assertEqual(
            [self.saved("South"), self.saved("South"), self.saved("North Zone"), self.saved()],
            ["SOUTH2610001", "SOUTH2610002", "NORTH2610001", "TRN2610001"],
        )

    def test_a_trainee_that_has_an_id_keeps_it(self):
        self.assertEqual(self.saved("South", uid="SOUTH116112"), "SOUTH116112")


class TraineeIdsTestCase(TrainerWorldTestCase):
    """The synthetic world makes stand-in IDs, "<prefix>-<n>" (tests/tenant_fixtures.py) - the prefix
    is what these tests check; the real number format is TheIdFollowsTheZone's."""

    def setUp(self):
        super().setUp()
        rate_limit.reset()
        self.addCleanup(rate_limit.reset)
        self.alpha.add_all([
            Category(categoryUid="CAT-S", name="South", visibleOnWeb="Zone", status="Approved"),
            SubCategory(subCategoryUid="SUB-S1", categoryUid="CAT-S", subCategory="South 1", status="Approved"),
        ])
        self.alpha.commit()


class SelfRegistration(TraineeIdsTestCase):
    def register(self, n, **place):
        body = {"name": f"New Person {n}", "phone": 7_100_000_000 + n, "email": f"new{n}@example.org", "state": "Kerala", **place}
        return self.w.client.post("/trainees/register", json=body, headers={"X-Tenant-ID": ALPHA, "X-Forwarded-For": f"198.51.100.{n}"})

    def test_the_zone_and_region_picked_name_the_trainee_and_are_saved_as_the_master_spells_them(self):
        response = self.register(1, zone="south", region="SOUTH 1")
        self.assertEqual(response.status_code, 201, response.text)
        trainee = response.json()["trainee"]
        self.assertRegex(trainee["traineeUid"], r"^SOUTH-\d+$")
        self.assertEqual((trainee["zone"], trainee["region"]), ("South", "South 1"))

    def test_a_self_registered_trainee_is_filed_under_the_tenants_company(self):
        # Before 2026-10-18 they had no company at all - invisible to a company-scoped admin.
        self.w.common.add(Agency(agencyUid="AGY2687355", companyName="Samsung India"))
        self.w.common.commit()
        response = self.register(5, zone="South", region="South 1")
        self.assertEqual(response.status_code, 201, response.text)
        self.alpha.expire_all()
        stored = self.alpha.query(Trainee).filter_by(traineeUid=response.json()["trainee"]["traineeUid"]).one()
        self.assertEqual(stored.company, "AGY2687355")
        listed = self.w.client.get("/admin/trainees/page?limit=200", headers=self.w.headers("coadmin")).json()["items"]
        self.assertIn(("Samsung India", stored.traineeUid), [(t["company"], t["traineeUid"]) for t in listed])

    def test_a_zone_or_region_not_on_the_master_list_is_refused(self):
        self.assertEqual(self.register(2, zone="Atlantis", region="South 1").status_code, 400)
        self.assertEqual(self.register(3, zone="South", region="North 1").status_code, 400)

    def test_an_older_app_that_sends_no_zone_still_registers_with_a_trn_id(self):
        response = self.register(4)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertRegex(response.json()["trainee"]["traineeUid"], r"^TRN-\d+$")

    def test_the_zone_list_is_there_before_sign_in(self):
        response = self.w.client.get("/locations/zones", headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), [{"name": "South", "options": ["South 1"]}])


class NewTraineeForm(TraineeIdsTestCase):
    BODY = {"fullName": "Form Person", "designation": "Promoter", "gender": "Female", "primaryEmail": "form@example.org",
            "primaryPhone": "9123456711", "state": "Delhi", "zone": "North Zone", "region": "North 1",
            "requestedBy": "Quess", "trainerId": "trainer1", "trainerName": "Trainer One", "supervisorId": "s",
            "supervisorName": "S", "jobStatus": "Active", "password": "Correct-Horse-9"}

    def add(self, **extra):
        response = self.w.client.post("/admin/trainees", json={**self.BODY, **extra}, headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def stored(self, uid):
        self.alpha.expire_all()
        return self.alpha.query(Trainee).filter_by(traineeUid=uid).one()

    def test_the_server_makes_the_id_and_the_trainee_signs_in_with_it(self):
        uid = self.add()["traineeUid"]
        self.assertRegex(uid, r"^NORTH-\d+$")                                    # zone "North Zone"
        self.assertEqual(self.stored(uid).username, uid)
        login = self.w.client.post("/trainees/login", json={"identifier": uid, "password": "Correct-Horse-9"},
                                   headers={"X-Tenant-ID": ALPHA})
        self.assertEqual(login.status_code, 200, login.text)

    def test_an_older_app_s_typed_id_is_ignored_but_its_username_kept(self):
        uid = self.add(traineeUid="TYPED-1", username="TYPED-1")["traineeUid"]
        self.assertRegex(uid, r"^NORTH-\d+$")
        self.assertEqual(self.stored(uid).username, "TYPED-1")

    def test_a_trainee_without_a_username_doesn_t_count_as_a_duplicate(self):
        self.alpha.add(Trainee(traineeUid="TRN-SELF", name="Self", email="self@example.org", phone=7_200_000_000, username=None))
        self.alpha.commit()
        created = self.add()  # not refused as a duplicate of the trainee with no username
        self.assertEqual(self.stored(created["traineeUid"]).name, "Form Person")
