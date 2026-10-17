"""How a session's modules actually played out, read from its activity log (conference_activity_log):
the Execution Flow rows, the audit log, the Session Heroes cards and the time modules were live.

The log is read through conference_format (log_module / log_action / log_time): rows are stored the
other system's way since 2026-10-17 (module IDs, India time), and rows written before still read the
same."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import MODULE_LABELS
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.repositories import activity_log_repository, admin_repository, assessment_repository, trainee_repository
from app.schemas.training import AuditLogEntry, ExecutionFlowItem, SessionHeroStat
from app.services.module_flow import configured_modules, live_quiz_suite_uid, module_planned_minutes
from app.utils.conference_format import active_module, is_running, log_action, log_module, log_time
from app.utils.date_utils import ist_now, ist_to_iso


def activity_log_list(db: Session, conference_uid: str) -> list[ConferenceActivityLog]:
    return activity_log_repository.list_for_conference(db, conference_uid)


def _by_module(logs: list[ConferenceActivityLog]) -> dict[str, list[ConferenceActivityLog]]:
    logs_by_module: dict[str, list[ConferenceActivityLog]] = {}
    for log in logs:
        logs_by_module.setdefault(log_module(log), []).append(log)
    return logs_by_module


def execution_flow(db: Session, conference: Conference) -> list[ExecutionFlowItem]:
    modules = configured_modules(conference)
    if not modules:
        return []

    logs_by_module = _by_module(activity_log_list(db, conference.conferenceUid))

    planned_minutes = module_planned_minutes(conference)
    now = ist_now()
    items: list[ExecutionFlowItem] = []
    for module_key in modules:
        module_logs = logs_by_module.get(module_key, [])
        starts = [entry for entry in module_logs if log_action(entry) == "STARTED"]
        stops = [entry for entry in module_logs if log_action(entry) == "STOPPED"]

        # A module can run more than once (Restart), so compare counts rather
        # than "has a STARTED / has a STOPPED": more starts than stops means
        # it's live right now; the latest pair is the run we report on.
        # Guarded by the module actually being `activeModuleId` - a stray
        # extra STARTED with no matching STOPPED (e.g. from a since-fixed
        # auto-advance race) would otherwise leave this permanently showing
        # "Running" with no way to stop it, even after the session ended.
        is_actually_running = (
            len(starts) > len(stops)
            and is_running(conference)
            and active_module(conference) == module_key
        )
        if is_actually_running:
            item_status = "Running"
            first_started = starts[0]
            last_started = starts[-1]
            elapsed = int((now - log_time(last_started)).total_seconds())
            started_at = ist_to_iso(log_time(first_started))
            ended_at = None
        elif starts:
            item_status = "Completed"
            first_started = starts[0]
            # Prefer the real last STOPPED; fall back to the last STARTED as
            # a synthetic end if the log is inconsistent (more starts than
            # stops but this isn't actually the live module) rather than
            # showing a runaway elapsed time.
            last_stopped = stops[-1] if stops else starts[-1]
            elapsed = int((log_time(last_stopped) - log_time(starts[-1])).total_seconds())
            started_at = ist_to_iso(log_time(first_started))
            ended_at = ist_to_iso(log_time(last_stopped))
        else:
            item_status = "Pending"
            elapsed = None
            started_at = None
            ended_at = None

        items.append(
            ExecutionFlowItem(
                moduleKey=module_key,
                label=MODULE_LABELS.get(module_key, module_key.title()),
                status=item_status,
                startedAt=started_at,
                endedAt=ended_at,
                elapsedSeconds=elapsed,
                assignedMinutes=planned_minutes.get(module_key),
            )
        )

    # `canStart`: session live, nothing else running, this module hasn't run
    # yet, every module ahead of it is done - the trainer walks the flow
    # forward one manual Start at a time.
    # `canRestart`: a finished module can be re-run, but only while no other
    # module is currently live.
    session_idle = is_running(conference) and active_module(conference) is None
    for index, item in enumerate(items):
        item.canStart = (
            session_idle
            and item.status == "Pending"
            and all(earlier.status == "Completed" for earlier in items[:index])
        )
        item.canRestart = session_idle and item.status == "Completed"
    return items


def _suite_for_module(conference: Conference, module_key: str) -> Optional[str]:
    """Which assessment suite a module runs against. Only STANDARD_TEST and
    LIVE_QUIZ have one."""
    if module_key == "STANDARD_TEST":
        return conference.postAssessmentUid
    if module_key == "LIVE_QUIZ":
        return live_quiz_suite_uid(conference)
    return None


def active_module_question_count(db: Session, conference: Conference) -> Optional[int]:
    """Question count of the currently-live module's suite - drives the
    "Targeted N QPs" pill on the Active Module card."""
    suite_uid = _suite_for_module(conference, active_module(conference) or "")
    if not suite_uid:
        return None
    return assessment_repository.count_questions_for_suite(db, suite_uid)


def session_heroes(db: Session, conference: Conference) -> list[SessionHeroStat]:
    """Per-module quiz/test summary (participants, average %, best %, top
    scorer) for the Session Heroes cards - from the latest attempt each
    trainee made on that module's suite."""
    hero_modules = [m for m in ("LIVE_QUIZ", "STANDARD_TEST") if m in configured_modules(conference)]
    if not hero_modules:
        return []

    all_results = assessment_repository.list_results_for_conferences(db, [conference.conferenceUid])
    latest_by_suite: dict[str, dict[str, object]] = {}
    for r in all_results:  # ordered attemptNumber desc -> first seen per trainee is latest
        latest_by_suite.setdefault(r.assessmentSuiteUid, {}).setdefault(r.traineeUid, r)

    per_module = []
    for module_key in hero_modules:
        suite_uid = _suite_for_module(conference, module_key)
        rows = list(latest_by_suite.get(suite_uid, {}).values()) if suite_uid else []
        best = max(rows, key=lambda r: float(r.percentage)) if rows else None
        per_module.append((module_key, rows, best))

    best_uids = {best.traineeUid for _, _, best in per_module if best}
    names = (
        {t.traineeUid: t.name for t in trainee_repository.get_by_uids(db, best_uids)} if best_uids else {}
    )

    heroes: list[SessionHeroStat] = []
    for module_key, rows, best in per_module:
        pcts = [float(r.percentage) for r in rows]
        heroes.append(
            SessionHeroStat(
                moduleKey=module_key,
                label=MODULE_LABELS.get(module_key, module_key),
                participants=len(rows),
                averagePercent=round(sum(pcts) / len(pcts), 1) if pcts else 0.0,
                bestPercent=round(max(pcts), 1) if pcts else 0.0,
                topName=names.get(best.traineeUid) if best else None,
            )
        )
    return heroes


