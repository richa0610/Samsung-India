"""A training (`conference` row) as the other system stores it (user, 2026-10-17) - the one module
that knows that format. It reads a stored row in the words the rest of this app works with, and
turns those words back into what gets stored.

Everything else in the app - and its API, so the phone app is unchanged - keeps one vocabulary:

    session status   "Scheduled" / "Ongoing" / "Completed" / "Cancelled"
    module           ATTENDANCE / STANDARD_TEST / LIVE_QUIZ / SURVEY
    quiz state       IDLE (the lobby) / QUESTION_LIVE / LEADERBOARD / FINISHED
    quiz clock       Unix-epoch milliseconds
    session flow     {"attendance": {...}, "standardTest": {...}, "liveQuiz": {...}, "survey": {...}}
    times            "10:00 AM"

What is stored is the other system's:

    conferenceStatus  "Scheduled" / "Started" / "Session Completed" / "Cancelled"
    activeModuleId    "Attendance_0" / "Assessment_<set>" / "Quiz_<set>" / "Survey_<set>"; "" once
                      the session has ended, NULL before it starts
    liveQuizState     IDLE (never opened) / WAITING (open, between questions) / QUESTION_LIVE /
                      LEADERBOARD / CLOSED (finished)
    liveTimerEndsAt   the India date-time as a number, YYYYMMDDHHMMSS
    sessionConfig     a JSON list of the modules in run order (write_session_config)
    times             "14:00"

and in `conference_activity_log` (the Execution Flow): the module's ID as above ("" for an entry
about the whole session), the session's start / end as STARTED / STOPPED, India time.

Rows written before (Ongoing, LIVE_QUIZ, FINISHED, epoch milliseconds, the {...} flow, "10:00 AM",
SESSION_STARTED, UTC log times) read exactly as they did, so no row has to be converted first;
scripts/align_conference_history.py tidies them into the new format."""

import html
import json
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import case, func

from app.core.constants import LIVE_QUIZ_STATE_FINISHED, LIVE_QUIZ_STATE_IDLE
from app.utils.date_utils import IST, time_to_minutes, to_stored_time, to_venue_time
from app.utils.places import place_name
from app.utils.status import title_status

# --- Session status ---------------------------------------------------------------------------

SCHEDULED = "Scheduled"
CANCELLED = "Cancelled"
# This app's words for a started / finished session, and what is stored for each.
RUNNING = "Ongoing"
COMPLETED = "Completed"
STORED_RUNNING = "Started"
STORED_COMPLETED = "Session Completed"

_RUNNING_WORDS = ("started", "ongoing", "live")
_COMPLETED_WORDS = ("session completed", "completed")
_STORED_STATUS = {RUNNING: STORED_RUNNING, COMPLETED: STORED_COMPLETED}
# India time is UTC + 5:30 (no daylight saving).
_INDIA_OFFSET = timedelta(hours=5, minutes=30)


def session_status(stored: Optional[str]) -> Optional[str]:
    """A stored `conferenceStatus` in this app's words: "Started" (and the older "Ongoing" / "Live")
    is "Ongoing", "Session Completed" (and "Completed") is "Completed", anything else Title-Cased."""
    word = (stored or "").strip().lower()
    if word in _RUNNING_WORDS:
        return RUNNING
    if word in _COMPLETED_WORDS:
        return COMPLETED
    return title_status(stored.strip()) if stored else stored


def stored_status(status: str) -> str:
    """What to store for a session status given in this app's words."""
    return _STORED_STATUS.get(status, status)


def is_running(conference) -> bool:
    return session_status(conference.conferenceStatus) == RUNNING


def is_completed(conference) -> bool:
    return session_status(conference.conferenceStatus) == COMPLETED


def is_cancelled(conference) -> bool:
    return session_status(conference.conferenceStatus) == CANCELLED


def status_sql(column):
    """SQL twin of `session_status`, lower-cased: 'ongoing', 'completed', or the stored word."""
    word = func.lower(func.trim(func.coalesce(column, "")))
    return case((word.in_(_RUNNING_WORDS), "ongoing"), (word.in_(_COMPLETED_WORDS), "completed"), else_=word)


