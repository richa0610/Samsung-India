"""The Add Training pickers come from the master list (user, 2026-10-13): a category is a form
field, its approved subcategories are the options. The zones are categories themselves, marked
visibleOnWeb = "Zone" (East, North, ...), and their subcategories are their regions (East ->
East 1, East 2, ...). A training saves the master's spelling ("North"); "North" and the older
"North Zone" are the same zone everywhere zones are compared - filters, access grants and their
SQL twins - so older trainings and grants keep matching. State / District no longer come from
the master (user, 2026-10-14) - the pincode directory replaced it (tests/test_locations.py)."""

import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from app.core.constants import AUDIENCE_CATEGORY, CHECKLIST_CATEGORY, SESSION_TYPE_CATEGORY
from app.dependencies.filters import ConferenceFilters
from app.models.admin_access import AdminAccess
from app.models.category import Category, SubCategory
from app.models.conference import Conference
from app.models.venue import Venue
from app.repositories import dashboard_repository
from app.services.access_service import reject_outside_scope, resolve_scope, scope_summary
from app.utils.zones import zone_key, zone_spellings
from tests.tenant_fixtures import ALPHA, TenantWorld, uid


class ZoneKey(unittest.TestCase):
    def test_both_spellings_are_one_zone(self):
        for value in ("North", "North Zone", " north zone ", "NORTH", "North  Zone"):
            with self.subTest(value=value):
                self.assertEqual(zone_key(value), "north")

    def test_blanks_and_other_names_are_left_alone(self):
        self.assertEqual(zone_key(None), "")
        self.assertEqual(zone_key("   "), "")
        self.assertEqual(zone_key("Zone"), "zone")    # nothing before the suffix: kept as is
        self.assertEqual(zone_key("Ozone"), "ozone")  # not a " zone" suffix
        self.assertEqual(zone_spellings("North Zone"), ("north", "north zone"))
        self.assertEqual(zone_spellings("north"), ("north", "north zone"))


