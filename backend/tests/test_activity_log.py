"""Every logsmaster column an action can fill is filled (user, 2026-10-08) - and no password or
login token ever reaches the table, only a one-way fingerprint of the session."""

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from app.core import rate_limit
from app.core.config import settings
from app.core.security import create_access_token
from app.models.conference import Conference
from app.models.logs_master import LogsMaster
from app.models.trainee import Trainee
from app.services import activity_log_service
from tests.tenant_fixtures import ALPHA, PASSWORD, uid
from tests.test_trainer_authorization import TrainerWorldTestCase

S_N1 = uid("S_N1")
APP_AGENT = "TOPS-App/1.0 (Android 14)"


def fingerprint(token: str) -> str:
    return f"sha256:{hashlib.sha256(token.encode()).hexdigest()[:16]}"


class ActivityLogColumns(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        rate_limit.reset()
        self.addCleanup(rate_limit.reset)

    def row(self, action):
        self.alpha.expire_all()
        return self.alpha.query(LogsMaster).filter(LogsMaster.action == action).order_by(LogsMaster.id.desc()).first()

    def trainee_login(self):
        phone = self.alpha.query(Trainee).filter(Trainee.traineeUid == "TR-S_N1-0").one().phone
        response = self.w.client.post(
            "/trainees/login", json={"identifier": str(phone), "password": PASSWORD},
            headers={"X-Tenant-ID": ALPHA, "X-Forwarded-For": "198.51.100.9", "User-Agent": APP_AGENT},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return phone, response.json()["access_token"]

    def test_a_login_fills_every_column_and_stores_no_password_or_token(self):
        phone, token = self.trainee_login()
        row = self.row("LOGIN")

        self.assertEqual((row.username, row.updatedBy, row.role, row.status), (str(phone), str(phone), "trainee", "Success"))
        self.assertEqual(row.login_IP, "198.51.100.9")
        self.assertEqual(row.logPath, "POST /trainees/login")
        self.assertEqual(row.token, fingerprint(token))
        self.assertIsNotNone(row.updatedOn)
        self.assertIsNotNone(row.loginTime)
        self.assertIsNone(row.logoutTime)   # the session is still open
        details = json.loads(row.securityDetails)
        self.assertEqual(details["userAgent"], APP_AGENT)
        self.assertEqual(details["tokenVersion"], 0)
        self.assertIn("sessionExpires", details)

        stored = [str(getattr(row, column.key)) for column in LogsMaster.__table__.columns]
        self.assertFalse(any(token in value or PASSWORD in value for value in stored))

    def test_a_logout_closes_the_same_session_it_was_opened_by(self):
        _, token = self.trainee_login()
        login = self.row("LOGIN")
        response = self.w.client.post("/trainees/logout", headers={"Authorization": f"Bearer {token}", "User-Agent": APP_AGENT})
        self.assertEqual(response.status_code, 204, response.text)

        logout = self.row("LOGOUT")
        self.assertIsNotNone(logout.logoutTime)
        self.assertEqual((logout.token, logout.loginTime), (login.token, login.loginTime))   # same session
        self.assertEqual(logout.logPath, "POST /trainees/logout")

    def test_the_reason_a_user_typed_lands_in_master_remarks(self):
        self.alpha.query(Conference).filter(Conference.conferenceUid == S_N1).update({"status": "Pending"})
        self.alpha.commit()
        response = self.w.client.post(f"/admin/trainings/{S_N1}/reject", json={"reason": "Venue not confirmed"},
                                      headers=self.w.headers("super"))
        self.assertEqual(response.status_code, 200, response.text)

        row = self.row("REJECT_TRAINING")
        self.assertEqual(row.masterRemarks, "Venue not confirmed")
        self.assertEqual(row.logPath, f"POST /admin/trainings/{S_N1}/reject")
        self.assertIsNotNone(row.loginTime)   # when "super" signed in - from the token they acted with
        self.assertIsNotNone(row.login_IP)

    def test_an_upload_records_the_file_it_stored(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for target in ("app.routers.media.MEDIA_ROOT", "app.core.media.MEDIA_ROOT"):
            self.enterContext(patch(target, root))
        response = self.w.client.post("/admin/trainees/TR-S_N1-0/photo",
                                      files={"file": ("p.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 64, "image/jpeg")},
                                      headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.row("UPLOAD_TRAINEE_PHOTO").filePath, "trainee_photos/TR-S_N1-0.jpg")


class SessionStartForOlderTokens(unittest.TestCase):
    def test_a_token_issued_before_iat_existed_gets_its_expiry_minus_the_lifetime(self):
        expires = datetime(2026, 10, 8, 18, 0, tzinfo=timezone.utc)
        claims = {"exp": int(expires.timestamp())}
        started = expires - timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.assertEqual(activity_log_service._session_start(claims), started.strftime("%Y-%m-%d %H:%M:%S"))

    def test_new_tokens_carry_when_they_were_issued(self):
        claims = activity_log_service._token_claims(create_access_token("someone"))
        self.assertLess(abs(claims["iat"] - datetime.now(timezone.utc).timestamp()), 60)


if __name__ == "__main__":
    unittest.main()
