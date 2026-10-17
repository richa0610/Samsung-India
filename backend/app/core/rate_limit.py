import time
from collections import defaultdict

from fastapi import HTTPException, status

# Single-process, in-memory sliding-window counters. Fine for the single-worker deployment this
# runs as (see run_prod.py); if this ever runs behind multiple worker processes, move the counters
# to Redis instead.
#
# Logins are limited per ACCOUNT only - there is deliberately no per-caller-IP limit (user,
# 2026-10-17): a classroom on one venue Wi-Fi, or trainers on one office network, share a single
# public address, and any per-address count ended up refusing real people.
_failures: dict[str, list[float]] = defaultdict(list)  # "scope:account" -> failed-login times

# Failed logins allowed per account (phone / username) inside the window, whatever IP they come
# from - so spreading guesses over many addresses doesn't help. A success clears the count.
ACCOUNT_MAX_FAILURES = 10
ACCOUNT_WINDOW_SECONDS = 900

_TOO_MANY = "Too many attempts. Please try again later."


def _recent(times: list[float], window_seconds: int) -> list[float]:
    window_start = time.monotonic() - window_seconds
    times[:] = [t for t in times if t > window_start]
    return times


def _account_key(scope: str, account: str) -> str:
    return f"{scope}:{str(account).strip().lower()}"


def ensure_account_not_locked(scope: str, account: str) -> None:
    """Refuses (429) a login for an account that has failed too often recently."""
    if len(_recent(_failures[_account_key(scope, account)], ACCOUNT_WINDOW_SECONDS)) >= ACCOUNT_MAX_FAILURES:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=_TOO_MANY)


def record_account_failure(scope: str, account: str) -> None:
    _failures[_account_key(scope, account)].append(time.monotonic())


def clear_account_failures(scope: str, account: str) -> None:
    _failures.pop(_account_key(scope, account), None)


def reset() -> None:
    """Forgets every counter - for tests, which share this process-wide state."""
    _failures.clear()
