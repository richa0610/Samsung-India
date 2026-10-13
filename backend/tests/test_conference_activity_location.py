"""conference_activity_log records where the trainer was for every trainer action (user, 2026-10-08):
session start (with a venue-location override spelled out in locationRemark), each module start /
restart / stop, and session end. A missing location never blocks an action."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.services.training import timeline
from tests.tenant_fixtures import uid
from tests.test_trainer_authorization import TrainerWorldTestCase

S_N1 = uid("S_N1")
VENUE = (28.6139, 77.2090)          # the session's venue (geofence centre, 100 m)
AT_VENUE = (28.6140, 77.2091)       # ~14 m away
FAR_AWAY = (28.7000, 77.3000)       # ~13 km away
PHOTO = ("p.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 64, "image/jpeg")


class TrainerLocationOnTheActivityLog(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for target in ("app.routers.media.MEDIA_ROOT", "app.core.media.MEDIA_ROOT"):
            self.enterContext(patch(target, root))
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({
            "status": "Approved", "geoLatitude": VENUE[0], "geoLongitude": VENUE[1], "geoRadius": 100,
            "sessionConfig": json.dumps({"attendance": {"geoFencing": True}}),
        })
        self.alpha.commit()
        self.headers = self.w.headers("trainer1")

    def start(self, at, venue=None):
        data = {"latitude": str(at[0]), "longitude": str(at[1])}
        if venue:
            data.update(venueLatitude=str(venue[0]), venueLongitude=str(venue[1]))
        return self.w.client.post(f"/admin/trainings/{S_N1}/start", files={"photo": PHOTO}, data=data, headers=self.headers)

    def rows(self, action):
        self.alpha.expire_all()
        return (self.alpha.query(ConferenceActivityLog)
                .filter(ConferenceActivityLog.conferenceUid == S_N1, ConferenceActivityLog.action == action)
                .order_by(ConferenceActivityLog.id).all())

    def assertAt(self, row, point):
        self.assertAlmostEqual(float(row.trainerLat), point[0], places=6)
        self.assertAlmostEqual(float(row.trainerLng), point[1], places=6)

    def test_a_session_started_at_the_venue_records_where_the_trainer_was(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        [row] = self.rows("SESSION_STARTED")
        self.assertAt(row, AT_VENUE)
        self.assertEqual((row.moduleId, row.performedBy), (None, "trainer1"))
        self.assertRegex(row.locationRemark, r"^At the venue - \d+ m from it \(allowed 100 m\)$")

    def test_a_venue_location_override_is_spelled_out_in_the_location_remark(self):
        refused = self.start(FAR_AWAY)
        self.assertEqual(refused.json()["detail"]["code"], "OUTSIDE_VENUE")   # the prompt that offers the override
        self.assertEqual(self.start(FAR_AWAY, venue=FAR_AWAY).status_code, 200)

        [row] = self.rows("SESSION_STARTED")
        self.assertAt(row, FAR_AWAY)
        self.assertRegex(
            row.locationRemark,
            r"^Venue location overridden by the trainer: from 28\.613900, 77\.209000 to 28\.700000, 77\.300000"
            r" - the trainer was \d{4,} m from the original venue \(allowed 100 m\)$",
        )

    def test_module_actions_record_the_position_sent_and_never_require_one(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        started = self.w.client.post(f"/admin/trainings/{S_N1}/modules/STANDARD_TEST/start",
                                     json={"latitude": FAR_AWAY[0], "longitude": FAR_AWAY[1]}, headers=self.headers)
        self.assertEqual(started.status_code, 200, started.text)
        stopped = self.w.client.post(f"/admin/trainings/{S_N1}/modules/stop-active", headers=self.headers)   # no location
        self.assertEqual(stopped.status_code, 200, stopped.text)

        [start_row] = self.rows("STARTED")
        self.assertAt(start_row, FAR_AWAY)
        self.assertRegex(start_row.locationRemark, r"^Outside the venue - \d+ m from it \(allowed 100 m\)$")
        [stop_row] = self.rows("STOPPED")
        self.assertIsNone(stop_row.trainerLat)
        self.assertEqual(stop_row.locationRemark, "Trainer location not shared")

    def test_ending_the_session_records_where_the_trainer_was(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        ended = self.w.client.post(
            f"/admin/trainings/{S_N1}/end", headers=self.headers,
            files={"photo": PHOTO, "attendanceSheet": ("s.pdf", b"%PDF-1.4", "application/pdf")},
            data={"totalPax": "2", "latitude": str(AT_VENUE[0]), "longitude": str(AT_VENUE[1])},
        )
        self.assertEqual(ended.status_code, 200, ended.text)
        [row] = self.rows("SESSION_ENDED")
        self.assertAt(row, AT_VENUE)

    def test_impossible_coordinates_are_refused(self):
        self.assertEqual(self.start((95.0, 77.2)).status_code, 422)
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        response = self.w.client.post(f"/admin/trainings/{S_N1}/modules/STANDARD_TEST/start",
                                      json={"latitude": 28.6, "longitude": 200}, headers=self.headers)
        self.assertEqual(response.status_code, 422)

    def test_the_new_rows_stay_out_of_the_execution_flow_timeline(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        self.alpha.expire_all()
        conference = self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).one()
        keys = {entry.moduleKey for entry in timeline.audit_log(self.alpha, conference)}
        self.assertNotIn(None, keys)
        self.assertFalse(keys & {"SESSION_STARTED", "SESSION_ENDED"})
