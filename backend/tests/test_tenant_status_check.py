"""TenantConnectionManager re-checks, on every request, that the tenant is still active (cached for a
short while). If the shared Common DB can't be read for that check, the request carries on with
what's already running - an unreadable registry must not take down a healthy tenant - and the
failure is logged with its traceback. A tenant known to be suspended is always refused."""

import unittest
from unittest.mock import MagicMock

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.tenant import TenantConnectionManager
from app.models.common.tenant_registry import Tenant


def registry_with(status: str):
    db = sessionmaker(bind=create_engine("sqlite://", poolclass=StaticPool))()
    Tenant.__table__.create(db.get_bind())
    db.add(Tenant(tenant_uid="GAMMA", company_name="Gamma", database_host="127.0.0.1", database_port=1,
                  database_name="gamma", database_username="u", database_password="p", status=status))
    db.commit()
    return db


def unreachable_registry():
    db = MagicMock()
    db.query.side_effect = OperationalError("SELECT ... FROM tenants", {}, Exception("Common DB is down"))
    return db


class TenantStatusRecheck(unittest.TestCase):
    def setUp(self):
        self.manager = TenantConnectionManager()

    def test_an_unreadable_registry_lets_the_request_through_and_logs_the_failure(self):
        with self.assertLogs("tenant_manager", level="ERROR") as logs:
            self.manager._check_tenant_active("GAMMA", unreachable_registry())   # no exception
        [record] = logs.records
        self.assertIn("Failed to re-check tenant status for 'GAMMA'", record.getMessage())
        self.assertIsNotNone(record.exc_info)   # logged with its traceback
        self.assertIsNone(self.manager._status_cache.get("GAMMA"))   # no verdict cached from a failed read

    def test_a_suspended_tenant_is_refused(self):
        with self.assertRaises(HTTPException) as caught:
            self.manager._check_tenant_active("GAMMA", registry_with("suspended"))
        self.assertEqual((caught.exception.status_code, caught.exception.detail),
                         (403, "Tenant account is suspended or inactive"))

    def test_a_known_suspension_holds_even_when_the_registry_then_goes_down(self):
        with self.assertRaises(HTTPException):
            self.manager._check_tenant_active("GAMMA", registry_with("suspended"))
        with self.assertRaises(HTTPException) as caught:
            self.manager._check_tenant_active("GAMMA", unreachable_registry())   # answered from the cache
        self.assertEqual(caught.exception.status_code, 403)

    def test_an_active_tenant_passes(self):
        self.manager._check_tenant_active("GAMMA", registry_with("active"))
        self.assertEqual(self.manager._status_cache.get("GAMMA"), "active")


if __name__ == "__main__":
    unittest.main()
