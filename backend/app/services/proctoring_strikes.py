"""A trainee's proctoring strikes, recorded and enforced on their attendance row for the training:

    theftRemarks       one line per strike, lock and unlock, newest first - never trimmed
    theftAttemptsLeft  the countdown ("3 to 0"): -1 per strike (never below 0), 0 at a lockout,
                       +3 per trainer unlock (PROCTORING_UNLOCK_ADDED_ATTEMPTS) - added, never reset
    isTheftLocked      1 once the server's own count of strikes since the last unlock reaches the
                       company's warning limit (the limit the app counts to as well), or the app
                       reports the lockout itself; a locked trainee can't open or submit the
                       Standard Test (trainee_access.open_assessment) until a trainer unlocks them
    securityDetails    JSON {"proctoring": {"reasons": {"SIDE-LOOK DETECTED": 2, ...}, "total": 3,
                                            "sinceUnlock": 3, "unlocks": 1, "strikeIds": [...]}}
                       `reasons` / `total` count every strike in this training and `unlocks` every
                       trainer unlock - an unlock never resets them. `sinceUnlock` is the server's
                       own count since the last unlock, so an app restarted mid-test (its count
                       starts over) can't delay the lock. `strikeIds` are the IDs the app gives
                       each strike: one sent twice - a retry on a bad connection - counts once.
                       Any other keys already there are kept.

Every caller holds the trainee's attendance row (SELECT ... FOR UPDATE) while it writes, so
concurrent strikes, lock reports, unlocks and submits run one after another.

An older app sends no strikes, only the lockout, without an ID (record_lockout): it is counted
once, and a repeat of it while the trainee is still locked changes nothing."""

import json
from dataclasses import dataclass
from typing import Optional

from app.core.constants import PROCTORING_UNLOCK_ADDED_ATTEMPTS
from app.models.attendance import Attendance
from app.utils.date_utils import utc_now

# Marks an unlock's line in theftRemarks - how rows written before `unlocks` was stored are counted.
UNLOCK_MARK = " -> UNLOCK: "

_KEY = "proctoring"
# The countdown's start when the row has none (the column's own default).
_DEFAULT_ATTEMPTS = 3
# Strike IDs remembered for spotting resends - a training's strikes are few, this only bounds the JSON.
_MAX_REMEMBERED_IDS = 200


@dataclass(frozen=True)
class StrikeOutcome:
    counted: bool  # False for a strike already counted (a resend)
    locked: bool  # the trainee is locked out now


def _details(attendance: Attendance) -> dict:
    """The row's securityDetails as a dict - text that isn't a JSON object is kept under "notes"."""
    raw = attendance.securityDetails
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {"notes": raw}
    return parsed if isinstance(parsed, dict) else {"notes": raw}


def _state(details: dict) -> dict:
    state = details.get(_KEY)
    if not isinstance(state, dict):
        state = {}
    state.setdefault("reasons", {})
    state.setdefault("total", 0)
    state.setdefault("sinceUnlock", 0)
    state.setdefault("strikeIds", [])
    return state


def _save(attendance: Attendance, details: dict, state: dict) -> None:
    details[_KEY] = state
    attendance.securityDetails = json.dumps(details)


def _log(attendance: Attendance, line: str) -> None:
    entry = f"[{utc_now().strftime('%Y-%m-%d %H:%M:%S')}] {line}"
    attendance.theftRemarks = f"{entry}\n{attendance.theftRemarks}" if attendance.theftRemarks else entry


def _seen(state: dict, strike_id: Optional[str]) -> bool:
    return strike_id is not None and strike_id in state["strikeIds"]


def _count(state: dict, violation: str, strike_id: Optional[str]) -> int:
    """Counts one new strike against its reason; returns its number since the last unlock."""
    if strike_id is not None:
        state["strikeIds"] = [*state["strikeIds"], strike_id][-_MAX_REMEMBERED_IDS:]
    state["reasons"][violation] = state["reasons"].get(violation, 0) + 1
    state["total"] += 1
    state["sinceUnlock"] += 1
    return state["sinceUnlock"]


def _lock(attendance: Attendance, violation: str, strike_number: int) -> None:
    attendance.isTheftLocked = 1
    attendance.theftAttemptsLeft = 0
    _log(attendance, f"LOCKED strike #{strike_number}: {violation}")


def _count_down(attendance: Attendance) -> None:
    left = attendance.theftAttemptsLeft if attendance.theftAttemptsLeft is not None else _DEFAULT_ATTEMPTS
    attendance.theftAttemptsLeft = max(0, left - 1)


def record_strike(attendance: Attendance, violation: str, strike_id: str, warning_limit: int) -> StrikeOutcome:
    """A strike the app reported: counted under its reason, and the trainee locked out once their
    strikes since the last unlock reach `warning_limit` - else one off the countdown and a line in
    the log. A resend (same ID) changes nothing; a strike arriving after the lock is counted and
    logged."""
    details = _details(attendance)
    state = _state(details)
    if _seen(state, strike_id):
        return StrikeOutcome(counted=False, locked=bool(attendance.isTheftLocked))
    number = _count(state, violation, strike_id)
    _save(attendance, details, state)
    if not attendance.isTheftLocked and number >= warning_limit:
        _lock(attendance, violation, number)
    else:
        _count_down(attendance)
        _log(attendance, f"STRIKE #{number}: {violation}")
    return StrikeOutcome(counted=True, locked=bool(attendance.isTheftLocked))


def record_lockout(attendance: Attendance, violation: str, strike_number: int, strike_id: Optional[str] = None) -> None:
    """The app locked the trainee out (every app version reports this): locked, and the strike
    counted under its reason unless it already was - by its ID, or, from an older app that sends
    none, because the trainee is already locked (a repeat of the same report). One that already
    locked them adds no second lock line."""
    details = _details(attendance)
    state = _state(details)
    is_new = not _seen(state, strike_id) and (strike_id is not None or not attendance.isTheftLocked)
    if is_new:
        _count(state, violation, strike_id)
        _save(attendance, details, state)
    if not attendance.isTheftLocked:
        _lock(attendance, violation, strike_number)
    elif is_new:
        _log(attendance, f"STRIKE #{state['sinceUnlock']}: {violation}")


def unlocks_used(attendance: Optional[Attendance]) -> int:
    """How many times a trainer lifted this trainee's lockout in this training: the stored count,
    or - for a row unlocked before it was stored - its unlock lines in theftRemarks."""
    if attendance is None:
        return 0
    stored = _state(_details(attendance)).get("unlocks")
    if isinstance(stored, int):
        return stored
    return sum(1 for line in (attendance.theftRemarks or "").splitlines() if UNLOCK_MARK in line)


def record_unlock(attendance: Attendance, username: str, reason: str) -> None:
    """A trainer lifted the lockout: unlocked, PROCTORING_UNLOCK_ADDED_ATTEMPTS more on the
    countdown (added to what was left, never a reset), the unlock counted and logged, and the
    count towards the next lockout starts over. Every reason count, the total, the remembered
    strike IDs and the log are kept."""
    used = unlocks_used(attendance)
    attendance.isTheftLocked = 0
    attendance.theftAttemptsLeft = (attendance.theftAttemptsLeft or 0) + PROCTORING_UNLOCK_ADDED_ATTEMPTS
    details = _details(attendance)
    state = _state(details)
    state["sinceUnlock"] = 0
    state["unlocks"] = used + 1
    _save(attendance, details, state)
    _log(attendance, f"{username}{UNLOCK_MARK}{reason}")
