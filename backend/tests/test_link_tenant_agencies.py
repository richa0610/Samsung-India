"""scripts/link_tenant_agencies.py - fills `tenants.agency_uid` with the agency ID the tenant's
company_name is registered under (any spelling): only an empty one is filled, so a second run changes
nothing; a company not registered yet, or a tenant already linked to another ID, is reported and never
changed. It keeps an undo file.

In-memory SQLite only."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import CommonBase
from app.models.agency import Agency, AgencyBase
from app.models.common.tenant_registry import Tenant
from scripts import link_tenant_agencies as script

SAMSUNG = "AGY2600001"
DEMO = "AGY2626653"


class LinkTenantAgencies(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        CommonBase.metadata.create_all(engine)
        AgencyBase.metadata.create_all(engine)
        self.addCleanup(engine.dispose)
        self.db = sessionmaker(bind=engine)()
        self.addCleanup(self.db.close)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        backups = patch.object(script, "BACKUP_DIR", Path(tmp.name))
        backups.start()
        self.addCleanup(backups.stop)

        self.db.add_all([
            Agency(agencyUid=SAMSUNG, companyName="  samsung   INDIA "),     # registered under another spelling
            Agency(agencyUid=DEMO, companyName="DEMO Bharat Electronics Pvt Ltd"),
        ])
        for uid, company, agency_uid in (
            ("samsung", "Samsung India", None),
            ("demo", "DEMO Bharat Electronics Pvt Ltd", ""),
            ("acme", "Acme Retail", None),                  # nobody registered it
            ("linked", "Samsung India", SAMSUNG),           # already done
            ("other", "Samsung India", "AGY2699999"),       # linked by hand to another ID
        ):
            self.db.add(Tenant(tenant_uid=uid, company_name=company, agency_uid=agency_uid, database_host="h",
                               database_name=f"tops_{uid}", database_username="u", database_password="p"))
        self.db.commit()

    def links(self):
        self.db.expire_all()
        return {t.tenant_uid: t.agency_uid for t in self.db.query(Tenant)}

    def test_the_preview_finds_each_registered_company_and_writes_nothing(self):
        before = self.links()
        plan = script.make_plan(self.db)
        self.assertEqual({c.after: c.before for c in plan.changes}, {SAMSUNG: None, DEMO: ""})
        self.assertEqual({(c.table, c.column) for c in plan.changes}, {("tenants", "agency_uid")})
        self.assertEqual(plan.already_linked, 1)
        self.assertEqual(len(plan.linked_elsewhere), 1)
        self.assertIn("AGY2699999", plan.linked_elsewhere[0])
        self.assertEqual(len(plan.not_registered), 1)
        self.assertIn("acme", plan.not_registered[0])
        self.assertEqual(self.links(), before)

    def test_apply_fills_them_and_a_second_run_changes_nothing(self):
        done, _ = script.apply(self.db, script.make_plan(self.db))
        self.assertEqual(done, 2)
        self.assertEqual(self.links(), {
            "samsung": SAMSUNG, "demo": DEMO, "acme": None, "linked": SAMSUNG, "other": "AGY2699999",
        })
        again = script.make_plan(self.db)
        self.assertEqual((again.changes, again.already_linked, len(again.not_registered)), ([], 3, 1))

    def test_undo_puts_back_exactly_what_it_changed(self):
        before = self.links()
        _, backup = script.apply(self.db, script.make_plan(self.db))
        self.assertEqual(script.undo(self.db, backup), (2, 2))
        self.assertEqual(self.links(), before)

    def test_undo_leaves_a_value_changed_since(self):
        _, backup = script.apply(self.db, script.make_plan(self.db))
        self.db.query(Tenant).filter_by(tenant_uid="demo").update({"agency_uid": "AGY2611111"})
        self.db.commit()
        self.assertEqual(script.undo(self.db, backup), (1, 2))
        self.assertEqual(self.links()["demo"], "AGY2611111")
        self.assertIsNone(self.links()["samsung"])

    def test_undo_refuses_a_file_from_another_script(self):
        _, backup = script.apply(self.db, script.make_plan(self.db))
        saved = json.loads(backup.read_text(encoding="utf-8"))
        backup.write_text(json.dumps({**saved, "tenant": "samsung"}), encoding="utf-8")
        with self.assertRaises(SystemExit):
            script.undo(self.db, backup)
        self.assertEqual(self.links()["demo"], DEMO)


if __name__ == "__main__":
    unittest.main()
