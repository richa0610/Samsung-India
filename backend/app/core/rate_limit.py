import threading
import time

from fastapi import HTTPException, status

from app.core.ttl_cache import TTLCache

# Single-process, in-memory sliding-window counters. Fine for the single-worker deployment this
# runs as (see run_prod.py); if this ever runs behind multiple worker processes, move the counters
# to Redis instead.
#
# Logins are limited per ACCOUNT only - there is deliberately no per-caller-IP limit (user,
# 2026-10-17): a classroom on one venue Wi-Fi, or trainers on one office network, share a single
# public address, and any per-address count ended up refusing real people.

# Failed logins allowed per account (phone / username) inside the window, whatever IP they come
# from - so spreading guesses over many addresses doesn't help. A success clears the count.
ACCOUNT_MAX_FAILURES = 10
ACCOUNT_WINDOW_SECONDS = 900

# How many accounts' recent failures are remembered at once. An account's entry goes
# ACCOUNT_WINDOW_SECONDS after its latest failure (every failure in it is outside the window by
# then), and past this many the least recently failed goes first - so a script typing endless
# made-up IDs, which never reach the slow password check, can't grow memory without limit (about
# 16 MB at most, measured with the longest IDs the login schemas allow). The trade-off: pushing a
# locked account out takes this many newer failed logins, each one a request of its own.
MAX_TRACKED_ACCOUNTS = 20_000

_failures = TTLCache(ttl_seconds=ACCOUNT_WINDOW_SECONDS, max_entries=MAX_TRACKED_ACCOUNTS)  # "scope:account" -> failed-login times
# Reading an account's failure times and storing them again is one step: requests run on many threads.
_lock = threading.Lock()

_TOO_MANY = "Too many attempts. Please try again later."


def _account_key(scope: str, account: str) -> str:
    return f"{scope}:{str(account).strip().lower()}"


def _recent_failures(key: str) -> list[float]:
    """The account's failure times still inside the window. Call with `_lock` held."""
    window_start = time.monotonic() - ACCOUNT_WINDOW_SECONDS
    return [t for t in _failures.get(key) or () if t > window_start]


def ensure_account_not_locked(scope: str, account: str) -> None:
    """Refuses (429) a login for an account that has failed too often recently. Stores nothing -
    only a failure is remembered."""
    with _lock:
        locked = len(_recent_failures(_account_key(scope, account))) >= ACCOUNT_MAX_FAILURES
    if locked:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=_TOO_MANY)


def record_account_failure(scope: str, account: str) -> None:
    key = _account_key(scope, account)
    with _lock:
        _failures.set(key, [*_recent_failures(key), time.monotonic()])


def clear_account_failures(scope: str, account: str) -> None:
    with _lock:
        _failures.discard(_account_key(scope, account))


def reset() -> None:
    """Forgets every counter - for tests, which share this process-wide state."""
    _failures.clear()