# --- Session flow (`sessionConfig`) -----------------------------------------------------------

# The flow's module keys in this app's session-flow dict, and each one's stored "type".
_FLOW_TYPES = {"attendance": "Attendance", "standardTest": "Assessment", "liveQuiz": "Quiz", "survey": "Survey"}
_FLOW_KEY_BY_TYPE = {stored.lower(): key for key, stored in _FLOW_TYPES.items()}
# The unlock condition this app's form calls "Manual Broadcast" is stored as "Manual".
AUTOMATIC_UNLOCK = "Automatic"
MANUAL_UNLOCK = "Manual Broadcast"
_STORED_MANUAL_UNLOCK = "Manual"


def _flag(value: Any) -> bool:
    return value is True or str(value or "").strip().lower() in ("1", "true", "yes")


def _count(value: Any) -> Optional[int]:
    text = str(value if value is not None else "").strip()
    return int(text) if text.isdigit() else None


def _without_blanks(values: dict) -> dict:
    return {key: value for key, value in values.items() if value is not None and value != ""}


def _attendance_in(config: dict) -> dict:
    return {
        **_without_blanks({
            "checkInOpens": to_venue_time(config.get("checkInTime")),
            "checkOutCloses": to_venue_time(config.get("checkOutTime")),
        }),
        "geoFencing": _flag(config.get("geoFencing")),
    }


def _module_in(item: dict, config: dict) -> dict:
    unlock = (config.get("unlockCondition") or "").strip()
    return {
        **_without_blanks({
            "assessmentSuiteUid": (item.get("linkedUid") or "").strip(),
            "questionCount": _count(item.get("questionCount")),
            "startTime": to_venue_time(config.get("startTime")),
            "endTime": to_venue_time(config.get("endTime")),
            "unlockCondition": MANUAL_UNLOCK if unlock == _STORED_MANUAL_UNLOCK else unlock,
        }),
        "checkIn": _flag(config.get("checkInRequired")),
    }


def _stored_modules(stored: Optional[str]) -> list[dict]:
    """The stored module list (the other system's shape); [] for a missing, malformed or older
    (dict-shaped) value."""
    try:
        parsed = json.loads(stored) if stored else None
    except (ValueError, TypeError):
        return []
    return [item for item in parsed if isinstance(item, dict)] if isinstance(parsed, list) else []


def read_session_config(stored: Optional[str]) -> dict:
    """A stored `sessionConfig` as this app's session-flow dict. The other system's list is read
    one module of each kind - the first, as it runs first (user, 2026-10-17); a dict written
    before is returned as it is; anything unreadable is {}."""
    try:
        parsed = json.loads(stored) if stored else None
    except (ValueError, TypeError):
        return {}
    if isinstance(parsed, dict):
        return parsed
    flow: dict = {}
    for item in _stored_modules(stored):
        key = _FLOW_KEY_BY_TYPE.get(str(item.get("type") or "").strip().lower())
        if key is None or key in flow:
            continue
        config = item.get("config") if isinstance(item.get("config"), dict) else {}
        flow[key] = _attendance_in(config) if key == "attendance" else _module_in(item, config)
    return flow


def _attendance_out(block: dict, conference_date: str) -> dict:
    return {
        "type": _FLOW_TYPES["attendance"],
        "config": {
            "date": conference_date,
            "checkInTime": to_stored_time(block.get("checkInOpens")),
            "checkOutTime": to_stored_time(block.get("checkOutCloses")),
            "geoFencing": "1" if block.get("geoFencing") else "0",
        },
    }


def _module_out(key: str, block: dict, conference_date: str) -> dict:
    config = {
        "date": conference_date,
        "startTime": to_stored_time(block.get("startTime")),
        "endTime": to_stored_time(block.get("endTime")),
    }
    if block.get("checkIn"):
        config["checkInRequired"] = "1"
    config["unlockCondition"] = AUTOMATIC_UNLOCK if block.get("unlockCondition") == AUTOMATIC_UNLOCK else _STORED_MANUAL_UNLOCK
    count = block.get("questionCount")
    return {
        "type": _FLOW_TYPES[key],
        "linkedUid": block.get("assessmentSuiteUid") or "",
        "questionCount": str(count) if count is not None else "",
        "config": config,
    }


