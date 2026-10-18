"""The public training ID format (app/utils/conference_id.py) and signed QR join codes
(app/utils/join_code.py): guessing or editing an ID, or changing the tenant, reveals nothing - so a
counted ID (the other system's shape, user 2026-10-17) is safe to use."""

import re
import unittest
from datetime import datetime
from unittest.mock import patch

from app.core.security import create_access_token
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.utils import conference_id, join_code
from app.utils.date_utils import ist_now
from tests.tenant_fixtures import ALPHA, BETA, TenantWorld, uid

OPEN = uid("S_N1")  # trainer1's training in ALPHA


class ConferenceIdAllocation(unittest.TestCase):
    """CONF + YY + a 5-digit running number, as the other system's IDs (user, 2026-10-17)."""

    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.db = self.w.tenant_db[ALPHA]
        self.year = f"{ist_now().year % 100:02d}"

    def add_training(self, conference_uid=None):
        conference = Conference(conferenceUid=conference_uid, company="Samsung India", conferenceDate="2026-10-05")
        self.db.add(conference)
        self.db.commit()
        return conference.conferenceUid

    def test_new_trainings_get_their_shape_counting_up(self):
        first, second = self.add_training(), self.add_training()
        self.assertRegex(first, rf"^CONF{self.year}\d{{5}}$")
        self.assertEqual(len(first), 11)
        self.assertEqual(int(second[-5:]), int(first[-5:]) + 1)

    def test_a_number_an_imported_training_already_has_is_skipped(self):
        self.add_training(f"CONF{self.year}10001")                        # the counter's first number
        self.add_training(f"CONF{self.year}10002")
        self.assertEqual(self.add_training(), f"CONF{self.year}10003")

    def test_it_gives_up_rather_than_reuse_an_id(self):
        for n in range(3):
            self.add_training(f"CONF{self.year}{10001 + n}")
        with patch.object(conference_id, "MAX_SKIPS", 3), self.assertRaises(RuntimeError):
            with self.w.alpha_engine.begin() as conn:
                conference_id.new_conference_uid(conn)

    def test_an_explicit_id_is_kept(self):
        conference = Conference(conferenceUid="CONF-KEEP", company="Samsung India")
        self.db.add(conference)
        self.db.commit()
        self.assertEqual(conference.conferenceUid, "CONF-KEEP")


class SignedJoinCodes(unittest.TestCase):
    def test_round_trip(self):
        code = join_code.make(ALPHA, OPEN)
        self.assertRegex(code, rf"^{OPEN}\.[A-Z2-7]{{16}}$")
        self.assertEqual(join_code.verify(ALPHA, code), OPEN)

    def test_an_edited_or_foreign_code_is_rejected(self):
        code = join_code.make(ALPHA, OPEN)
        body, signature = code.rsplit(".", 1)
        flipped = ("A" if signature[0] != "A" else "B") + signature[1:]
        for bad in (f"{body}.{flipped}", f"{uid('S_S1')}.{signature}", code + "X", "." + signature, "", "x" * 200):
            with self.subTest(bad=bad[:40]):
                self.assertIsNone(join_code.verify(ALPHA, bad))
        self.assertIsNone(join_code.verify(BETA, code))                     # another tenant

    def test_unsigned_codes_only_during_the_grace_period(self):
        with patch.object(join_code.settings, "JOIN_CODE_LEGACY_UNTIL", "2026-10-31"), \
                patch("app.utils.join_code.ist_now", return_value=datetime(2026, 10, 31, 23, 59)):
            self.assertEqual(join_code.verify(ALPHA, OPEN), OPEN)
        with patch.object(join_code.settings, "JOIN_CODE_LEGACY_UNTIL", "2026-10-31"), \
                patch("app.utils.join_code.ist_now", return_value=datetime(2026, 11, 1, 0, 1)):
            self.assertIsNone(join_code.verify(ALPHA, OPEN))
        with patch.object(join_code.settings, "JOIN_CODE_LEGACY_UNTIL", ""):
            self.assertIsNone(join_code.verify(ALPHA, OPEN))


class JoinThroughTheApi(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        db = self.w.tenant_db[ALPHA]
        db.query(Conference).filter_by(conferenceUid=OPEN).update({"status": "Approved", "conferenceDate": "2099-01-01"})
        db.commit()
        signed_only = patch.object(join_code.settings, "JOIN_CODE_LEGACY_UNTIL", "")
        signed_only.start()
        self.addCleanup(signed_only.stop)

    def preview(self, code, tenant=ALPHA):
        return self.w.client.get(f"/sessions/join/{code}", headers={"X-Tenant-ID": tenant})

    def test_a_signed_code_shows_the_training(self):
        response = self.preview(join_code.make(ALPHA, OPEN))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["conferenceUid"], OPEN)

    def test_a_guessed_id_or_edited_code_reveals_nothing(self):
        code = join_code.make(ALPHA, OPEN)
        for bad in (OPEN, uid("S_DEL"), code[:-1] + ("A" if code[-1] != "A" else "B"), "CONF2600001"):
            with self.subTest(bad=bad):
                response = self.preview(bad)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("Training", response.text.replace("training session code", ""))

    def test_changing_the_tenant_header_does_not_cross_tenants(self):
        self.assertEqual(self.preview(join_code.make(ALPHA, OPEN), tenant=BETA).status_code, 404)
        self.assertEqual(self.preview(join_code.make(BETA, uid("B_N1")), tenant=ALPHA).status_code, 404)

    def test_joining_needs_the_signed_code(self):
        phone = self.w.tenant_db[ALPHA].query(Trainee).filter_by(traineeUid="TR-OTHER-TRAINER").one().phone
        headers = {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=ALPHA, role='trainee')}"}
        self.assertEqual(self.w.client.post(f"/sessions/join/{OPEN}", headers=headers).status_code, 404)
        response = self.w.client.post(f"/sessions/join/{join_code.make(ALPHA, OPEN)}", headers=headers)
        self.assertEqual(response.status_code, 200, response.text)
        # a trainee of another tenant can't use this tenant's code
        beta_headers = {"Authorization": f"Bearer {create_access_token(subject=str(phone), tenant_id=BETA, role='trainee')}"}
        self.assertIn(self.w.client.post(f"/sessions/join/{join_code.make(ALPHA, OPEN)}", headers=beta_headers).status_code,
                      (401, 404))

    def test_only_the_trainings_trainer_gets_its_code(self):
        response = self.w.client.get(f"/admin/trainings/{OPEN}/join-code", headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(join_code.verify(ALPHA, response.json()["joinCode"]), OPEN)
        self.assertEqual(response.json()["tenantId"], ALPHA)  # the company the QR link names
        self.assertEqual(self.w.client.get(f"/admin/trainings/{OPEN}/join-code", headers=self.w.headers("trainer2")).status_code, 404)
        self.assertEqual(self.w.client.get(f"/admin/trainings/{OPEN}/join-code").status_code, 401)


if __name__ == "__main__":
    unittest.main()
