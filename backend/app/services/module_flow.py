import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.constants import (
    AUTO_ADVANCE_PERFORMER,
    LIVE_QUIZ_STATE_IDLE,
    MODULE_CONFIG_KEY,
    MODULE_LABELS,
    MODULE_SEQUENCE,
)
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.repositories import activity_log_repository, conference_repository
from app.utils.date_utils import parse_module_start, time_to_minutes

# sessionConfig key + planned-start-time field for each module, used to order
# the flow by time.
_MODULE_CONFIG = {
    "ATTENDANCE": ("attendance", "checkInOpens"),
    "STANDARD_TEST": ("standardTest", "startTime"),
    "LIVE_QUIZ": ("liveQuiz", "startTime"),
    "SURVEY": ("survey", "startTime"),
}
# sessionConfig key + (start field, end field) for each module - the planned
# window the trainer set when building the session flow.
_MODULE_TIME_RANGE = {
    "ATTENDANCE": ("attendance", "checkInOpens", "checkOutCloses"),
    "STANDARD_TEST": ("standardTest", "startTime", "endTime"),
    "LIVE_QUIZ": ("liveQuiz", "startTime", "endTime"),
    "SURVEY": ("survey", "startTime", "endTime"),
}
_CANONICAL_INDEX = {key: i for i, key in enumerate(MODULE_SEQUENCE)}

__all__ = [
    "MODULE_LABELS",
    "configured_modules",
    "module_planned_minutes",
    "log_module_action",
    "auto_advance_if_due",
    "live_quiz_suite_uid",
]


def live_quiz_suite_uid(conference: Conference) -> str | None:
    """The assessment suite the Live Quiz module runs against. Unlike the
    other modules it has no dedicated Conference column - it only ever lives
    in `sessionConfig.liveQuiz.assessmentSuiteUid`."""
    if not conference.sessionConfig:
        return None
    try:
        return json.loads(conference.sessionConfig).get("liveQuiz", {}).get("assessmentSuiteUid")
    except (ValueError, AttributeError):
        return None


def _module_start_minutes(module_key: str, config: dict, conference: Conference) -> int | None:
    section, field = _MODULE_CONFIG[module_key]
    raw = (config.get(section) or {}).get(field)
    if raw is None and module_key == "ATTENDANCE":
        raw = conference.conferenceTime
    return time_to_minutes(raw)


def configured_modules(conference: Conference) -> list[str]:
    """Which modules this session's flow includes, in run order - sorted by
    each module's planned start time (from `sessionConfig`). Modules without a
    planned time keep the canonical order and sort last."""
    config = {}
    if conference.sessionConfig:
        try:
            config = json.loads(conference.sessionConfig)
        except ValueError:
            config = {}

    modules = []
    if conference.enableCheckIn:
        modules.append("ATTENDANCE")
    if conference.postAssessmentUid:
        modules.append("STANDARD_TEST")
    if config.get("liveQuiz"):
        modules.append("LIVE_QUIZ")
    if conference.surveyUid:
        modules.append("SURVEY")

    def sort_key(module_key: str) -> tuple[int, int]:
        minutes = _module_start_minutes(module_key, config, conference)
        return (minutes if minutes is not None else 10**9, _CANONICAL_INDEX[module_key])

    return sorted(modules, key=sort_key)


def module_planned_minutes(conference: Conference) -> dict[str, int]:
    """Each configured module's planned duration in minutes, from the
    start/end times the trainer set on it in `sessionConfig` (free-text
    "10:00 AM" values). Modules with no usable start/end pair - or an end
    that isn't after the start - are left out. Drives the "Assigned" time
    budget and the "Total Time Used" gauge on the Session Dashboard."""
    config = {}
    if conference.sessionConfig:
        try:
            config = json.loads(conference.sessionConfig)
        except ValueError:
            config = {}

    planned: dict[str, int] = {}
    for module_key in configured_modules(conference):
        section, start_field, end_field = _MODULE_TIME_RANGE[module_key]
        block = config.get(section) or {}
        start = time_to_minutes(block.get(start_field))
        end = time_to_minutes(block.get(end_field))
        if start is None and module_key == "ATTENDANCE":
            start = time_to_minutes(conference.conferenceTime)
        if start is None or end is None:
            continue
        span = end - start
        if span > 0:
            planned[module_key] = span
    return planned


def log_module_action(db: Session, conference_uid: str, module_id: str, action: str, performed_by: str) -> None:
    activity_log_repository.add(
        db,
        ConferenceActivityLog(
            conferenceUid=conference_uid,
            moduleId=module_id,
            action=action,
            performedBy=performed_by,
        ),
    )


def auto_advance_if_due(db: Session, conference: Conference) -> bool:
    """Starts the next configured module by itself once its planned start
    time has passed - but ONLY when that module's "Unlock Condition" (the
    Add Training per-module setting, stored in `sessionConfig`) is
    "Automatic". A module set to "Manual Broadcast", or one with no
    `unlockCondition` at all (ATTENDANCE has none - see MODULE_CONFIG_KEY),
    still waits for the trainer to tap Start, exactly as before.

    Mirrors every gate `start_module` enforces (session live, nothing else
    running, this module hasn't run, every earlier module finished) so an
    auto-start can never skip ahead of - or race - a manual one. Called from
    both the trainee's `get_current_session` and the trainer dashboard fetch,
    so either side polling is enough to trigger it; no cron needed.

    Returns True if it started something.
    """
    if conference.conferenceStatus != "Ongoing" or conference.activeModuleId:
        return False

    modules = configured_modules(conference)
    if not modules:
        return False

    logs_by_module: dict[str, set[str]] = defaultdict(set)
    for log in activity_log_repository.list_for_conference(db, conference.conferenceUid):
        logs_by_module[log.moduleId].add(log.action)

    # First module in flow order that hasn't run yet - the same one
    # start_module would let the trainer start right now.
    next_module = next((m for m in modules if "STARTED" not in logs_by_module[m]), None)
    if next_module is None:
        return False

    config_key = MODULE_CONFIG_KEY.get(next_module)
    if not config_key:
        return False  # ATTENDANCE - no unlockCondition, always manual

    try:
        module_config = json.loads(conference.sessionConfig or "{}").get(config_key) or {}
    except ValueError:
        return False

    if module_config.get("unlockCondition") != "Automatic":
        return False

    start_at = parse_module_start(conference.conferenceDate, module_config.get("startTime"))
    if start_at is None or datetime.now() < start_at:
        return False

    conference.activeModuleId = next_module
    if next_module == "LIVE_QUIZ":
        conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    log_module_action(db, conference.conferenceUid, next_module, "STARTED", AUTO_ADVANCE_PERFORMER)
    conference_repository.save(db, conference)
    return True