def _run_order(item: dict) -> int:
    config = item["config"]
    minutes = time_to_minutes(config.get("checkInTime") or config.get("startTime"))
    if minutes is not None:
        return minutes
    # No planned time: the attendance check-in still opens the session; anything else runs last.
    return -1 if item["type"] == _FLOW_TYPES["attendance"] else 10**9


def write_session_config(flow: dict, conference_date: Optional[str]) -> Optional[str]:
    """What to store for this app's session-flow dict: the other system's list - each module with its
    question set and settings, every value a string, in the order they run (by planned time, ties
    keeping Attendance / Test / Quiz / Survey order). None when the flow has no module."""
    items = []
    for key in _FLOW_TYPES:
        block = flow.get(key)
        if block:
            build = _attendance_out(block, conference_date or "") if key == "attendance" else _module_out(key, block, conference_date or "")
            items.append(build)
    if not items:
        return None
    return json.dumps(sorted(items, key=_run_order), separators=(",", ":"))


def has_attendance(conference) -> bool:
    """Whether the session flow includes the Attendance check-in: the other system lists it as a
    module (and keeps `enableCheckIn` 0); a row this app wrote before has `enableCheckIn` set."""
    if _stored_modules(conference.sessionConfig):
        return "attendance" in read_session_config(conference.sessionConfig)
    return bool(conference.enableCheckIn)


def live_quiz_suite_uid(conference) -> Optional[str]:
    """The question set the session's Live Quiz runs."""
    return (read_session_config(conference.sessionConfig).get("liveQuiz") or {}).get("assessmentSuiteUid")


def quiz_suite_uids(conference) -> set[str]:
    """Every Live Quiz question set the session's flow lists - the Python twin of
    dashboard_repository.live_quiz_suite_is, so the two must match exactly: each "Quiz" module's
    text `linkedUid` in the other system's list (a training from that system may list more than
    one; all their results count as marks), or the older dict's liveQuiz set."""
    modules = _stored_modules(conference.sessionConfig)
    if modules:
        return {
            item["linkedUid"]
            for item in modules
            if item.get("type") == _FLOW_TYPES["liveQuiz"] and isinstance(item.get("linkedUid"), str) and item["linkedUid"]
        }
    suite = live_quiz_suite_uid(conference)
    return {suite} if isinstance(suite, str) and suite else set()


def module_suite_uid(conference, module_key: str) -> Optional[str]:
    """The question set a trainee answers in this module: the Standard Test, Live Quiz or Survey
    set. None for ATTENDANCE, or a module whose set isn't chosen."""
    if module_key == "STANDARD_TEST":
        return conference.postAssessmentUid or None
    if module_key == "LIVE_QUIZ":
        return live_quiz_suite_uid(conference)
    if module_key == "SURVEY":
        return conference.surveyUid or None
    return None


# --- The running module (`activeModuleId`) ----------------------------------------------------

_MODULE_TYPES = {"ATTENDANCE": "Attendance", "STANDARD_TEST": "Assessment", "LIVE_QUIZ": "Quiz", "SURVEY": "Survey"}
_MODULE_BY_TYPE = {stored.lower(): key for key, stored in _MODULE_TYPES.items()}
# No module: what `activeModuleId` holds once the session has ended, and a session-level entry's
# `moduleId` in the Execution Flow log.
NO_MODULE = ""


def module_key(stored: Optional[str]) -> Optional[str]:
    """A stored module ID ("Quiz_AS2684628", or this app's key "LIVE_QUIZ" written before) as this
    app's key; None for none or one it doesn't know."""
    stored = (stored or "").strip()
    if not stored:
        return None
    if stored in _MODULE_TYPES:  # written before: the key itself
        return stored
    return _MODULE_BY_TYPE.get(stored.split("_", 1)[0].lower())


def active_module(conference) -> Optional[str]:
    """The module running now, as this app's key (LIVE_QUIZ, ...), or None."""
    return module_key(conference.activeModuleId)


