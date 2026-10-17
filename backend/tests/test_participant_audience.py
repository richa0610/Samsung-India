"""Session Dashboard participant rows carry the participant's real audience type - ASSIGNED,
UNASSIGNED or FRESH, as recorded when they joined (attendance.sessionMeta) - the same split the
Audience Breakdown counts, instead of folding the last two into one."""

import json

from app.models.attendance import Attendance
from tests.tenant_fixtures import uid
from tests.test_trainer_authorization import TrainerWorldTestCase


class ParticipantRowsCarryTheirAudienceType(TrainerWorldTestCase):
    def joined(self, attendance_uid, status, audience=None):
        meta = json.dumps({"audience": audience}) if audience else None
        self.alpha.query(Attendance).filter(Attendance.attendanceUid == attendance_uid).update({"status": status, "sessionMeta": meta})
        self.alpha.commit()

    def test_assigned_unassigned_and_fresh_each_show_as_themselves(self):
        self.joined("ATT-S_N1-0", "Present", "FRESH")
        self.joined("ATT-S_N1-1", "Joined", "ASSIGNED")
        self.joined("ATT-RO", "Joined")  # no recorded audience (a legacy row) -> UNASSIGNED

        response = self.get("trainer1", f"/admin/trainings/{uid('S_N1')}")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        audience = {row["traineeUid"]: row["audienceType"] for row in body["trainees"]}

        self.assertEqual(audience, {"TR-S_N1-0": "FRESH", "TR-S_N1-1": "ASSIGNED", "TR-ROSTER-ONLY": "UNASSIGNED"})
        # The same split the Audience Breakdown card counts.
        self.assertEqual(
            (body["audience"]["assigned"], body["audience"]["unassigned"], body["audience"]["fresh"]),
            (1, 1, 1),
        )
