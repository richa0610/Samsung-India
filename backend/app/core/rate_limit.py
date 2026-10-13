import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.utils.helpers import client_ip

# Single-process, in-memory sliding-window counters. Fine for the single-worker deployment this
# runs as (see run_prod.py); if this ever runs behind multiple worker processes, move the counters
# to Redis instead.
_attempts: dict[str, list[float]] = defaultdict(list)  # "path:client_ip" -> request times
_failures: dict[str, list[float]] = defaultdict(list)  # "scope:account" -> failed-login times
_caller_failures: dict[str, list[float]] = defaultdict(list)  # "scope:client_ip" -> failed-login times

# Failed logins allowed per account (phone / username) inside the window, whatever IP they come
# from - so spreading guesses over many addresses doesn't help. A success clears the count.
ACCOUNT_MAX_FAILURES = 10
ACCOUNT_WINDOW_SECONDS = 900

# Failed logins allowed per caller IP inside the window, for a login limited by failures only (the
# trainee login): a classroom signing in over one venue Wi-Fi shares one public IP, so counting
# successes too would lock the room out after a handful of trainees. A success does NOT clear it -
# otherwise one valid account could reset the count between guesses at others.
CALLER_MAX_FAILURES = 20
CALLER_WINDOW_SECONDS = 300

_TOO_MANY = "Too many attempts. Please try again later."


def _recent(times: list[float], window_seconds: int) -> list[float]:
    window_start = time.monotonic() - window_seconds
    times[:] = [t for t in times if t > window_start]
    return times


def rate_limit(max_attempts: int = 5, window_seconds: int = 300):
    """Per-caller limit on an endpoint. The caller's IP comes from utils.helpers.client_ip, which
    only trusts what our own proxy added - a forged X-Forwarded-For / CF-Connecting-IP can't
    make each request look like a new caller."""

    def dependency(request: Request) -> None:
        attempts = _recent(_attempts[f"{request.url.path}:{client_ip(request) or 'unknown'}"], window_seconds)
        if len(attempts) >= max_attempts:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=_TOO_MANY)
        attempts.append(time.monotonic())

    return dependency


def _refuse_if_over(times: list[float], max_failures: int, window_seconds: int) -> None:
    if len(_recent(times, window_seconds)) >= max_failures:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=_TOO_MANY)


def _account_key(scope: str, account: str) -> str:
    return f"{scope}:{str(account).strip().lower()}"


def _caller_key(scope: str, ip_address: str | None) -> str:
    return f"{scope}:{ip_address or 'unknown'}"


def ensure_account_not_locked(scope: str, account: str) -> None:
    """Refuses (429) a login for an account that has failed too often recently."""
    _refuse_if_over(_failures[_account_key(scope, account)], ACCOUNT_MAX_FAILURES, ACCOUNT_WINDOW_SECONDS)


def ensure_caller_not_locked(scope: str, ip_address: str | None) -> None:
    """Refuses (429) a login from a caller IP with too many recent failed logins (see CALLER_MAX_FAILURES).
    `ip_address` is utils.helpers.client_ip's - only what our own proxy appended."""
    _refuse_if_over(_caller_failures[_caller_key(scope, ip_address)], CALLER_MAX_FAILURES, CALLER_WINDOW_SECONDS)


def record_caller_failure(scope: str, ip_address: str | None) -> None:
    _caller_failures[_caller_key(scope, ip_address)].append(time.monotonic())


def record_account_failure(scope: str, account: str) -> None:
    _failures[_account_key(scope, account)].append(time.monotonic())


def clear_account_failures(scope: str, account: str) -> None:
    _failures.pop(_account_key(scope, account), None)


def reset() -> None:
    """Forgets every counter - for tests, which share this process-wide state."""
    _attempts.clear()
    _failures.clear()
    _caller_failures.clear()