def module_id(conference, module_key: Optional[str]) -> Optional[str]:
    """What `activeModuleId` (and the Execution Flow log) stores for `module_key`: its type and
    question set ("Quiz_AS2684628"); "Attendance_0" for the attendance check-in. None for no module."""
    if module_key is None:
        return None
    return f"{_MODULE_TYPES[module_key]}_{module_suite_uid(conference, module_key) or 0}"


# --- The Execution Flow log (`conference_activity_log`) ---------------------------------------
#
# Stored the other system's way (user, 2026-10-17): `moduleId` is module_id's value ("" for an
# entry about the whole session), the session's start / end are STARTED / STOPPED with no module,
# `timestamp` is India time. Rows this app wrote before keep this app's keys (or NULL), the
# SESSION_STARTED / SESSION_ENDED actions and UTC; both read the same through these functions.

LOG_STARTED = "STARTED"
LOG_STOPPED = "STOPPED"
# This app's words for the session-level entries.
SESSION_STARTED = "SESSION_STARTED"
SESSION_ENDED = "SESSION_ENDED"
_STORED_SESSION_ACTIONS = {SESSION_STARTED: LOG_STARTED, SESSION_ENDED: LOG_STOPPED}
_SESSION_ACTIONS = {stored: action for action, stored in _STORED_SESSION_ACTIONS.items()}


def log_columns(conference, module: Optional[str], action: str) -> dict:
    """The `moduleId` / `action` an entry about `module` (None = the whole session) is stored with."""
    return {"moduleId": module_id(conference, module) or NO_MODULE, "action": _STORED_SESSION_ACTIONS.get(action, action)}


def written_before(entry) -> bool:
    """A log row this app wrote before 2026-10-17: its moduleId is NULL or this app's own key."""
    return entry.moduleId is None or entry.moduleId.strip() in _MODULE_TYPES


def log_module(entry) -> Optional[str]:
    """The module a log row is about, as this app's key; None for the whole session."""
    return module_key(entry.moduleId)


def log_action(entry) -> str:
    """A log row's action in this app's words: a session-level STARTED / STOPPED is
    SESSION_STARTED / SESSION_ENDED; the rest as stored."""
    action = (entry.action or "").strip().upper()
    if not (entry.moduleId or "").strip():
        return _SESSION_ACTIONS.get(action, action)
    return action


def log_time(entry) -> datetime:
    """When a log row was written, in India time (a row written before was stored in UTC)."""
    return entry.timestamp + _INDIA_OFFSET if written_before(entry) else entry.timestamp


def gps_override_remark(latitude: float, longitude: float) -> str:
    """The session-start entry's remark when the trainer moved the venue location: where to."""
    return f"GPS_OVERRIDE: {float(latitude):.6f}, {float(longitude):.6f}"


# --- Live Quiz state and clock ----------------------------------------------------------------

QUIZ_NOT_OPENED = "IDLE"
QUIZ_WAITING = "WAITING"
QUIZ_CLOSED = "CLOSED"
_STORED_QUIZ_STATE = {LIVE_QUIZ_STATE_IDLE: QUIZ_WAITING, LIVE_QUIZ_STATE_FINISHED: QUIZ_CLOSED}


def quiz_state(conference) -> str:
    """The stored Live Quiz state in this app's words: CLOSED (and the older FINISHED) is FINISHED;
    IDLE, WAITING or nothing is IDLE - the lobby; the rest as stored."""
    stored = (conference.liveQuizState or "").strip().upper()
    if stored in (QUIZ_CLOSED, LIVE_QUIZ_STATE_FINISHED):
        return LIVE_QUIZ_STATE_FINISHED
    if stored in ("", QUIZ_NOT_OPENED, QUIZ_WAITING):
        return LIVE_QUIZ_STATE_IDLE
    return stored


def set_quiz_state(conference, state: str) -> None:
    """Stores a Live Quiz state given in this app's words (the lobby is WAITING, finished is CLOSED)."""
    conference.liveQuizState = _STORED_QUIZ_STATE.get(state, state)


_CLOCK_FORMAT = "%Y%m%d%H%M%S"
# Every YYYYMMDDHHMMSS number is at least this; an epoch-milliseconds reading (written before) stays
# below it until the year 2286.
_CLOCK_FLOOR = 10**13


