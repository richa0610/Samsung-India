"""scripts/add_master_options.py - adds categories and their options to the master list from a
JSON file: a missing category is created Approved, only missing options are added, never a
duplicate of an existing one (any spelling, any status); a category that isn't Approved, is there
twice or is marked differently stops the run; --undo removes exactly what it added."""

import contextlib
import io
import itertools
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models.category import Category, SubCategory
from scripts import add_master_options as script


class AddMasterOptions(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.db.add_all([
            Category(categoryUid="CA-AUD", name="Audience", visibleOnWeb="Conference", status="Approved"),
            Category(categoryUid="CA-OLD", name="Retired", visibleOnWeb="No", status="Rejected"),
            SubCategory(subCategoryUid="S-EXISTING", categoryUid="CA-AUD", subCategory="sec  plan", status="Pending"),
            SubCategory(subCategoryUid="S-OTHER", categoryUid="CA-OTHER", subCategory="SEC", status="Approved"),  # another category
        ])
        self.db.commit()
        counter = itertools.count(1)
        self._uid = patch("app.models.uid_events.next_uid", side_effect=lambda _conn, prefix: f"{prefix}26{next(counter):05d}")
        self._uid.start()
        self.tmp = tempfile.TemporaryDirectory()
        self._backups = patch.object(script, "BACKUP_DIR", Path(self.tmp.name))
        self._backups.start()

    def tearDown(self):
        self._uid.stop()
        self._backups.stop()
        self.tmp.cleanup()
        self.db.close()

    def run_preview(self, *categories):
        path = Path(self.tmp.name) / "options.json"
        path.write_text(json.dumps({"_comment": "x", "categories": list(categories)}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            return script.preview(self.db, script.load_plan(path))

    def options(self, category_uid):
        return sorted((row.subCategory, row.status) for row in self.db.query(SubCategory).filter_by(categoryUid=category_uid))

    def test_the_preview_lists_only_what_is_missing_and_writes_nothing(self):
        steps, problems = self.run_preview(
            {"name": " audience ", "visibleOnWeb": "conference", "options": ["SEC Plan", " SEC ", "SEC", "OT  SEC"]},
            {"name": "North", "visibleOnWeb": "Zone", "options": ["North 1"]},
        )
        self.assertEqual(problems, [])
        self.assertEqual([(s.name, s.category_uid, s.options) for s in steps], [
            ("audience", "CA-AUD", ["SEC", "OT SEC"]),  # "SEC Plan" is the existing "sec  plan"; "SEC" once
            ("North", None, ["North 1"]),               # a category to create
        ])
        self.assertEqual(self.db.query(Category).count(), 2)
        self.assertEqual(self.options("CA-AUD"), [("sec  plan", "Pending")])

    def test_apply_creates_the_category_and_adds_the_options_approved_with_who_and_why(self):
        steps, _ = self.run_preview(
            {"name": "Audience", "visibleOnWeb": "Conference", "options": ["SEC Plan", "SEC"]},
            {"name": "North", "visibleOnWeb": "Zone", "options": ["North 1", "North 2"]},
        )
        backup = json.loads(script.apply(self.db, steps, "samsung").read_text())
        north = self.db.query(Category).filter_by(name="North").one()
        self.assertEqual((north.categoryUid, north.visibleOnWeb, north.status, north.updatedBy), ("CAT2600001", "Zone", "Approved", script.ADDED_BY))
        self.assertEqual(self.options("CA-AUD"), [("SEC", "Approved"), ("sec  plan", "Pending")])
        self.assertEqual(self.options("CAT2600001"), [("North 1", "Approved"), ("North 2", "Approved")])
        self.assertEqual(backup, {"tenant": "samsung", "categories": ["CAT2600001"], "subcategories": ["SUB2600002", "SUB2600003", "SUB2600004"]})
        self.assertEqual(self.options("CA-OTHER"), [("SEC", "Approved")])

    def test_an_unapproved_duplicated_or_differently_marked_category_stops_the_run(self):
        self.db.add(Category(categoryUid="CA-TWICE", name="Twice", visibleOnWeb="No", status="Approved"))
        self.db.add(Category(categoryUid="CA-TWICE2", name="twice", visibleOnWeb="No", status="Approved"))
        self.db.commit()
        _, problems = self.run_preview(
            {"name": "Retired", "options": ["X"]},                               # Rejected
            {"name": "Twice", "options": ["X"]},                                 # two rows
            {"name": "Audience", "visibleOnWeb": "Zone", "options": ["X"]},      # marked Conference
            {"name": "Audience", "visibleOnWeb": "Conference", "options": ["SEC"]},
        )
        self.assertEqual(len(problems), 3)

    def test_undo_removes_exactly_what_was_added_but_keeps_a_category_that_gained_an_option(self):
        steps, _ = self.run_preview(
            {"name": "Audience", "visibleOnWeb": "Conference", "options": ["SEC"]},
            {"name": "North", "visibleOnWeb": "Zone", "options": ["North 1"]},
            {"name": "South", "visibleOnWeb": "Zone", "options": ["South 1"]},
        )
        backup = script.apply(self.db, steps, "samsung")
        south = self.db.query(Category).filter_by(name="South").one().categoryUid
        self.db.add(SubCategory(subCategoryUid="S-WEBSITE", categoryUid=south, subCategory="South 9", status="Approved"))  # added since
        self.db.commit()
        with self.assertRaises(SystemExit):
            script.undo(self.db, backup, "other-tenant")
        self.assertEqual(script.undo(self.db, backup, "samsung"), (3, 1, [south]))
        self.assertEqual(sorted(c.name for c in self.db.query(Category)), ["Audience", "Retired", "South"])
        self.assertEqual(self.options("CA-AUD"), [("sec  plan", "Pending")])
        self.assertEqual(self.options(south), [("South 9", "Approved")])


if __name__ == "__main__":
    unittest.main()
