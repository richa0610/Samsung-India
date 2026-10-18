"""scripts/align_company_ids.py - a training's and a trainee's company as the other system stores it
(user, 2026-10-17/18): the company's agency ID from the shared registry, not its name. A stored name
becomes the ID registered under it (any spelling); a trainee with no company gets the tenant's; an ID
already stored is left alone, so a second run changes nothing; a name nobody registered, and a
training with no company, are reported, never changed. It keeps an undo file.

In-memory SQLite only."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import CommonBase, TenantBase
from app.models.agency import Agency, AgencyBase
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.trainee import Trainee
from scripts import align_company_ids as script

SAMSUNG = "AGY2600001"
DEMO = "AGY2626653"
TENANT = "alpha"


def _session(*metadatas):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    for metadata in metadatas:
        metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


class AlignCompanyIds(unittest.TestCase):
    def setUp(self):
        engine, self.db = _session(TenantBase.metadata)
        common_engine, self.common_db = _session(CommonBase.metadata, AgencyBase.metadata)
        for e, s in ((engine, self.db), (common_engine, self.common_db)):
            self.addCleanup(e.dispose)
            self.addCleanup(s.close)
        uid = patch("app.models.uid_events.next_uid", return_value=None)
        uid.start()
        self.addCleanup(uid.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        backups = patch.object(script, "BACKUP_DIR", Path(tmp.name))
        backups.start()
        self.addCleanup(backups.stop)

        self.common_db.add_all([
            Agency(agencyUid=SAMSUNG, companyName="Samsung India"),
            Agency(agencyUid=DEMO, companyName="DEMO Bharat Electronics Pvt Ltd"),
            Tenant(tenant_uid=TENANT, company_name="Samsung India", agency_uid=SAMSUNG, database_host="h",
                   database_name="tops_alpha", database_username="u", database_password="p"),
        ])
        self.common_db.commit()
        for uid_, company in (
            ("CONF-NAME", "Samsung India"),
            ("CONF-SPELLED", "  samsung   INDIA "),         # same company, another spelling
            ("CONF-ID", DEMO),                              # written since the change
            ("CONF-UNKNOWN", "Acme Retail"),                # nobody registered it
            ("CONF-NONE", None),                            # a training with no company: only reported
        ):
            self.db.add(Conference(conferenceUid=uid_, company=company))
        for n, company in enumerate(("Samsung India", None, "  ", SAMSUNG), start=1):
            self.db.add(Trainee(traineeUid=f"TR-{n}", name=f"Person {n}", email=f"p{n}@example.test", phone=9_000_000_000 + n,
                                company=company))
        self.db.commit()

    def companies(self, model, key):
        self.db.expire_all()
        return {getattr(row, key): row.company for row in self.db.query(model)}

    def plan(self):
        return script.make_plan(self.db, self.common_db, TENANT)

    def test_the_preview_maps_names_fills_trainees_without_one_and_writes_nothing(self):
        before = (self.companies(Conference, "conferenceUid"), self.companies(Trainee, "traineeUid"))
        plan = self.plan()
        self.assertEqual(
            sorted((c.table, c.before or "", c.after) for c in plan.changes),
            [("conference", "  samsung   INDIA ", SAMSUNG), ("conference", "Samsung India", SAMSUNG),
             ("trainee", "", SAMSUNG), ("trainee", "  ", SAMSUNG), ("trainee", "Samsung India", SAMSUNG)],
        )
        conference, trainee = plan.tables["conference"], plan.tables["trainee"]
        self.assertEqual((conference.already_ids, conference.blank, conference.not_registered), (1, 1, {"Acme Retail": 1}))
        self.assertEqual((trainee.already_ids, trainee.blank, trainee.not_registered), (1, 0, {}))
        self.assertEqual((self.companies(Conference, "conferenceUid"), self.companies(Trainee, "traineeUid")), before)

    def test_apply_converts_them_and_a_second_run_changes_nothing(self):
        done, _ = script.apply(self.db, self.plan(), TENANT)
        self.assertEqual(done, 5)
        self.assertEqual(self.companies(Conference, "conferenceUid"), {
            "CONF-NAME": SAMSUNG, "CONF-SPELLED": SAMSUNG, "CONF-ID": DEMO, "CONF-UNKNOWN": "Acme Retail", "CONF-NONE": None,
        })
        self.assertEqual(set(self.companies(Trainee, "traineeUid").values()), {SAMSUNG})
        again = self.plan()
        self.assertEqual(again.changes, [])
        self.assertEqual((again.tables["conference"].already_ids, again.tables["trainee"].already_ids), (3, 4))

    def test_undo_puts_back_exactly_what_it_changed(self):
        before = (self.companies(Conference, "conferenceUid"), self.companies(Trainee, "traineeUid"))
        _, backup = script.apply(self.db, self.plan(), TENANT)
        self.assertEqual(script.undo(self.db, backup, TENANT), (5, 5))
        self.assertEqual((self.companies(Conference, "conferenceUid"), self.companies(Trainee, "traineeUid")), before)

    def test_undo_leaves_a_value_changed_since(self):
        _, backup = script.apply(self.db, self.plan(), TENANT)
        self.db.query(Conference).filter_by(conferenceUid="CONF-NAME").update({"company": DEMO})
        self.db.commit()
        self.assertEqual(script.undo(self.db, backup, TENANT), (4, 5))
        self.assertEqual(self.companies(Conference, "conferenceUid")["CONF-NAME"], DEMO)

    def test_undo_refuses_another_tenants_file(self):
        _, backup = script.apply(self.db, self.plan(), TENANT)
        with self.assertRaises(SystemExit):
            script.undo(self.db, backup, "beta")
        self.assertEqual(self.companies(Conference, "conferenceUid")["CONF-NAME"], SAMSUNG)

    def test_without_a_registered_tenant_trainees_without_a_company_are_only_reported(self):
        self.common_db.query(Tenant).delete()
        self.common_db.commit()
        trainee = self.plan().tables["trainee"]
        self.assertEqual(trainee.blank, 2)


if __name__ == "__main__":
    unittest.main()
