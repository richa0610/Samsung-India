"""The public training ID format (app/utils/conference_id.py) and signed QR join codes
(app/utils/join_code.py): guessing or editing an ID, or changing the tenant, reveals nothing."""

import re
import unittest
from datetime import datetime
from unittest.mock import patch

from app.core.security import create_access_token
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.utils import conference_id, join_code
from tests.tenant_fixtures import ALPHA, BETA, TenantWorld, uid

OPEN = uid("S_N1")  # trainer1's training in ALPHA


class ConferenceIdFormat(unittest.TestCase):
    def test_the_format(self):
        with patch("app.utils.conference_id.ist_now", return_value=datetime(2026, 9, 30, 12, 0)):
            value = conference_id.candidate("Samsung India", "trainer1")
        self.assertRegex(value, r"^CONF26\d{8}$")
        self.assertEqual(len(value), 14)

    def test_company_and_trainer_codes_are_stable_opaque_and_not_the_names(self):
        a = conference_id.opaque_code("company", "Samsung India")
        self.assertEqual(a, conference_id.opaque_code("company", "  samsung india "))  # spelling-insensitive
        self.assertRegex(a, r"^\d{2}$")
        codes = {conference_id.opaque_code("company", f"Company {n}") for n in range(200)}
        self.assertGreater(len(codes), 50)                                     # spread over 00-99

    def test_different_secrets_give_different_codes(self):
        names = [f"Company {n}" for n in range(30)]
        original = [conference_id.opaque_code("company", n) for n in names]
        with patch.object(conference_id, "_KEY", b"another-server-secret"):
            other = [conference_id.opaque_code("company", n) for n in names]
        self.assertNotEqual(original, other)


class ConferenceIdAllocation(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.db = self.w.tenant_db[ALPHA]

    def test_a_taken_id_is_skipped(self):
        taken = conference_id.candidate("Samsung India", "trainer1")
        self.db.add(Conference(conferenceUid=taken, company="Samsung India", trainerEmployeeId="trainer1"))
        self.db.commit()
        draws = iter([int(taken[-4:]), int(taken[-4:]), 1234])
        with patch("app.utils.conference_id.secrets.randbelow", lambda _n: next(draws)), \
                patch("app.utils.conference_id.ist_now", return_value=datetime.now()):
            with self.w.alpha_engine.connect() as conn:
                fresh = conference_id.new_conference_uid(conn, "Samsung India", "trainer1")
        self.assertNotEqual(fresh, taken)
        self.assertTrue(fresh.endswith("1234"))

    def test_it_gives_up_rather_than_reuse_an_id(self):
        taken = conference_id.candidate("Samsung India", "trainer1")
        self.db.add(Conference(conferenceUid=taken, company="Samsung India", trainerEmployeeId="trainer1"))
        self.db.commit()
        with patch("app.utils.conference_id.secrets.randbelow", lambda _n: int(taken[-4:])), \
                patch("app.utils.conference_id.ist_now", return_value=datetime.now()):
            with self.w.alpha_engine.connect() as conn, self.assertRaises(RuntimeError):
                conference_id.new_conference_uid(conn, "Samsung India", "trainer1")

    def test_new_trainings_get_the_new_format(self):
        conference = Conference(company="Samsung India", trainerEmployeeId="trainer1", conferenceDate="2026-10-05")
        self.db.add(conference)
        self.db.commit()
        self.assertRegex(conference.conferenceUid, r"^CONF\d{10}$")
        self.assertEqual(conference.conferenceUid[6:8], conference_id.opaque_code("company", "Samsung India"))
        self.assertEqual(conference.conferenceUid[8:10], conference_id.opaque_code("trainer", "trainer1"))

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
        self.assertEqual(self.w.client.get(f"/admin/trainings/{OPEN}/join-code", headers=self.w.headers("trainer2")).status_code, 404)
        self.assertEqual(self.w.client.get(f"/admin/trainings/{OPEN}/join-code").status_code, 401)


if __name__ == "__main__":
    unittest.main()
