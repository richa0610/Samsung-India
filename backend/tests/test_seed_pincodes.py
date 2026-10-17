"""scripts/seed_pincodes.py - a seeded post office gets the directory's own ID style: PUI + its row id
(at least 3 digits, never cut short) + its pincode, e.g. PUI016515571; and the directory's bookkeeping
values (user, 2026-10-16)."""

import unittest

from scripts import seed_pincodes as script


class ThePincodeUid(unittest.TestCase):
    def test_pui_then_the_row_id_then_the_pincode(self):
        self.assertEqual(script.pincode_uid(16, "515571"), "PUI016515571")
        self.assertEqual(script.pincode_uid(1234, "534176"), "PUI1234534176")   # a long id is never cut

    def test_rows_are_filled_like_the_directory_s_own(self):
        self.assertEqual(script.SEEDED_BY, "System")
        self.assertEqual(
            script.BOOKKEEPING,
            {"isRead": "Yes", "status": "Approved", "remarks": "Verified", "securityDetails": "Secured", "masterRemarks": "Updated"},
        )
