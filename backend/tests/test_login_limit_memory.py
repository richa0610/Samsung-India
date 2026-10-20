"""The login failure limit takes bounded memory (review finding, 2026-10-19).

Failed logins are counted per account - made-up IDs included, which never reach the slow password
check and so cost almost nothing to send. Each account's entry is now dropped ACCOUNT_WINDOW_SECONDS
after its latest failure, at most MAX_TRACKED_ACCOUNTS are kept (the least recently failed go first),
and merely checking an account stores nothing. The approved rules are unchanged - per account only,
never per caller IP, 10 failures / 15 minutes, a success clears the count (test_phase23_fixes).

Pure in-process tests; the clock is replaced, so nothing waits in real time."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.core import rate_limit
from app.core.ttl_cache import TTLCache

SCOPE = "test-login"


class LimiterTestCase(unittest.TestCase):
    def setUp(self):
        rate_limit.reset()
        self.addCleanup(rate_limit.reset)
        self.now = 1_000_000.0
        clock = patch("app.core.rate_limit.time.monotonic", side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)

    def fail(self, account, times=1):
        for _ in range(times):
            rate_limit.record_account_failure(SCOPE, account)

    def locked(self, account):
        try:
            rate_limit.ensure_account_not_locked(SCOPE, account)
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 429)
            return True
        return False


class CheckingAnAccountStoresNothing(LimiterTestCase):
    def test_checking_accounts_that_never_failed_remembers_none_of_them(self):
        for i in range(1_000):
            self.assertFalse(self.locked(f"typed-{i}"))
        self.assertEqual(len(rate_limit._failures), 0)


class MemoryIsBounded(LimiterTestCase):
    def test_endless_made_up_ids_never_exceed_the_cap(self):
        for i in range(rate_limit.MAX_TRACKED_ACCOUNTS + 500):
            self.fail(f"typed-{i}")
        self.assertEqual(len(rate_limit._failures), rate_limit.MAX_TRACKED_ACCOUNTS)

    def test_a_locked_account_outlasts_a_flood_smaller_than_the_cap(self):
        self.fail("trainer1", rate_limit.ACCOUNT_MAX_FAILURES)
        for i in range(rate_limit.MAX_TRACKED_ACCOUNTS - 1):
            self.fail(f"typed-{i}")
        self.assertTrue(self.locked("trainer1"))

    def test_the_least_recently_failed_account_goes_first(self):
        self.fail("first", rate_limit.ACCOUNT_MAX_FAILURES)
        self.fail("second", rate_limit.ACCOUNT_MAX_FAILURES)
        for i in range(rate_limit.MAX_TRACKED_ACCOUNTS - 2):
            self.fail(f"typed-{i}")
        self.fail("first")       # still being guessed at: now the most recent
        self.fail("one-more")    # the cache is full - the least recently failed makes room
        self.assertTrue(self.locked("first"))
        self.assertFalse(self.locked("second"))


class EntriesExpire(LimiterTestCase):
    def test_an_account_is_free_once_its_failures_leave_the_window_and_its_entry_goes(self):
        self.fail("trainer1", rate_limit.ACCOUNT_MAX_FAILURES)
        self.now += rate_limit.ACCOUNT_WINDOW_SECONDS - 1
        self.assertTrue(self.locked("trainer1"))
        self.now += 1
        self.assertFalse(self.locked("trainer1"))
        self.assertEqual(len(rate_limit._failures), 0)

    def test_the_window_slides(self):
        self.fail("trainer1", rate_limit.ACCOUNT_MAX_FAILURES - 1)
        self.now += 600
        self.fail("trainer1")
        self.assertTrue(self.locked("trainer1"))
        self.now += 300   # the first failures are now a full window old
        self.assertFalse(self.locked("trainer1"))

    def test_a_success_forgets_the_account(self):
        self.fail("trainer1", 3)
        rate_limit.clear_account_failures(SCOPE, "trainer1")
        self.assertEqual(len(rate_limit._failures), 0)


class TTLCacheMakesRoomWithoutScanning(unittest.TestCase):
    """Entries are kept in the order stored, so making room drops from the front - the oldest, and
    any expired - instead of scanning every entry."""

    def test_a_re_stored_key_counts_as_the_newest_even_on_the_same_clock_tick(self):
        # Windows' monotonic clock ticks about every 15 ms, so equal timestamps are ordinary.
        cache = TTLCache(ttl_seconds=30, max_entries=2)
        with patch("app.core.ttl_cache.time.monotonic", return_value=1000.0):
            cache.set("a", 1)
            cache.set("b", 2)
            cache.set("a", 3)
            cache.set("c", 4)
            self.assertEqual([cache.get(k) for k in "abc"], [3, None, 4])

    def test_expired_entries_make_room_before_a_live_one(self):
        cache = TTLCache(ttl_seconds=30, max_entries=3)
        for at, key in ((1000.0, "a"), (1020.0, "b"), (1020.0, "c"), (1031.0, "d")):
            with patch("app.core.ttl_cache.time.monotonic", return_value=at):
                cache.set(key, key.upper())
        with patch("app.core.ttl_cache.time.monotonic", return_value=1031.0):
            self.assertEqual([cache.get(k) for k in "abcd"], [None, "B", "C", "D"])
            self.assertEqual(len(cache), 3)

    def test_discard_forgets_a_key(self):
        cache = TTLCache(ttl_seconds=30)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.discard("a")
        cache.discard("never-stored")
        self.assertEqual((len(cache), cache.get("a"), cache.get("b")), (1, None, 2))
