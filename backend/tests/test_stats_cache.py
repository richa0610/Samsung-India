"""The admin dashboard stats are computed on every open - never served from a cache, since other
servers and systems write to the same database (Phase 5). The small TTLCache helper itself is
still used elsewhere (the tenant status cache) and is tested here."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.core.ttl_cache import TTLCache
from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
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


class StatsAreNeverCached(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def fake_build(common_db, db, filters, admin=None, tenant_id=None):
            self.calls.append(filters)
            return SimpleNamespace(n=len(self.calls))

        p = patch.object(admin_router.admin_service, "build_admin_dashboard_stats", side_effect=fake_build)
        p.start()
        self.addCleanup(p.stop)
        self.request = SimpleNamespace(headers={}, query_params={})

    def call(self, fresh=False):
        admin = Admin()
        admin.id = 1
        return admin_router.get_admin_dashboard_stats(self.request, fresh, None, None, ConferenceFilters(), admin)

    def test_every_open_is_computed(self):
        first, second, refreshed = self.call(), self.call(), self.call(fresh=True)
        self.assertEqual((first.n, second.n, refreshed.n), (1, 2, 3))

    def test_no_cache_is_left_behind(self):
        self.assertFalse(hasattr(admin_router, "_stats_cache"))


if __name__ == "__main__":
    unittest.main()
