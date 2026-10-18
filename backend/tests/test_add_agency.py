"""scripts/add_agency.py - registers one company in the shared `agency` table from a JSON file:
a preview writes nothing; --apply adds it Pending with a fresh agencyUid and saves an undo file;
a company already registered (any spelling of its name, or its email / phone) or a malformed
file stops it before anything is written; --undo removes exactly that row. The table is never
part of what app startup creates or alters. Synthetic in-memory SQLite only."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import CommonBase, TenantBase
from app.models.agency import Agency, AgencyBase
from scripts import add_agency as script

DEMO_FILE = Path(script.__file__).resolve().parent / "agency.demo.json"


class AddAgency(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        AgencyBase.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.db.add(Agency(agencyUid="AG2400001", companyName="Existing  Agency Pvt Ltd", name="Someone",
                           email="hello@existing.example.test", phone=9876543210, status="Approved"))
        self.db.commit()
        self.tmp = tempfile.TemporaryDirectory()
        backups = patch.object(script, "BACKUP_DIR", Path(self.tmp.name))
        backups.start()
        self.addCleanup(backups.stop)

    def tearDown(self):
        self.tmp.cleanup()
        self.db.close()

    def file(self, **agency):
        path = Path(self.tmp.name) / "agency.json"
        base = {"companyName": "New Co", "name": "Asha", "email": "asha@newco.example.test", "phone": "9123456789"}
        path.write_text(json.dumps({"agency": {**base, **agency}}), encoding="utf-8")
        return path

    def preview(self, path):
        with contextlib.redirect_stdout(io.StringIO()):
            return script.preview(self.db, path)

    def rows(self):
        return self.db.query(Agency).count()

    def test_the_demo_file_previews_cleanly_and_nothing_is_written(self):
        agency, problems = self.preview(DEMO_FILE)
        self.assertEqual(problems, [])
        self.assertTrue(agency["companyName"].startswith("DEMO "))
        self.assertTrue(agency["email"].endswith("@example.test"))
        self.assertEqual(self.rows(), 1)

    def test_apply_adds_it_pending_with_a_fresh_uid_and_an_undo_file(self):
        agency, _ = self.preview(self.file(website="https://newco.example.test", localPinCode="411001"))
        uid, backup = script.apply(self.db, agency)
        row = self.db.query(Agency).filter_by(agencyUid=uid).one()
        self.assertRegex(uid, r"^AGY\d{7}$")
        self.assertEqual((row.companyName, row.phone, row.status, row.updatedBy), ("New Co", 9123456789, "Pending", script.ADDED_BY))
        self.assertEqual(json.loads(backup.read_text(encoding="utf-8")), {"agencyUid": uid, "companyName": "New Co"})

    def test_an_already_registered_company_email_or_phone_stops_it(self):
        for clash in ({"companyName": " existing agency pvt ltd "}, {"email": "HELLO@existing.example.test"}, {"phone": "9876543210"}):
            with self.subTest(clash=clash):
                _, problems = self.preview(self.file(**clash))
                self.assertEqual(len(problems), 1)
                self.assertIn("AG2400001", problems[0])

    def test_a_malformed_file_stops_it(self):
        for broken, reason in (
            ({"phone": "12345"}, "phone"),
            ({"email": "not-an-email"}, "email"),
            ({"localPinCode": "41100"}, "localPinCode"),
            ({"companyName": "  "}, "companyName is required"),
            ({"password": "x"}, "Unknown field(s): password"),
        ):
            with self.subTest(broken=broken):
                _, problems = self.preview(self.file(**broken))
                self.assertTrue(any(reason in problem for problem in problems), problems)

    def test_a_template_value_left_unfilled_stops_it(self):
        _, problems = self.preview(self.file(localCity="<city>"))
        self.assertEqual(problems, ["localCity still holds the placeholder <city>"])

    def test_the_samsung_file_passes_every_check_and_names_its_tenants_company(self):
        # Filled in and registered on 2026-10-18 (AGY2687355); its companyName must stay exactly the
        # `tenants` row's company_name, the only link between the two.
        agency, problems = self.preview(DEMO_FILE.with_name("agency.samsung.json"))
        self.assertEqual(problems, [])
        self.assertEqual(agency["companyName"], "Samsung India")
        self.assertEqual(self.rows(), 1)

    def test_undo_removes_exactly_that_row_and_only_while_it_is_still_this_scripts(self):
        agency, _ = self.preview(self.file())
        uid, backup = script.apply(self.db, agency)
        self.assertEqual(script.undo(self.db, backup), 1)
        self.assertEqual([row.agencyUid for row in self.db.query(Agency)], ["AG2400001"])

        uid, backup = script.apply(self.db, agency)
        self.db.query(Agency).filter_by(agencyUid=uid).update({"updatedBy": "another-system-admin"})
        self.db.commit()
        self.assertEqual(script.undo(self.db, backup), 0)  # someone else has taken it over - left alone
        self.assertEqual(self.rows(), 2)

    def test_app_startup_never_creates_or_alters_the_agency_table(self):
        self.assertNotIn("agency", CommonBase.metadata.tables)
        self.assertNotIn("agency", TenantBase.metadata.tables)
        self.assertIs(Agency.__table__.metadata, AgencyBase.metadata)
