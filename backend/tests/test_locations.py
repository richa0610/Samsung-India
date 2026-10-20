"""State / District / Venue pickers from the pincode directory (user, 2026-10-14).

The India Post directory (`pincode`, shared Common database - one row per post office, names in
capitals) replaces the master list's "State" categories entirely, with no fallback. Each state is
listed once with its own districts, shown as words ("UTTAR PRADESH" -> "Uttar Pradesh"). A venue
belongs to a district when its own district (and state, when it has one) say so, or when its
pincode is one of that district's - so "Aurangabad" in Bihar never lists Maharashtra's venues.
The list is public (the registration form reads it before sign-in) and cached for an hour.

Synthetic TenantWorld (in-memory SQLite) only - never a real database.
"""

import unittest
from unittest.mock import patch

from app.database.connection import CommonBase, TenantBase
from app.models.pincode import Pincode, PincodeBase
from app.models.trainee import Trainee
from app.models.venue import Venue
from app.repositories import dashboard_repository, location_repository
from app.services import location_service
from app.utils.places import place_key, place_name, place_spellings
from tests.tenant_fixtures import ALPHA, TenantWorld

# (pincode, district, state) - as the other system stores them.
DIRECTORY = [
    ("431001", "AURANGABAD", "MAHARASHTRA"),
    ("431002", "AURANGABAD", "MAHARASHTRA"),
    ("431001", "AURANGABAD", "MAHARASHTRA"),  # a second post office with the same pincode
    ("400001", "MUMBAI", "MAHARASHTRA"),
    ("400002", "Mumbai", "Maharashtra"),  # another spelling of the same place
    ("824101", "AURANGABAD", "BIHAR"),  # the same district name, in another state
    ("110001", "NEW DELHI", "DELHI"),
    ("110002", "", "DELHI"),  # no district - left out
    ("999999", "GHOST", "  "),  # no state - left out
    ("180001", "JAMMU", "JAMMU AND KASHMIR"),
]

EXPECTED_STATES = [
    {"name": "Bihar", "options": ["Aurangabad"]},
    {"name": "Delhi", "options": ["New Delhi"]},
    {"name": "Jammu and Kashmir", "options": ["Jammu"]},
    {"name": "Maharashtra", "options": ["Aurangabad", "Mumbai"]},
]


