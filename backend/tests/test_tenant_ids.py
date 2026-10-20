"""A new tenant's ID (user, 2026-10-18): TEN_ + its company's first three letters in capitals + _ + YY
+ a running number from 20001 shared by every tenant, e.g. TEN_SAM_2620001. A tenant given an ID keeps
it, and the ones made before ("samsung", "demo") don't count towards the number. The provisioner
registers a tenant sent without an ID under the next one.

In-memory SQLite only."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registers the before_insert hooks
from app.database.connection import CommonBase, TenantBase
from app.models.common.tenant_registry import Tenant
from app.services import tenant_provisioner
from app.utils.uid import tenant_code


class TenantIds(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        CommonBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)
        clock = patch("app.utils.uid.ist_now", return_value=datetime(2026, 10, 18, 10, 0))
        clock.start()
        self.addCleanup(clock.stop)
        for uid, company in (("samsung", "Samsung India"), ("demo", "DEMO Bharat Electronics Pvt Ltd")):
            self.saved(company, uid)

    def saved(self, company, uid=None):
        row = Tenant(tenant_uid=uid, company_name=company, database_host="h", database_name="db",
                     database_username="u", database_password="p")
        self.db.add(row)
        self.db.commit()
        return row.tenant_uid

    def test_the_first_new_tenant_starts_at_20001_and_the_number_runs_across_companies(self):
        self.assertEqual(self.saved("Samsung India"), "TEN_SAM_2620001")
        self.assertEqual(self.saved("DEMO Bharat Electronics Pvt Ltd"), "TEN_DEM_2620002")
        self.assertEqual(self.saved("Samsung India"), "TEN_SAM_2620003")

    def test_the_number_follows_the_highest_one_taken_even_from_an_earlier_year(self):
        self.saved("Acme Retail", "TEN_ACM_2520007")
        self.assertEqual(self.saved("Samsung India"), "TEN_SAM_2620008")

    def test_a_tenant_given_an_id_keeps_it(self):
        self.assertEqual(self.saved("Samsung India", "custom"), "custom")
        self.assertEqual(self.saved("Samsung India"), "TEN_SAM_2620001")

    def test_the_code_is_the_first_three_letters_of_the_name(self):
        self.assertEqual(tenant_code("Samsung India"), "SAM")
        self.assertEqual(tenant_code("  3M India"), "MIN")
        self.assertEqual(tenant_code("LG"), "LG")
        self.assertEqual(tenant_code("123 & Co."), "CO")
        with self.assertRaises(ValueError):
            tenant_code(" 1-2 ")

    def test_the_provisioner_registers_a_tenant_sent_without_an_id_under_the_next_one(self):
        with patch.object(tenant_provisioner, "create_engine", return_value=MagicMock()), \
                patch.object(TenantBase.metadata, "create_all"):
            tenant = tenant_provisioner.provision_new_tenant(
                None, "Samsung India", "h", 3306, "tops_sam", "u", "p", common_db=self.db,
            )
        self.assertEqual(tenant.tenant_uid, "TEN_SAM_2620001")
        self.assertEqual(self.db.query(Tenant).filter_by(company_name="Samsung India").count(), 2)


if __name__ == "__main__":
    unittest.main()
