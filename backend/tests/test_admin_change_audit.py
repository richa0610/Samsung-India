"""The `admin` table's own audit columns (services/admin_change_audit.py, user 2026-10-16): an
admin-table account saving its profile, photo or Aadhaar is stamped with who changed it and from
where, in the other system's wording - never with its password hash or its login token. `remarks`
(the approver's note) stays as it was, and agency trainers - whose table has no such columns - save
exactly as before.

Synthetic TenantWorld (in-memory SQLite, temporary media folder) only.
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from app.core.request_context import token_fingerprint
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.utils import user_agent
from tests.test_closeout_security import PDF, MediaTestCase

CHROME_ON_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
CALLER_IP = "203.0.113.7"
JPEG = ("photo.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * 32, "image/jpeg")
NOW_IST = datetime(2026, 10, 16, 15, 24, 21)


class AdminChangeAuditTestCase(MediaTestCase):
    def setUp(self):
        super().setUp()
        self.admin_id = self.w.admins["adm_trainer"].id
        self.w.common.query(Admin).filter(Admin.id == self.admin_id).update({"remarks": "Approved by HQ"})
        self.w.common.commit()
        clock = patch("app.services.admin_change_audit.ist_now", return_value=NOW_IST)
        clock.start()
        self.addCleanup(clock.stop)
        self.headers = {**self.w.headers("adm_trainer"), "User-Agent": CHROME_ON_WINDOWS, "X-Forwarded-For": CALLER_IP}
        self.raw_token = self.headers["Authorization"].removeprefix("Bearer ")

    def patch_profile(self, body):
        response = self.w.client.patch("/admin/profile", json=body, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)

    def upload(self, path, file):
        response = self.w.client.post(path, files={"file": file}, headers=self.headers)
        self.assertEqual(response.status_code, 200, response.text)

    def row(self) -> Admin:
        self.w.common.expire_all()
        return self.w.common.get(Admin, self.admin_id)


class AProfileSaveIsStamped(AdminChangeAuditTestCase):
    def test_security_details_name_the_browser_system_agent_caller_and_time(self):
        self.patch_profile({"name": "Renamed Admin"})
        self.assertEqual(
            self.row().securityDetails,
            f"Your browser: Google Chrome 124.0.0.0 -->-- on windows reports -->-- {CHROME_ON_WINDOWS}"
            f" -->-- REMOTE_ADDR {CALLER_IP} -->-- 16-10-2026 03:24:21 PM",
        )

    def test_master_remarks_say_who_with_which_session_and_the_row_as_saved(self):
        self.patch_profile({"name": "Renamed Admin", "city": "Patna", "facebookUsername": "https://facebook.com/x"})
        line = self.row().masterRemarks
        self.assertTrue(
            line.startswith(
                f"Admin updated by Renamed Admin(adm_trainer), With token {token_fingerprint(self.raw_token)}"
                " where Keys details are, Now name is: Renamed Admin, email is: , "
            ),
            line,
        )
        for part in ("localCity is: Patna", "password is: not changed", "remarks is: Approved by HQ",
                     "facebook is: https://facebook.com/x"):
            self.assertIn(part, line)
        self.assertTrue(line.endswith("github is: "), line)

    def test_who_and_when_are_set_and_the_approvers_remarks_are_kept(self):
        self.patch_profile({"name": "Renamed Admin"})
        row = self.row()
        self.assertEqual((row.updatedBy, row.remarks), ("adm_trainer", "Approved by HQ"))
        self.assertIsNotNone(row.updationOn)


class NoSecretsAreWritten(AdminChangeAuditTestCase):
    def test_a_password_change_is_noted_but_neither_the_hash_nor_the_token_is_stored(self):
        self.patch_profile({"password": "New-Secret-Pass-9"})
        row = self.row()
        self.assertIn("password is: changed", row.masterRemarks)
        for column in (row.masterRemarks, row.securityDetails):
            for secret in (row.password, "New-Secret-Pass-9", self.raw_token):
                self.assertNotIn(secret, column)


class UploadsAreStampedToo(AdminChangeAuditTestCase):
    def test_a_photo_upload_lists_the_new_photo(self):
        self.upload("/admin/profile/photo", JPEG)
        row = self.row()
        self.assertIn(f"profilePhoto is: {row.profilePhoto}", row.masterRemarks)
        self.assertTrue(row.securityDetails.startswith("Your browser: Google Chrome 124.0.0.0"), row.securityDetails)

    def test_an_aadhaar_upload_lists_the_new_document(self):
        self.upload("/admin/profile/aadhar", PDF)
        row = self.row()
        self.assertIn(f"aadharImage is: {row.aadharImage}", row.masterRemarks)


class AgencyTrainersSaveAsBefore(AdminChangeAuditTestCase):
    def test_an_agency_trainer_profile_save_still_works_and_touches_no_admin_row(self):
        response = self.w.client.patch("/admin/profile", json={"name": "Agency Renamed"}, headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        self.alpha.expire_all()
        self.assertEqual(self.alpha.query(AgencyTeam).filter_by(username="trainer1").one().name, "Agency Renamed")
        self.assertIsNone(self.row().masterRemarks)


class BrowserAndSystem(unittest.TestCase):
    def test_common_agents(self):
        cases = {
            CHROME_ON_WINDOWS: ("Google Chrome 124.0.0.0", "windows"),
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 "
            "Safari/537.36 Edg/124.0.2478.80": ("Microsoft Edge 124.0.2478.80", "windows"),
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 "
            "Chrome/121.0.0.0 Mobile Safari/537.36": ("Samsung Internet 25.0", "android"),
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.4 Mobile/15E148 Safari/604.1": ("Safari 17.4", "ios"),
            "okhttp/4.12.0": ("okhttp 4.12.0", "unknown"),  # the Android app itself
            "": ("Unknown", "unknown"),
        }
        for agent, expected in cases.items():
            with self.subTest(agent=agent):
                self.assertEqual(user_agent.describe(agent), expected)

    def test_no_agent_at_all(self):
        self.assertEqual(user_agent.describe(None), ("Unknown", "unknown"))