class PlaceNames(unittest.TestCase):
    def test_a_name_in_capitals_reads_as_words(self):
        for raw, shown in (
            ("UTTAR PRADESH", "Uttar Pradesh"),
            ("JAMMU AND KASHMIR", "Jammu and Kashmir"),
            ("THE DADRA AND NAGAR HAVELI AND DAMAN AND DIU", "The Dadra and Nagar Haveli and Daman and Diu"),
            ("AURANGABAD(BH)", "Aurangabad(BH)"),
            ("Y.S.R.", "Y.S.R."),
            ("NORTH-EAST", "North-East"),
            ("  NORTH   GOA ", "North Goa"),
            ("mumbai", "Mumbai"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(place_name(raw), shown)

    def test_a_name_already_written_in_mixed_case_is_kept(self):
        self.assertEqual(place_name("Y.S.R. Kadapa"), "Y.S.R. Kadapa")
        self.assertEqual(place_name(" Lucknow "), "Lucknow")

    def test_every_saved_spelling_is_one_place(self):
        for spelling in ("Uttar Pradesh", "UTTAR PRADESH", " uttar pradesh ", "uttar_pradesh", "up", "UP"):
            with self.subTest(spelling=spelling):
                self.assertEqual(place_key(spelling), "uttar pradesh")
        self.assertEqual(place_key("puducherry_city"), "puducherry")
        self.assertEqual(place_key(None), "")

    def test_the_spellings_of_a_place_include_the_old_codes_for_it(self):
        self.assertEqual(place_spellings("Uttar Pradesh"), ["up", "uttar pradesh"])
        self.assertEqual(place_spellings("Chandigarh"), ["chandigarh", "chandigarh city"])
        self.assertEqual(place_spellings("Bihar"), ["bihar"])


class TheTableIsNeverChangedByTheApp(unittest.TestCase):
    def test_startup_metadata_does_not_hold_the_pincode_table(self):
        # main.py runs create_all + the column / index sync on these two - never on the directory.
        self.assertNotIn("pincode", CommonBase.metadata.tables)
        self.assertNotIn("pincode", TenantBase.metadata.tables)
        self.assertIs(Pincode.__table__.metadata, PincodeBase.metadata)


class DirectoryWorld(unittest.TestCase):
    def setUp(self):
        self.w = TenantWorld()
        self.w.common.add_all(Pincode(pincode=pin, district=district, stateName=state) for pin, district, state in DIRECTORY)
        self.w.common.commit()

    def tearDown(self):
        self.w.close()

    def get(self, path, who=None):
        response = self.w.client.get(path, headers=self.w.headers(who) if who else {})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()


class TheStateAndDistrictLists(DirectoryWorld):
    def test_each_state_is_listed_once_with_only_its_own_districts(self):
        self.assertEqual(self.get("/locations/states"), EXPECTED_STATES)

    def test_needs_no_sign_in_for_the_registration_form(self):
        self.assertEqual(self.w.client.get("/locations/states").status_code, 200)

    def test_the_staff_pickers_get_the_same_list(self):
        for who in ("trainer1", "coord", "super"):
            with self.subTest(who=who):
                self.assertEqual(self.get("/admin/states", who=who), EXPECTED_STATES)

    def test_an_empty_directory_gives_an_empty_list_with_no_fallback(self):
        self.w.common.query(Pincode).delete()
        self.w.common.commit()
        location_service.clear_cache()
        self.assertEqual(self.get("/locations/states"), [])

    def test_the_list_is_read_once_and_then_served_from_memory(self):
        with patch.object(
            location_repository, "state_district_pairs", wraps=location_repository.state_district_pairs
        ) as read:
            self.get("/locations/states")
            self.get("/admin/states", who="trainer1")
            self.assertEqual(read.call_count, 1)
            location_service.clear_cache()
            self.get("/locations/states")
            self.assertEqual(read.call_count, 2)
        self.assertEqual(location_service.CACHE_SECONDS, 3600)

    def pincodes(self, state, district):
        return location_service.district_pincodes(self.w.common, state, district)

    def test_a_districts_pincodes_cover_every_spelling_of_it_and_never_another_states(self):
        self.assertEqual(self.pincodes("Maharashtra", "Mumbai"), {"400001", "400002"})
        self.assertEqual(self.pincodes("MAHARASHTRA", "aurangabad"), {"431001", "431002"})
        self.assertEqual(self.pincodes("Bihar", "Aurangabad"), {"824101"})
        self.assertEqual(self.pincodes("Bihar", "Mumbai"), frozenset())
        self.assertEqual(self.pincodes("Atlantis", "Mumbai"), frozenset())


class TheVenueList(DirectoryWorld):
    def setUp(self):
        super().setUp()
        db = self.w.tenant_db[ALPHA]
        db.add_all([
            Venue(venueUid="V-MH", name="Hall MH", state="Maharashtra", district="Aurangabad", status="Approved"),
            Venue(venueUid="V-BR", name="Hall BR", state="Bihar", district="Aurangabad", status="Approved"),
            # no state on record: its district name is all there is to go by
            Venue(venueUid="V-NOSTATE", name="Hall NoState", district="aurangabad", status="Approved"),
            # its own district is misspelled, but its pincode is Maharashtra's Aurangabad
            Venue(venueUid="V-PIN", name="Hall Pin", state="Maharashtra", district="Aurangabad City", pincode="431 002", status="Approved"),
            Venue(venueUid="V-PENDING", name="Hall Pending", state="Maharashtra", district="Aurangabad", pincode="431001", status="Pending"),
            Venue(venueUid="V-MUM", name="Hall Mumbai", state="maharashtra", district="MUMBAI", status="Approved"),
            # saved under another district, but its pincode is Bihar's Aurangabad
            Venue(venueUid="V-GAYA", name="Hall Gaya", state="Bihar", district="Gaya", pincode="824101", status="Approved"),
        ])
        db.commit()

    def venues(self, query):
        return [option["value"] for option in self.get(f"/admin/venues?{query}", who="trainer1")]

    def test_a_district_lists_only_its_own_states_venues_and_those_its_pincodes_place_there(self):
        self.assertEqual(self.venues("state=Maharashtra&district=Aurangabad"), ["V-MH", "V-NOSTATE", "V-PIN"])
        self.assertEqual(self.venues("state=Bihar&district=Aurangabad"), ["V-BR", "V-GAYA", "V-NOSTATE"])

    def test_any_spelling_of_the_state_and_district_finds_them(self):
        self.assertEqual(self.venues("state=MAHARASHTRA&district=aurangabad"), ["V-MH", "V-NOSTATE", "V-PIN"])
        self.assertEqual(self.venues("state=Maharashtra&district=Mumbai"), ["V-MUM"])

    def test_a_district_the_directory_doesnt_know_still_finds_venues_by_name(self):
        self.assertEqual(self.venues("state=Bihar&district=Gaya"), ["V-GAYA"])
        self.assertEqual(self.venues("state=Maharashtra&district=Nowhere"), [])

    def test_an_older_app_build_sending_only_the_district_gets_its_venues_by_name(self):
        self.assertEqual(self.venues("district=Aurangabad"), ["V-BR", "V-MH", "V-NOSTATE"])

    def test_an_overlong_name_is_refused(self):
        response = self.w.client.get(f"/admin/venues?district={'x' * 151}", headers=self.w.headers("trainer1"))
        self.assertEqual(response.status_code, 422)


class TheStateRankingPool(unittest.TestCase):
    """Trainees registered by older app builds saved the old list's codes ("uttar_pradesh", "up");
    newer ones save the directory's name. They are one state when ranking."""

    def setUp(self):
        self.w = TenantWorld()
        db = self.db = self.w.tenant_db[ALPHA]
        # Every fixture trainee marked Present is ranked; five of them get a state here.
        for trainee_uid, state in (
            ("TR-S_N1-0", "Uttar Pradesh"),
            ("TR-S_DEL-0", "uttar_pradesh"),
            ("TR-S_S1-0", "up"),
            ("TR-S_BLANK-0", "UTTAR PRADESH"),
            ("TR-S_N1V-0", "Bihar"),
        ):
            db.query(Trainee).filter(Trainee.traineeUid == trainee_uid).update({"state": state})
        db.commit()

    def tearDown(self):
        self.w.close()

    def test_every_spelling_of_a_state_is_one_pool(self):
        for trainee_uid, state in (("TR-S_N1-0", "Uttar Pradesh"), ("TR-S_S1-0", "up")):
            with self.subTest(state=state):
                _, in_state = dashboard_repository.trainee_rank(self.db, trainee_uid, state)
                self.assertEqual((in_state.rank, in_state.total), (1, 4))

    def test_another_state_is_its_own_pool_and_no_state_is_none(self):
        _, bihar = dashboard_repository.trainee_rank(self.db, "TR-S_N1V-0", "Bihar")
        self.assertEqual((bihar.rank, bihar.total), (1, 1))
        _, none = dashboard_repository.trainee_rank(self.db, "TR-O_N1-0", "  ")
        self.assertEqual((none.rank, none.total), (None, 0))