def _pair_runs(
    module_logs: list[ConferenceActivityLog],
) -> list[tuple[ConferenceActivityLog, Optional[ConferenceActivityLog]]]:
    """Turns a module's chronological STARTED/STOPPED events into
    (started, stopped) run pairs - a module can run more than once if
    `advance-module` ever cycles back around to it."""
    runs: list[tuple[ConferenceActivityLog, Optional[ConferenceActivityLog]]] = []
    open_start: Optional[ConferenceActivityLog] = None
    for log in module_logs:
        if log_action(log) == "STARTED":
            if open_start is not None:
                runs.append((open_start, None))
            open_start = log
        elif log_action(log) == "STOPPED" and open_start is not None:
            runs.append((open_start, log))
            open_start = None
    if open_start is not None:
        runs.append((open_start, None))
    return runs


def module_active_seconds(db: Session, conference: Conference) -> Optional[int]:
    """Total wall-clock time any module has actually been running - the sum
    of each configured module's own run durations from
    ConferenceActivityLog (via _pair_runs, so a module that ran more than
    once via Restart has every run counted, not just the latest) - not the
    raw time since the session started, which would also count time before
    the first module went live or any gap between one module stopping and
    the next one starting."""
    if not conference.actualStartedAt:
        return None

    modules = configured_modules(conference)
    if not modules:
        return None

    logs_by_module = _by_module(activity_log_list(db, conference.conferenceUid))

    now = ist_now()
    total_seconds = 0
    for module_key in modules:
        for started, stopped in _pair_runs(logs_by_module.get(module_key, [])):
            end_point = log_time(stopped) if stopped else now
            total_seconds += int((end_point - log_time(started)).total_seconds())
    return total_seconds


def _resolve_performer_names(db: Session, usernames: set[str]) -> dict[str, str]:
    """`performedBy` values written before 2026-10-17 are either an `Admin` username (Common DB) or
    an `AgencyTeam` username (this tenant's DB); since then it is the person's name (the other
    system's way), which no lookup matches and is shown as stored. This function is called
    several layers deep from many endpoints (audit log / execution flow
    attribution), so rather than threading a `common_db` session through
    every one of those call chains, it opens its own short-lived Common DB
    session just for the Admin half of the lookup."""
    if not usernames:
        return {}
    names: dict[str, str] = {}

    from app.database.common import CommonSessionLocal

    common_db = CommonSessionLocal()
    try:
        for admin in admin_repository.get_admins_by_usernames(common_db, usernames):
            names[admin.username] = admin.name or admin.username
    finally:
        common_db.close()

    remaining = usernames - names.keys()
    if remaining:
        for agent in admin_repository.get_agents_by_usernames(db, remaining):
            names[agent.username] = agent.name or agent.username
    return names


def audit_log(db: Session, conference: Conference) -> list[AuditLogEntry]:
    modules = configured_modules(conference)
    if not modules:
        return []

    logs = activity_log_list(db, conference.conferenceUid)
    logs_by_module = _by_module(logs)

    performer_names = _resolve_performer_names(db, {log.performedBy for log in logs if log.performedBy})

    now = ist_now()
    entries: list[AuditLogEntry] = []

    # Schedule overrides (recorded by start_training when a trainer starts a
    # session earlier or later than its scheduled time) sit at the top of the
    # log - they happen before any module runs.
    for log in logs:
        if log_action(log) != "SCHEDULE_OVERRIDE":
            continue
        who = performer_names.get(log.performedBy, log.performedBy) if log.performedBy else None
        entries.append(
            AuditLogEntry(
                moduleKey="SCHEDULE_OVERRIDE",
                label="Schedule override",
                runNumber=1,
                startedAt=ist_to_iso(log_time(log)),
                endedAt=ist_to_iso(log_time(log)),
                elapsedSeconds=None,
                isRunning=False,
                startedBy=who,
                note=log.locationRemark,
            )
        )

    for module_key in modules:
        runs = _pair_runs(logs_by_module.get(module_key, []))
        for run_number, (started, stopped) in enumerate(runs, start=1):
            end_point = log_time(stopped) if stopped else now
            elapsed = int((end_point - log_time(started)).total_seconds())
            entries.append(
                AuditLogEntry(
                    moduleKey=module_key,
                    label=MODULE_LABELS.get(module_key, module_key.title()),
                    runNumber=run_number,
                    startedAt=ist_to_iso(log_time(started)),
                    endedAt=ist_to_iso(log_time(stopped)) if stopped else None,
                    elapsedSeconds=elapsed,
                    isRunning=stopped is None,
                    startedBy=performer_names.get(started.performedBy, started.performedBy) if started.performedBy else None,
                )
            )
    return entries
