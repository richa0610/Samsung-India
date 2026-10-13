"""ConferenceFilters.matches - the admin filter applied to a training in memory (the access-plan
report counts trainings with it). Every list matches case- and space-insensitively; an empty filter
matches everything; every set filter must match."""

import unittest
from types import SimpleNamespace

from app.dependencies.filters import ConferenceFilters, get_conference_filters

LIST_FIELDS = {   # filter list -> the training field it's matched against
    "trainers": "trainerEmployeeId",
    "zones": "zone",
    "regions": "region",
    "session_types": "sessionType",
    "training_types": "trainingType",
}


def training(**overrides):
    values = dict(conferenceDate="2026-10-08", trainerEmployeeId="trainer1", zone="North Zone", region="North 1",
                  sessionType="Classroom", trainingType="Product", company="Samsung India")
    values.update(overrides)
    return SimpleNamespace(**values)


class Matches(unittest.TestCase):
    def test_an_empty_filter_matches_everything_even_blank_trainings(self):
        blank = training(**{field: None for field in LIST_FIELDS.values()}, conferenceDate=None, company=None)
        self.assertTrue(ConferenceFilters().matches(training()))
        self.assertTrue(ConferenceFilters().matches(blank))

    def test_the_date_range_is_inclusive(self):
        window = ConferenceFilters(start="2026-10-01", end="2026-10-31")
        for date, expected in (("2026-09-30", False), ("2026-10-01", True), ("2026-10-31", True), ("2026-11-01", False)):
            with self.subTest(date=date):
                self.assertEqual(window.matches(training(conferenceDate=date)), expected)

    def test_an_undated_training_fails_a_start_date_but_passes_an_end_date_only(self):
        self.assertFalse(ConferenceFilters(start="2026-10-01").matches(training(conferenceDate=None)))
        self.assertTrue(ConferenceFilters(end="2026-10-31").matches(training(conferenceDate=None)))

    def test_each_list_filter_ignores_case_and_spaces_and_rejects_others_and_blanks(self):
        for filter_name, field in LIST_FIELDS.items():
            wanted = get_conference_filters(**{name: None for name in ("start", "end", *LIST_FIELDS)} | {filter_name: " Wanted , Other "})
            with self.subTest(filter=filter_name):
                self.assertTrue(wanted.matches(training(**{field: "  WANTED "})))
                self.assertTrue(wanted.matches(training(**{field: "other"})))
                self.assertFalse(wanted.matches(training(**{field: "something else"})))
                self.assertFalse(wanted.matches(training(**{field: None})))

    def test_the_company_scope_ignores_case_and_spaces(self):
        scoped = ConferenceFilters(company=" samsung india ")
        self.assertTrue(scoped.matches(training(company="Samsung India")))
        self.assertFalse(scoped.matches(training(company="Other Co")))
        self.assertFalse(scoped.matches(training(company=None)))

    def test_every_set_filter_must_match(self):
        both = ConferenceFilters(zones=["north zone"], training_types=["product"])
        self.assertTrue(both.matches(training()))
        self.assertFalse(both.matches(training(trainingType="Soft Skills")))
        self.assertFalse(both.matches(training(zone="South Zone")))


if __name__ == "__main__":
    unittest.main()
