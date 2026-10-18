"""Company codes (user, 2026-10-18): before signing in, the app asks for the company code - the
tenant's ID, in any letter case - and sends it as X-Tenant-ID.

  - GET /tenants/lookup?code= names an active company (its ID and name); an unknown code and a
    suspended company get the same 404, so the lookup reveals nothing more.
  - GET /tenants/current names the company a signed-in account's token was issued for.
  - Whatever case the code is sent in, the request is served by the registry's own spelling of it:
    sign-in works (an admin's grant names that spelling), and the token carries it.

Synthetic TenantWorld (in-memory SQLite) only - see tests/tenant_fixtures.py."""

import unittest
from unittest.mock import patch

from jose import jwt
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.database.tenant import TenantConnectionManager
from app.models.common.tenant_registry import Tenant
from app.repositories import tenant_repository
from tests.tenant_fixtures import ALPHA, PASSWORD, TenantWorld

TRAINEE_PHONE = "9000000001"  # the first seeded trainee, in ALPHA


def token_tenant(response) -> str:
    return jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])["tenant_id"]


class CompanyCodes(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)

    def lookup(self, code):
        return self.w.client.get("/tenants/lookup", params={"code": code})

    def test_a_code_in_any_letter_case_names_the_company(self):
        for code in (ALPHA, ALPHA.lower(), f"  {ALPHA.title()} "):
            with self.subTest(code=code):
                response = self.lookup(code)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), {"tenantId": ALPHA, "companyName": "Samsung India"})

    def test_an_unknown_code_and_a_suspended_company_get_the_same_answer(self):
        self.w.common.query(Tenant).filter(Tenant.tenant_uid == ALPHA).update({"status": "suspended"})
        self.w.common.commit()
        for code in (ALPHA, "NOPE"):
            with self.subTest(code=code):
                response = self.lookup(code)
                self.assertEqual((response.status_code, response.json()["detail"]), (404, "Company code not found"))

    def test_a_code_is_required(self):
        self.assertEqual(self.w.client.get("/tenants/lookup").status_code, 422)
        self.assertEqual(self.lookup("").status_code, 422)

    def test_a_signed_in_account_learns_its_company(self):
        response = self.w.client.get("/tenants/current", headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"tenantId": ALPHA, "companyName": "Samsung India"})
        self.assertIn(self.w.client.get("/tenants/current").status_code, (401, 403))

    def test_staff_sign_in_with_a_lower_case_code_lands_in_the_registered_tenant(self):
        response = self.w.client.post("/admin/login", json={"username": "coadmin", "password": PASSWORD},
                                      headers={"X-Tenant-ID": ALPHA.lower()})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(token_tenant(response), ALPHA)



        response = self.w.client.post("/trainees/login", json={"identifier": TRAINEE_PHONE, "password": PASSWORD},
                                      headers={"X-Tenant-ID": f" {ALPHA.lower()} "})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(token_tenant(response), ALPHA)


class CanonicalTenantId(unittest.TestCase):
    """TenantConnectionManager.canonical_uid on its own: the registry's spelling, else the ID as sent."""

    def setUp(self):
        self.w = TenantWorld()
        self.addCleanup(self.w.close)
        self.manager = TenantConnectionManager()

    def test_a_registered_id_comes_back_in_its_own_spelling(self):
        self.assertEqual(self.manager.canonical_uid(" alpha "), ALPHA)

    def test_an_unknown_id_comes_back_as_sent(self):
        self.assertEqual(self.manager.canonical_uid(" Nope "), "Nope")

    def test_the_registry_is_read_once_for_any_number_of_ids(self):
        with patch.object(tenant_repository, "list_uids", wraps=tenant_repository.list_uids) as reads:
            for sent in ("alpha", "ALPHA", "beta", "junk-1", "junk-2"):
                self.manager.canonical_uid(sent)
        self.assertEqual(reads.call_count, 1)

    def test_an_unreadable_registry_leaves_the_id_as_sent(self):
        failing = patch.object(tenant_repository, "list_uids", side_effect=OperationalError("SELECT", {}, Exception("down")))
        with failing, self.assertLogs("tenant_manager", level="ERROR"):
            self.assertEqual(self.manager.canonical_uid("alpha"), "alpha")


if __name__ == "__main__":
    unittest.main()
