"""Trainee check-in - the plain endpoint and the secure (location + photo) one share their rules
(services/attendance_service.py):

1. A first check-in creates the trainee's row as Present, tagged with how they reached the session
   (ASSIGNED on their own trainer's session, else UNASSIGNED), with one Present log under the live
   module.
2. Checking in again changes nothing; with ALLOW_ATTENDANCE_RETEST the row and its log are replaced
   by fresh ones.
3. A trainee the trainer already marked Absent is refused.
4. A geofenced session refuses the plain check-in, and a secure one from outside the radius - which
   only counts the try (attemptCount); at the venue the secure one records the photo, distance,
   location and device.
5. The secure form field is still called `conferenceUid` - what the app sends.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import settings
from app.core.security import create_access_token
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.conference import Conference
from app.models.trainee import Trainee
from tests.tenant_fixtures import ALPHA, TenantWorld

CONFERENCE = "CONF-CHECKIN"
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
AT_VENUE = {"latitude": 28.6139, "longitude": 77.2090}
FAR_AWAY = {"latitude": 28.7, "longitude": 77.3}  # about 13 km from the venue
OWN_TRAINEE = "TR-ASSIGNED-ONLY"  # trainer1's trainee
OTHER_TRAINEE = "TR-OTHER-TRAINER"  # trainer2's trainee


class CheckInTestCase(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.db = self.w.tenant_db[ALPHA]
        self.db.add(Conference(conferenceUid=CONFERENCE, trainerEmployeeId="trainer1", trainerName="Trainer1",
                               conferenceDate="2026-09-20", conferenceStatus="Ongoing", status="Approved",
                               activeModuleId="ATTENDANCE"))
        self.db.commit()

        media = tempfile.TemporaryDirectory()
        self.addCleanup(media.cleanup)
        self.media = Path(media.name)
        for patcher in (
            patch("app.routers.attendance.media_subdir", return_value=self.media),
            patch.object(settings, "ALLOW_ATTENDANCE_RETEST", False),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def headers(self, trainee_uid):
        phone = self.db.query(Trainee).filter(Trainee.traineeUid == trainee_uid).one().phone
        return {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=ALPHA, role='trainee')}"}

    def check_in(self, trainee_uid=OWN_TRAINEE):
        return self.w.client.post("/attendance/check-in", json={"conferenceUid": CONFERENCE}, headers=self.headers(trainee_uid))

    def secure_check_in(self, position, field="conferenceUid"):
        return self.w.client.post(
            "/attendance/check-in/secure",
            data={field: CONFERENCE, **position},
            files={"photo": ("face.jpg", JPEG, "image/jpeg")},
            headers=self.headers(OWN_TRAINEE),
        )

    def rows(self, trainee_uid=OWN_TRAINEE):
        self.db.expire_all()
        attendance = self.db.query(Attendance).filter(
            Attendance.conferenceUid == CONFERENCE, Attendance.traineeUid == trainee_uid
        ).all()
        logs = self.db.query(AttendanceLog).filter(
            AttendanceLog.conferenceUid == CONFERENCE, AttendanceLog.traineeUid == trainee_uid
        ).all()
        return attendance, logs

    def geofence(self):
        self.db.query(Conference).filter(Conference.conferenceUid == CONFERENCE).update({
            "geoLatitude": AT_VENUE["latitude"], "geoLongitude": AT_VENUE["longitude"], "geoRadius": 100,
            "sessionConfig": json.dumps({"attendance": {"geoFencing": True}}),
        })
        self.db.commit()


class APlainCheckIn(CheckInTestCase):
    def test_the_first_check_in_marks_the_trainee_present_with_one_log(self):
        response = self.check_in()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Present")
        (attendance,), (log,) = self.rows()
        self.assertEqual(attendance.status, "Present")
        self.assertEqual(attendance.markedOn, response.json()["markedOn"])
        self.assertEqual(attendance.trainerUid, "trainer1")
        self.assertEqual(json.loads(attendance.sessionMeta), {"audience": "ASSIGNED"})
        self.assertEqual((log.moduleId, log.status), ("ATTENDANCE", "Present"))

    def test_a_trainee_of_another_trainer_is_tagged_unassigned(self):
        self.assertEqual(self.check_in(OTHER_TRAINEE).status_code, 200)
        (attendance,), _ = self.rows(OTHER_TRAINEE)
        self.assertEqual(json.loads(attendance.sessionMeta), {"audience": "UNASSIGNED"})

    def test_checking_in_again_changes_nothing(self):
        first = self.check_in().json()
        again = self.check_in()
        self.assertEqual(again.status_code, 200, again.text)
        self.assertEqual(again.json(), first)
        attendance, logs = self.rows()
        self.assertEqual((len(attendance), len(logs)), (1, 1))

    def test_with_retests_allowed_a_second_check_in_replaces_the_row_and_its_log(self):
        self.check_in()
        with patch.object(settings, "ALLOW_ATTENDANCE_RETEST", True):
            response = self.check_in()
        self.assertEqual(response.status_code, 200, response.text)
        (attendance,), (log,) = self.rows()
        self.assertEqual((attendance.status, attendance.attemptCount), ("Present", 1))
        self.assertEqual((log.status, log.deviceInfo), ("Present", "testclient"))

    def test_a_trainee_marked_absent_is_refused(self):
        self.db.add(Attendance(conferenceUid=CONFERENCE, traineeUid=OWN_TRAINEE, status="Absent"))
        self.db.commit()
        response = self.check_in()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "You've been marked absent for this session.")
        (attendance,), logs = self.rows()
        self.assertEqual((attendance.status, logs), ("Absent", []))

    def test_a_geofenced_session_needs_the_secure_check_in(self):
        self.geofence()
        response = self.check_in()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.rows(), ([], []))


class ASecureCheckIn(CheckInTestCase):
    def test_at_the_venue_it_records_the_photo_distance_location_and_device(self):
        self.geofence()
        response = self.secure_check_in(AT_VENUE)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "Present")
        self.assertLess(response.json()["distanceMeters"], 1)
        (attendance,), (log,) = self.rows()
        self.assertEqual((attendance.status, attendance.checkInDistance), ("Present", "0"))
        self.assertEqual(json.loads(attendance.sessionMeta), {"audience": "ASSIGNED"})
        self.assertTrue(attendance.checkInPhoto.startswith("attendance_photos/"))
        self.assertEqual((self.media / attendance.checkInPhoto.split("/")[-1]).read_bytes(), JPEG)
        self.assertEqual((log.moduleId, log.status), ("ATTENDANCE", "Present"))
        self.assertEqual(log.locationData, f"{AT_VENUE['latitude']},{AT_VENUE['longitude']}")
        self.assertEqual(log.deviceInfo, "testclient")

    def test_outside_the_radius_it_is_refused_and_only_the_try_is_counted(self):
        self.geofence()
        response = self.secure_check_in(FAR_AWAY)
        self.assertEqual(response.status_code, 400)
        self.assertIn("from the venue", response.json()["detail"])
        (attendance,), logs = self.rows()
        # The try is counted (attemptCount: the try they get in on); nothing else is saved.
        self.assertEqual((attendance.status, attendance.attemptCount, attendance.checkInPhoto, logs), ("Joined", 2, None, []))
        self.assertEqual(list(self.media.iterdir()), [])

    def test_a_second_secure_check_in_keeps_the_first_photo(self):
        self.secure_check_in(AT_VENUE)
        (first,), _ = self.rows()
        again = self.secure_check_in(AT_VENUE)
        self.assertEqual(again.status_code, 200, again.text)
        (attendance,), logs = self.rows()
        self.assertEqual((attendance.checkInPhoto, len(logs)), (first.checkInPhoto, 1))

    def test_the_form_field_is_still_called_conferenceUid(self):
        response = self.secure_check_in(AT_VENUE, field="conference_uid")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.rows(), ([], []))


if __name__ == "__main__":
    unittest.main()
