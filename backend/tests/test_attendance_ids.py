"""An attendance row's ID names how the trainee reached the training, as the other system's do
(user, 2026-10-16): NATD a new user (registered through the QR), ATN one on the trainer's roster, EXATD
an existing / unassigned one - + YY + a running number, e.g. NATD2610001. Rows that already have an ID
keep it.

In-memory SQLite only."""

import json
import unittest
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import TenantBase
from app.models.attendance import Attendance
from app.utils import join_code
from tests.tenant_fixtures import ALPHA
from tests.test_check_in import CONFERENCE, OTHER_TRAINEE, OWN_TRAINEE, CheckInTestCase


class ThePrefixFollowsTheTraineesType(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        TenantBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)
        clock = patch("app.utils.uid.ist_now", return_value=datetime(2026, 10, 16, 10, 0))
        clock.start()
        self.addCleanup(clock.stop)

    def saved(self, audience=None, uid=None):
        meta = json.dumps({"audience": audience}) if audience else None
        row = Attendance(conferenceUid="CONF-1", traineeUid=f"TRN-{audience}", status="Joined", sessionMeta=meta, attendanceUid=uid)
        self.db.add(row)
        self.db.commit()
        return row.attendanceUid

    def test_new_assigned_and_existing_users(self):
        self.assertEqual(
            [self.saved("FRESH"), self.saved("ASSIGNED"), self.saved("UNASSIGNED"), self.saved()],
            ["NATD2610001", "ATN2610001", "EXATD2610001", "EXATD2610002"],   # no type saved = an existing user
        )

    def test_a_row_that_has_an_id_keeps_it(self):
        self.assertEqual(self.saved("FRESH", uid="ATN25001"), "ATN25001")


class EveryWayARowIsCreated(CheckInTestCase):
    def setUp(self):
        super().setUp()
        ids = patch("app.models.uid_events.next_uid", side_effect=lambda _connection, prefix: f"{prefix}-ID")
        ids.start()
        self.addCleanup(ids.stop)

    def uid(self, trainee_uid):
        (row,), _ = self.rows(trainee_uid)
        return row.attendanceUid

    def join(self, trainee_uid, via_registration):
        path = f"/sessions/join/{join_code.make(ALPHA, CONFERENCE)}?viaRegistration={str(via_registration).lower()}"
        response = self.w.client.post(path, headers=self.headers(trainee_uid))
        self.assertEqual(response.status_code, 200, response.text)

    def test_check_in_by_the_trainers_own_trainee_is_atn(self):
        self.assertEqual(self.check_in(OWN_TRAINEE).status_code, 200)
        self.assertEqual(self.uid(OWN_TRAINEE), "ATN-ID")

    def test_check_in_by_another_trainers_trainee_is_exatd(self):
        self.assertEqual(self.check_in(OTHER_TRAINEE).status_code, 200)
        self.assertEqual(self.uid(OTHER_TRAINEE), "EXATD-ID")

    def test_a_qr_join_right_after_registering_is_natd(self):
        self.join(OTHER_TRAINEE, via_registration=True)
        self.assertEqual(self.uid(OTHER_TRAINEE), "NATD-ID")

    def test_a_qr_join_by_an_existing_user_is_exatd(self):
        self.join(OTHER_TRAINEE, via_registration=False)
        self.assertEqual(self.uid(OTHER_TRAINEE), "EXATD-ID")
