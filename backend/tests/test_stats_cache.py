"""The admin dashboard stats are cached for 30 seconds per admin + filter.
These check the cache expires and stays bounded, that one admin can never be
served another's numbers, and that `fresh=true` (pull-to-refresh / live update)
bypasses it."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.ttl_cache import TTLCache
from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.routers import admin as admin_router


class TTLCacheTests(unittest.TestCase):
    def test_entries_expire(self):
        cache = TTLCache(ttl_seconds=30)
        with patch("app.core.ttl_cache.time.monotonic", return_value=1000.0):
            cache.set("k", "v")
            self.assertEqual(cache.get("k"), "v")
        with patch("app.core.ttl_cache.time.monotonic", return_value=1029.9):
            self.assertEqual(cache.get("k"), "v")
        with patch("app.core.ttl_cache.time.monotonic", return_value=1030.0):
            self.assertIsNone(cache.get("k"))

    def test_stays_bounded_and_drops_the_oldest(self):
        cache = TTLCache(ttl_seconds=30, max_entries=3)
        for step, key in enumerate("abcd"):
            with patch("app.core.ttl_cache.time.monotonic", return_value=1000.0 + step):
                cache.set(key, key.upper())
        with patch("app.core.ttl_cache.time.monotonic", return_value=1005.0):
            self.assertIsNone(cache.get("a"))
            self.assertEqual([cache.get(k) for k in "bcd"], ["B", "C", "D"])


def _admin(kind, ident):
    obj = (Admin if kind == "admin" else AgencyTeam)()
    obj.id = ident
    return obj


class StatsCacheKeyTests(unittest.TestCase):
    def test_key_separates_tenant_account_and_scope(self):
        f = ConferenceFilters(company="Samsung India", zones=["north"])
        base = admin_router.stats_cache_key("samsung", _admin("admin", 1), f)
        self.assertEqual(base, admin_router.stats_cache_key("samsung", _admin("admin", 1), ConferenceFilters(company="Samsung India", zones=["north"])))
        self.assertNotEqual(base, admin_router.stats_cache_key("other", _admin("admin", 1), f))            # another tenant
        self.assertNotEqual(base, admin_router.stats_cache_key("samsung", _admin("admin", 2), f))           # another admin
        self.assertNotEqual(base, admin_router.stats_cache_key("samsung", _admin("agency", 1), f))          # same id, other table
        self.assertNotEqual(base, admin_router.stats_cache_key("samsung", _admin("admin", 1), ConferenceFilters(company="Samsung India", zones=["south"])))  # other zone scope
        self.assertNotEqual(base, admin_router.stats_cache_key("samsung", _admin("admin", 1), ConferenceFilters(company="Other Co", zones=["north"])))      # other company
        self.assertNotEqual(base, admin_router.stats_cache_key("samsung", _admin("admin", 1), ConferenceFilters(company="Samsung India", zones=["north"], start="2026-09-01")))  # other date filter


class RouteCachingTests(unittest.TestCase):
    def setUp(self):
        admin_router._stats_cache.clear()
        self.request = SimpleNamespace(headers={}, query_params={})
        self.calls = []

        def fake_build(common_db, db, filters, admin=None, tenant_id=None):
            self.calls.append(filters)
            return SimpleNamespace(n=len(self.calls))

        self.patches = [
            patch.object(admin_router.admin_service, "build_admin_dashboard_stats", side_effect=fake_build),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        admin_router._stats_cache.clear()

    def _call(self, admin, filters=None, fresh=False):
        return admin_router.get_admin_dashboard_stats(
            self.request, fresh, None, None, filters or ConferenceFilters(company="Samsung India"), admin
        )

    def test_second_open_is_served_from_the_cache(self):
        a = _admin("admin", 1)
        first, second = self._call(a), self._call(a)
        self.assertIs(first, second)
        self.assertEqual(len(self.calls), 1)

    def test_fresh_skips_the_cache_and_refreshes_it(self):
        a = _admin("admin", 1)
        self._call(a)
        refreshed = self._call(a, fresh=True)
        self.assertEqual(len(self.calls), 2)
        self.assertIs(self._call(a), refreshed)  # the next normal open sees the refreshed copy
        self.assertEqual(len(self.calls), 2)

    def test_different_admins_and_filters_never_share_an_entry(self):
        self._call(_admin("admin", 1))
        self._call(_admin("admin", 2))
        self._call(_admin("admin", 1), ConferenceFilters(company="Samsung India", start="2026-09-24", end="2026-09-24"))
        self.assertEqual(len(self.calls), 3)


if __name__ == "__main__":
    unittest.main()