def timer_ends_ms(conference) -> Optional[int]:
    """When the live question's time runs out, as epoch milliseconds; None when no clock is set."""
    stored = conference.liveTimerEndsAt
    if not stored:
        return None
    stored = int(stored)
    if stored < _CLOCK_FLOOR:
        return stored
    try:
        ends = datetime.strptime(str(stored), _CLOCK_FORMAT).replace(tzinfo=IST)
    except ValueError:
        return None
    return int(ends.timestamp()) * 1000


def set_timer_ends(conference, epoch_ms: int) -> None:
    """Stores when the live question's time runs out - the India date-time, to the nearest second."""
    ends = datetime.fromtimestamp(round(epoch_ms / 1000), tz=IST)
    conference.liveTimerEndsAt = int(ends.strftime(_CLOCK_FORMAT))


# --- Values written when a training is created ------------------------------------------------

NOT_ASSIGNED = "Not Assigned"
NO_FILE = "defaultfile.png"
RESIDENTIAL = "Residential Conference"
NON_RESIDENTIAL = "Non-Residential Conference"


def stored_or_not_assigned(value: Optional[str]) -> str:
    """A training hub / venue as stored: the value, or "Not Assigned" when there is none."""
    return (value or "").strip() or NOT_ASSIGNED


def assigned(value: Optional[str]) -> Optional[str]:
    """A stored training hub / venue, or None for none ("Not Assigned" or blank)."""
    text = (value or "").strip()
    return None if not text or text.lower() == NOT_ASSIGNED.lower() else text


def not_assigned_sql(column):
    """SQL twin of `assigned`: NULL for a blank or "Not Assigned" value."""
    return func.nullif(func.nullif(func.trim(func.coalesce(column, "")), ""), NOT_ASSIGNED)


def uploaded(value: Optional[str]) -> Optional[str]:
    """A stored file path, or None while nothing is uploaded (blank or "defaultfile.png")."""
    text = (value or "").strip()
    return None if not text or text == NO_FILE else text


def stored_place(value: Optional[str]) -> Optional[str]:
    """A state / district as stored: in capitals ("NEW DELHI"), spaces tidied; None when blank."""
    return " ".join((value or "").split()).upper() or None


def location_label(conference) -> Optional[str]:
    """Where a training is, as the app shows it: "New Delhi, Delhi" (stored "NEW DELHI" / "DELHI")."""
    return ", ".join(filter(None, [place_name(conference.district), place_name(conference.state)])) or None


def conference_type(residential: bool) -> str:
    return RESIDENTIAL if residential else NON_RESIDENTIAL


def is_residential(conference) -> bool:
    """True for a residential training ("Residential Conference" - not "Non-Residential ...")."""
    return (conference.conferenceType or "").strip().lower().startswith("residential")


def trainer_label(name: Optional[str], username: Optional[str]) -> Optional[str]:
    """`trainerName` as stored: "Demo Trainer (demotrainer)"; just the one that's known otherwise."""
    name, username = (name or "").strip(), (username or "").strip()
    if name and username and name != username:
        return f"{name} ({username})"
    return name or username or None


def creation_note(residential: bool, author_name: str, author_id: str, conference_uid: str) -> str:
    """`masterRemarks` for a new training: "New Non Residential Conference added by Arun (AGT001) |
    UID: CONF2675966"."""
    kind = "Residential" if residential else "Non Residential"
    return f"New {kind} Conference added by {author_name} ({author_id}) | UID: {conference_uid}"


_LINE_BREAK = re.compile(r"<br\s*/?>|</p>\s*<p[^>]*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


def stored_remark(text: Optional[str]) -> Optional[str]:
    """An approval note as stored: one HTML paragraph ("<p>Approved</p>"), its text escaped."""
    text = (text or "").strip()
    return f"<p>{html.escape(text)}</p>" if text else None


def remark_text(stored: Optional[str]) -> Optional[str]:
    """A stored approval note as plain text: paragraphs and <br> become new lines, other tags are
    dropped, entities (&nbsp;) are read."""
    if not stored:
        return stored
    text = html.unescape(_TAG.sub("", _LINE_BREAK.sub("\n", stored))).replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line) or None
