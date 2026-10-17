from collections import defaultdict
from datetime import timedelta

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
from app.repositories import activity_log_repository, attendance_repository, conference_repository
from app.utils.conference_format import (
    AUTOMATIC_UNLOCK,
    active_module,
    has_attendance,
    is_running,
    live_quiz_suite_uid,
    log_action,
    log_columns,
    log_module,
    module_id,
    module_suite_uid,
    quiz_suite_uids,
    read_session_config,
    set_quiz_state,
)
from app.utils.date_utils import ist_now, parse_module_start, time_to_minutes, utc_now

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

# How late auto_advance_if_due() is allowed to fire past a module's
# scheduled start before giving up and leaving it to a manual Start instead.
AUTO_ADVANCE_WINDOW = timedelta(minutes=5)

__all__ = [
    "MODULE_LABELS",
    "configured_modules",
    "module_planned_minutes",
    "log_module_action",
    "auto_advance_if_due",
    "live_quiz_suite_uid",
    "module_suite_uid",
    "scored_suite_uids",
    "mark_checkout_if_last_module",
]


# live_quiz_suite_uid / module_suite_uid live in conference_format (the Live Quiz's question set is
# only in `sessionConfig`, in either stored shape); they're re-exported here, where the rest of the
# app has always looked for them.


def scored_suite_uids(conference: Conference) -> set[str]:
    """The question sets whose results count as marks: the Standard Test and the Live Quiz. A
    Survey has no right answers, so its result only records that it was submitted - it never
    counts toward a score, pass / fail, average or rank (dashboard_repository.scored_suite_condition
    is the same rule in SQL)."""
    return {suite for suite in (conference.postAssessmentUid, *quiz_suite_uids(conference)) if suite}


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
    config = read_session_config(conference.sessionConfig)

    modules = []
    # The other system lists Attendance as a module and keeps enableCheckIn 0 (user, 2026-10-17).
    if has_attendance(conference):
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
    config = read_session_config(conference.sessionConfig)

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


def log_module_action(
    db: Session,
    conference: Conference,
    module: str | None,
    action: str,
    performed_by: str,
    latitude: float | None = None,
    longitude: float | None = None,
    location_remark: str | None = None,
) -> None:
    """One Execution Flow event about `module` (this app's key; None = the whole session), stored
    the other system's way (user, 2026-10-17 - conference_format.log_columns): its module ID, the
    session's start / end as STARTED / STOPPED with no module, India time, `performed_by` the
    person's name. Only the session-start entry carries where the trainer was (session_start)."""
    activity_log_repository.add(
        db,
        ConferenceActivityLog(
            conferenceUid=conference.conferenceUid,
            **log_columns(conference, module, action),
            timestamp=ist_now(),
            performedBy=performed_by,
            trainerLat=latitude,
            trainerLng=longitude,
            locationRemark=location_remark,
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
    if not is_running(conference) or active_module(conference):
        return False

    modules = configured_modules(conference)
    if not modules:
        return False

    logs_by_module: dict[str, set[str]] = defaultdict(set)
    for log in activity_log_repository.list_for_conference(db, conference.conferenceUid):
        logs_by_module[log_module(log)].add(log_action(log))

    # First module in flow order that hasn't run yet - the same one
    # start_module would let the trainer start right now.
    next_module = next((m for m in modules if "STARTED" not in logs_by_module[m]), None)
    if next_module is None:
        return False

    config_key = MODULE_CONFIG_KEY.get(next_module)
    if not config_key:
        return False  # ATTENDANCE - no unlockCondition, always manual

    module_config = read_session_config(conference.sessionConfig).get(config_key) or {}
    if module_config.get("unlockCondition") != AUTOMATIC_UNLOCK:
        return False

    start_at = parse_module_start(conference.conferenceDate, module_config.get("startTime"))
    # `conferenceDate`/`startTime` are venue-local (IST) - compare against the
    # venue clock, not the host's naive wall clock. On the UTC-hosted Render
    # server, using datetime.now() here left an auto-advance-due module stuck
    # for up to ~5h30m after it was actually due.
    if start_at is None:
        return False
    now = ist_now()
    if now < start_at:
        return False
    # Auto-start only fires within a tight window of the scheduled time - if
    # the previous module ran long and this module's slot has already
    # passed by more than that, it falls back to a manual Start instead of
    # silently kicking off late (e.g. after a multi-hour delay).
    if now - start_at > AUTO_ADVANCE_WINDOW:
        return False

    # Atomic claim: two concurrent pollers (a trainee's get_current_session
    # and the trainer dashboard fetch, or two trainees) can both reach this
    # point having each read activeModuleId as NULL before either commits -
    # a check-then-act race. Without this, both proceed to log their own
    # STARTED for the same module, which throws off the Execution Flow's
    # start/stop-count pairing and leaves it permanently showing "Running"
    # with no way to stop it, even after the whole session has ended. This
    # UPDATE only succeeds for whichever request's transaction gets there
    # first (MySQL row-locks it until commit); the loser matches 0 rows and
    # backs off without logging anything.
    stored_module = module_id(conference, next_module)
    if not conference_repository.claim_active_module(db, conference.conferenceUid, None, stored_module):
        return False

    conference.activeModuleId = stored_module
    if next_module == "LIVE_QUIZ":
        set_quiz_state(conference, LIVE_QUIZ_STATE_IDLE)
    log_module_action(db, conference, next_module, "STARTED", AUTO_ADVANCE_PERFORMER)
    conference_repository.save(db, conference)
    return True


def mark_checkout_if_last_module(db: Session, conference: Conference, trainee_uid: str, module_key: str) -> None:
    """Records the trainee's check-out moment the instant they finish the
    LAST module in this session's configured flow - whichever module type
    that happens to be (Attendance-only sessions check out on check-in,
    others on their final Standard Test/Live Quiz/Survey submission).

    Called from each module's own completion point (attendance_service's
    check_in/check_in_secure, assessment_service's submit_assessment,
    live_quiz_service's submit_live_quiz) rather than from one central
    place, since "completing a module" means something different for each
    one and there's no single shared completion event to hook.

    Idempotent: only ever sets checkOutTime once per attendance row, so a
    trainee re-submitting (a retest, a second Live Quiz "Final Submit"
    call, etc.) never overwrites their original check-out moment.
    """
    modules = configured_modules(conference)
    if not modules or modules[-1] != module_key:
        return

    attendance = attendance_repository.get_for_conference_and_trainee(db, conference.conferenceUid, trainee_uid)
    if not attendance or attendance.checkOutTime:
        return

    attendance.checkOutTime = utc_now()