class MasterListPickers(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        db = self.w.tenant_db[ALPHA]
        db.add_all([
            # the zones are categories marked "Zone" (as in the real table); their subcategories are the regions
            Category(categoryUid="CA-E", name="East", visibleOnWeb="Zone", status="Approved"),                # no regions yet
            Category(categoryUid="CA-N", name=" North ", visibleOnWeb="Zone", status="Approved"),
            Category(categoryUid="CA-C", name="Central", visibleOnWeb="Zone", status="Pending"),              # not approved
            Category(categoryUid="CA-R", name="Room Type", visibleOnWeb="Venue", status="Approved"),          # not a zone
            SubCategory(subCategoryUid="RG1", categoryUid="CA-N", subCategory="North 2", status="Approved"),
            SubCategory(subCategoryUid="RG2", categoryUid="CA-N", subCategory=" North 1 ", status="Approved"),
            SubCategory(subCategoryUid="RG3", categoryUid="CA-N", subCategory="North 9", status="Rejected"),   # not approved
            SubCategory(subCategoryUid="RG4", categoryUid="CA-C", subCategory="Central 1", status="Approved"),  # its zone isn't
            # the states: categories marked "State"; their subcategories are the districts
            Category(categoryUid="CA-MH", name="Maharashtra", visibleOnWeb="State", status="Approved"),
            Category(categoryUid="CA-DL", name="Delhi", visibleOnWeb="state", status="Approved"),              # any case
            Category(categoryUid="CA-OS", name="Old State", visibleOnWeb="State", status="Rejected"),
            SubCategory(subCategoryUid="DT9", categoryUid="CA-OS", subCategory="Ghost District", status="Approved"),
            SubCategory(subCategoryUid="DT1", categoryUid="CA-MH", subCategory="Pune", status="Approved"),
            SubCategory(subCategoryUid="DT2", categoryUid="CA-MH", subCategory="Mumbai", status="Approved"),
            SubCategory(subCategoryUid="DT3", categoryUid="CA-DL", subCategory="New Delhi", status="Approved"),
            SubCategory(subCategoryUid="DT4", categoryUid="CA-DL", subCategory="Old District", status="Pending"),
            # the fields' own categories, found by name (any case / spacing) - never by an ID
            Category(categoryUid="CAT-AUD", name=f" {AUDIENCE_CATEGORY.upper()} ", status="Approved"),
            Category(categoryUid="CAT-SES", name=SESSION_TYPE_CATEGORY, status="Approved"),
            Category(categoryUid="CAT-CHK", name=CHECKLIST_CATEGORY, status="Approved"),
            Category(categoryUid="CAT-OLD", name=AUDIENCE_CATEGORY, status="Rejected"),   # not approved
            SubCategory(subCategoryUid="SC1", categoryUid="CAT-AUD", subCategory="Retail Staff", status="Approved"),
            SubCategory(subCategoryUid="SC2", categoryUid="CAT-AUD", subCategory="Old Audience", status="Rejected"),
            SubCategory(subCategoryUid="SC6", categoryUid="CAT-OLD", subCategory="Retired Audience", status="Approved"),
            SubCategory(subCategoryUid="SC3", categoryUid="CAT-SES", subCategory="Classroom", status="Approved"),
            SubCategory(subCategoryUid="SC4", categoryUid="CAT-CHK", subCategory="Projector", status="Approved"),
            SubCategory(subCategoryUid="SC5", categoryUid="CA-R", subCategory="Deluxe", status="Approved"),  # another field's option
        ])
        db.commit()

    def tearDown(self):
        self.w.close()

    def get(self, path, who="trainer1"):
        response = self.w.client.get(path, headers=self.w.headers(who))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def options(self, path, who="trainer1"):
        return [(option["label"], option["value"]) for option in self.get(path, who)]

    def test_the_zones_are_the_approved_zone_categories_each_with_its_approved_regions(self):
        self.assertEqual(self.get("/admin/zones"), [
            {"name": "East", "options": []},
            {"name": "North", "options": ["North 1", "North 2"]},
        ])

    def test_the_masters_state_categories_are_no_longer_the_state_list(self):
        # The fixture still holds approved "State" categories with districts; the State picker now
        # reads only the pincode directory, which is empty in this world.
        self.assertEqual(self.get("/admin/states"), [])

    def test_a_district_name_finds_venues_saved_with_the_name_or_with_the_old_code(self):
        db = self.w.tenant_db[ALPHA]
        db.add_all([
            Venue(venueUid="V1", name="Hall A", district="new_delhi", status="Approved"),   # older app builds' code
            Venue(venueUid="V2", name="Hall B", district="New Delhi", status="Approved"),   # the master's name
            Venue(venueUid="V3", name="Hall C", district="Mumbai", status="Approved"),
            Venue(venueUid="V4", name="Hall D", district="New Delhi", status="Pending"),     # not approved
        ])
        db.commit()
        for district in ("New Delhi", "new_delhi", " NEW DELHI "):
            with self.subTest(district=district):
                self.assertEqual(self.options(f"/admin/venues?district={district}"), [("Hall A", "V1"), ("Hall B", "V2")])

    def test_each_picker_offers_only_its_own_categorys_approved_options(self):
        self.assertEqual(self.options("/admin/audiences"), [("Retail Staff", "Retail Staff")])
        self.assertEqual(self.options("/admin/session-types"), [("Classroom", "Classroom")])

    def test_the_checklist_no_longer_offers_other_categories_options(self):
        self.assertEqual(self.options("/admin/checklist-items"), [("Projector", "SC4")])

    def test_a_category_with_no_options_yet_offers_the_values_past_trainings_used(self):
        # No Training Type option in the master: the fixture trainings' "Webinar" is still offered.
        self.assertEqual(self.options("/admin/training-types"), [("Webinar", "Webinar")])

    def test_admin_panel_accounts_get_the_same_options(self):
        self.assertEqual(self.get("/admin/zones", who="coord"), self.get("/admin/zones"))
        self.assertEqual(self.get("/admin/states", who="coord"), self.get("/admin/states"))


class NorthIsNorthZone(unittest.TestCase):
    """S_NEW is a training saved with the master's "North"; the fixture ones say "North Zone"."""

    def setUp(self):
        self.w = TenantWorld()
        db = self.w.tenant_db[ALPHA]
        db.add(Conference(conferenceUid=uid("S_NEW"), company="Samsung India", zone="North", region="North 1",
                          trainerEmployeeId="trainer1", trainerName="Trainer1", conferenceDate="2026-09-20",
                          conferenceStatus="Scheduled", status="Pending", trainingType="Webinar"))
        db.commit()

    def tearDown(self):
        self.w.close()

    def scope(self, who="coord"):
        return resolve_scope(self.w.common, self.w.principal(who), ALPHA)

    def visible(self, conditions) -> set:
        db = self.w.tenant_db[ALPHA]
        return {value.removeprefix("CONF-") for (value,) in db.query(Conference.conferenceUid).filter(*conditions)}

    def regrant_coordinator(self, zone):
        self.w.common.query(AdminAccess).filter_by(admin_id=self.w.admins["coord"].id).update({"zone": zone})
        self.w.common.commit()

    def test_a_north_zone_grant_covers_a_training_saved_as_north(self):
        scope = self.scope()
        self.assertTrue(scope.allows_row("Samsung India", "North", "North 1"))
        self.assertFalse(scope.allows_row("Samsung India", "South", "South 1"))
        self.assertEqual(self.visible(dashboard_repository.access_scope_conditions(scope)), {"S_N1", "S_DEL", "S_N1V", "S_NEW"})

    def test_a_north_grant_covers_the_older_north_zone_trainings(self):
        self.regrant_coordinator("North")
        scope = self.scope()
        self.assertTrue(scope.allows_row("Samsung India", "North Zone", "North 1"))
        self.assertEqual(self.visible(dashboard_repository.access_scope_conditions(scope)), {"S_N1", "S_DEL", "S_N1V", "S_NEW"})

    def test_two_spellings_of_one_grant_are_one_rule_and_the_summary_lists_both_spellings_once(self):
        self.w.grant(self.w.admins["coord"], "coordinator", ALPHA, "Samsung India", zone="North")
        self.w.common.commit()
        scope = self.scope()
        self.assertEqual(len(scope.rules), 1)
        # Both spellings, so an older app build (which looks for "north zone") still finds its zone.
        self.assertEqual(scope_summary(scope)["zones"], ["north", "north zone"])

    def test_a_north_zone_coordinator_may_place_a_training_in_north_but_not_south(self):
        reject_outside_scope(self.scope(), "Samsung India", "North", "North 1")
        with self.assertRaises(HTTPException):
            reject_outside_scope(self.scope(), "Samsung India", "South", "South 1")

    def test_the_zone_filter_matches_either_spelling_in_sql_and_in_memory(self):
        for wanted in ("North", "North Zone", "north zone"):
            with self.subTest(filter=wanted):
                filters = ConferenceFilters(zones=[wanted])
                self.assertEqual(self.visible(dashboard_repository.conference_conditions(filters)), {"S_N1", "S_DEL", "S_N1V", "S_NEW", "O_N1"})
                self.assertTrue(filters.matches(SimpleNamespace(conferenceDate="2026-09-20", company="X", trainerEmployeeId="t",
                                                                zone="North", region="r", sessionType="s", trainingType="w")))

    def test_the_training_list_shows_both_spellings_to_the_coordinator_and_filters_by_either(self):
        for query in ("", "&zones=North", "&zones=North%20Zone"):
            with self.subTest(query=query):
                response = self.w.client.get(f"/admin/trainings/page?limit=200{query}", headers=self.w.headers("coord"))
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(self.w.conference_keys(response.json()["items"]), {"S_N1", "S_DEL", "S_N1V", "S_NEW"})


if __name__ == "__main__":
    unittest.main()
