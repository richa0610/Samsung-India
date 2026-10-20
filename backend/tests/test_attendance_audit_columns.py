"""The attendance row's audit columns.

- updationOn / token / logPath: every write stamps when (UTC), a one-way fingerprint of the login
  token it was made with (never the token) and the request (models/audit_stamp_events.py).
- attemptCount: on a geofenced session, the secure check-in try the trainee got in on - 1 on the
  first, each refused try from outside the venue adds 1.
- masterRemarks: the latest reason a trainer typed (mark, unlock).
- geofenceBypass / bypassRemark: 1 + the reason when the trainer marks someone Present on a
  geofenced session without their own located check-in; 0 / empty otherwise.
"""

from app.core.request_context import token_fingerprint
from app.models.attendance import Attendance
from tests.test_check_in import AT_VENUE, CONFERENCE, FAR_AWAY, OWN_TRAINEE, CheckInTestCase

MARK_URL = f"/admin/trainings/{CONFERENCE}/attendance/{OWN_TRAINEE}"


class AttendanceAuditTestCase(CheckInTestCase):
    def row(self) -> Attendance:
        (attendance,), _ = self.rows()
        return attendance

    def trainer(self, path, body):
        # Kept: a token made again later carries a later issue time once the clock ticks over a second.
        self.trainer_headers = self.w.headers("trainer1")
        return self.w.client.post(path, json=body, headers=self.trainer_headers)

    def join(self):
        """The trainee on the session as "Joined" - before any check-in of their own."""
        self.db.add(Attendance(conferenceUid=CONFERENCE, traineeUid=OWN_TRAINEE, trainerUid="trainer1", status="Joined"))
        self.db.commit()


class WhoWhenHow(AttendanceAuditTestCase):
    def test_the_trainees_check_in_stamps_its_own_request(self):
        # The token that was sent - a second one minted after the request differs once its
        # issued-at second has moved on.
        headers = self.headers(OWN_TRAINEE)
        self.assertEqual(self.secure_check_in(AT_VENUE, headers=headers).status_code, 200)
        row = self.row()
        raw_token = headers["Authorization"].removeprefix("Bearer ")
        self.assertIsNotNone(row.updationOn)
        self.assertEqual(row.token, token_fingerprint(raw_token))
        self.assertNotIn(raw_token, row.token)
        self.assertEqual(row.logPath, "POST /attendance/check-in/secure")

    def test_a_trainers_change_is_stamped_with_the_trainers_request(self):
        self.secure_check_in(AT_VENUE)
        response = self.trainer(MARK_URL, {"status": "Absent", "reason": "Left after check-in"})
        self.assertEqual(response.status_code, 200, response.text)
        row = self.row()
        trainer_token = self.trainer_headers["Authorization"].removeprefix("Bearer ")
        self.assertEqual(row.token, token_fingerprint(trainer_token))
        self.assertEqual(row.logPath, f"POST {MARK_URL}"[:100])


class CheckInTries(AttendanceAuditTestCase):
    def test_each_refused_try_from_outside_the_venue_counts(self):
        self.geofence()
        for _ in range(2):
            self.assertEqual(self.secure_check_in(FAR_AWAY).status_code, 400)
        self.assertEqual(self.secure_check_in(AT_VENUE).status_code, 200)
        row = self.row()
        self.assertEqual((row.status, row.attemptCount), ("Present", 3))

    def test_in_on_the_first_try_is_one(self):
        self.geofence()
        self.secure_check_in(AT_VENUE)
        self.assertEqual(self.row().attemptCount, 1)

    def test_a_try_after_checking_in_is_not_counted(self):
        self.geofence()
        self.secure_check_in(AT_VENUE)
        self.assertEqual(self.secure_check_in(FAR_AWAY).status_code, 200)   # already in: nothing to do
        self.assertEqual(self.row().attemptCount, 1)


class TrainerReasons(AttendanceAuditTestCase):
    def test_marking_present_on_a_geofenced_session_without_check_in_is_a_bypass(self):
        self.geofence()
        self.join()
        response = self.trainer(MARK_URL, {"status": "Present", "reason": "Phone GPS not working"})
        self.assertEqual(response.status_code, 200, response.text)
        row = self.row()
        self.assertEqual((row.geofenceBypass, row.bypassRemark, row.masterRemarks),
                         (1, "Phone GPS not working", "Phone GPS not working"))

    def test_marking_absent_or_without_a_geofence_is_no_bypass(self):
        self.join()
        self.trainer(MARK_URL, {"status": "Present", "reason": "Seen in the room"})   # no geofence
        self.assertEqual((self.row().geofenceBypass, self.row().bypassRemark), (0, None))
        self.geofence()
        self.trainer(MARK_URL, {"status": "Absent", "reason": "Left early"})
        row = self.row()
        self.assertEqual((row.geofenceBypass, row.bypassRemark, row.masterRemarks), (0, None, "Left early"))

    def test_the_trainees_own_check_in_clears_an_earlier_bypass(self):
        self.geofence()
        self.join()
        self.trainer(MARK_URL, {"status": "Present", "reason": "Phone GPS not working"})
        self.assertEqual(self.secure_check_in(AT_VENUE).status_code, 200)
        row = self.row()
        self.assertEqual((row.geofenceBypass, row.bypassRemark, row.masterRemarks), (0, None, "Phone GPS not working"))

    def test_an_unlock_keeps_its_reason(self):
        self.join()
        self.db.query(Attendance).filter_by(conferenceUid=CONFERENCE, traineeUid=OWN_TRAINEE).update({"isTheftLocked": 1})
        self.db.commit()
        response = self.trainer(f"{MARK_URL}/unlock", {"reason": "Camera glare, not cheating"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.row().masterRemarks, "Camera glare, not cheating")
