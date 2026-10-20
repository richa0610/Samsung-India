"""conference_activity_log is written the other system's way (user, 2026-10-17 - replacing the
2026-10-08 "location on every trainer action" rule): only the session-start entry says where the
trainer was; a venue-location override is "GPS_OVERRIDE: <new location>"; module entries carry the
module's ID and no location; the session's start / end are STARTED / STOPPED with no module; who did
it is the person's name; times are India time. A missing location never blocks an action."""

import json
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.services.training import timeline
from app.utils.date_utils import ist_now
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

    def rows(self):
        self.alpha.expire_all()
        return self.alpha.query(ConferenceActivityLog).filter(ConferenceActivityLog.conferenceUid == S_N1).order_by(ConferenceActivityLog.id).all()

    def assertAt(self, row, point):
        self.assertAlmostEqual(float(row.trainerLat), point[0], places=6)
        self.assertAlmostEqual(float(row.trainerLng), point[1], places=6)

    def test_the_session_start_records_where_the_trainer_was(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        [row] = self.rows()
        self.assertEqual((row.moduleId, row.action, row.performedBy, row.locationRemark), ("", "STARTED", "Trainer1", None))
        self.assertAt(row, AT_VENUE)
        self.assertLess(abs(row.timestamp - ist_now()), timedelta(minutes=1))     # India time

    def test_a_venue_location_override_is_written_as_gps_override(self):
        refused = self.start(FAR_AWAY)
        self.assertEqual(refused.json()["detail"]["code"], "OUTSIDE_VENUE")   # the prompt that offers the override
        self.assertEqual(self.start(FAR_AWAY, venue=FAR_AWAY).status_code, 200)
        [row] = self.rows()
        self.assertAt(row, FAR_AWAY)
        self.assertEqual(row.locationRemark, "GPS_OVERRIDE: 28.700000, 77.300000")

    def test_module_and_end_entries_carry_the_module_and_no_location(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        started = self.w.client.post(f"/admin/trainings/{S_N1}/modules/STANDARD_TEST/start",
                                     json={"latitude": FAR_AWAY[0], "longitude": FAR_AWAY[1]}, headers=self.headers)
        self.assertEqual(started.status_code, 200, started.text)                # an older app's location is ignored
        stopped = self.w.client.post(f"/admin/trainings/{S_N1}/modules/stop-active", headers=self.headers)
        self.assertEqual(stopped.status_code, 200, stopped.text)
        ended = self.w.client.post(
            f"/admin/trainings/{S_N1}/end", headers=self.headers,
            files={"photo": PHOTO, "attendanceSheet": ("s.pdf", b"%PDF-1.4", "application/pdf")},
            data={"totalPax": "2", "latitude": str(AT_VENUE[0]), "longitude": str(AT_VENUE[1])},
        )
        self.assertEqual(ended.status_code, 200, ended.text)
        self.assertEqual(
            [(r.moduleId, r.action, r.performedBy, r.trainerLat, r.locationRemark) for r in self.rows()[1:]],
            [("Assessment_SUITE-1", "STARTED", "Trainer1", None, None),
             ("Assessment_SUITE-1", "STOPPED", "Trainer1", None, None),
             ("", "STOPPED", "Trainer1", None, None)],
        )

    def test_impossible_start_coordinates_are_refused(self):
        self.assertEqual(self.start((95.0, 77.2)).status_code, 422)
        self.assertEqual(self.start(AT_VENUE).status_code, 200)

    def test_the_execution_flow_reads_the_new_rows(self):
        self.assertEqual(self.start(AT_VENUE).status_code, 200)
        self.w.client.post(f"/admin/trainings/{S_N1}/modules/STANDARD_TEST/start", headers=self.headers)
        self.alpha.expire_all()
        conference = self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).one()
        flow = {item.moduleKey: item for item in timeline.execution_flow(self.alpha, conference)}
        self.assertEqual(flow["STANDARD_TEST"].status, "Running")
        self.assertLess(flow["STANDARD_TEST"].elapsedSeconds, 60)
        self.assertTrue(flow["STANDARD_TEST"].startedAt.endswith("+05:30"))
        self.assertNotIn(None, {entry.moduleKey for entry in timeline.audit_log(self.alpha, conference)})
