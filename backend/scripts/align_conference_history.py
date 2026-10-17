"""Brings what this app saved before 2026-10-17 in line with the other system's format (user) - only
what can't be read correctly as it is, because a stored time doesn't say which clock it is on:

  - `conference.actualStartedAt` / `actualEndedAt` this app saved in UTC become India time;
  - `conference_activity_log` rows this app wrote become that system's rows: India time, the module's
    ID ("Quiz_AS2684628" for LIVE_QUIZ, "" for an entry about the whole session) and the session's
    start / end as STARTED / STOPPED. Who did it and the location columns are left as written.

    cd backend
    venv/Scripts/python.exe scripts/align_conference_history.py                  # preview - writes nothing
    venv/Scripts/python.exe scripts/align_conference_history.py --apply          # convert
    venv/Scripts/python.exe scripts/align_conference_history.py --undo backups/align-conference-history-<...>.json

A log row is this app's older kind when its moduleId is NULL or one of this app's module keys
(conference_format.written_before) - so a row converted once, or written since, is never converted
again. A start / end time is checked against the training's own first session start / last session
end in that log, both on the UTC clock: within a few minutes of it, the time was saved in UTC and
moves 5 h 30 min forward; about 5 h 30 min after it, it is already India time and is left alone. A
time with nothing to check it against, or matching neither, is reported and left as it is.

What --apply changes (each value's old and new form) is saved to backups/ before it is committed;
--undo puts back exactly those values, on rows that still hold what this script wrote.

Run it only once the backend that writes the new format is live everywhere it serves this database
(Render and any local server): an older backend would keep adding rows the old way after it.
"""

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app.models  # noqa: E402,F401 - registers every table
from app.core.config import settings  # noqa: E402
from app.models.conference import Conference  # noqa: E402
from app.models.conference_activity_log import ConferenceActivityLog  # noqa: E402
from scripts import _value_changes as value_changes  # noqa: E402
from scripts._value_changes import Change, as_text  # noqa: E402
from app.utils.conference_format import (  # noqa: E402
    SESSION_ENDED,
    SESSION_STARTED,
    log_action,
    log_columns,
    log_module,
    written_before,
)

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
INDIA_OFFSET = timedelta(hours=5, minutes=30)
# How far a stored time may be from its log entry and still be that same moment.
TOLERANCE = timedelta(minutes=5)
# Each converted conference column -> the session-level log entry it is checked against.
TIME_COLUMNS = {"actualStartedAt": SESSION_STARTED, "actualEndedAt": SESSION_ENDED}
_STAMP = value_changes.STAMP
_TABLES = {"conference": Conference, "conference_activity_log": ConferenceActivityLog}
_NO_TRAINING = SimpleNamespace(postAssessmentUid=None, surveyUid=None, sessionConfig=None)


@dataclass
class Plan:
    changes: list[Change] = field(default_factory=list)
    log_rows: int = 0
    already_india: int = 0
    left_alone: list[str] = field(default_factory=list)  # why each unconverted time was left as it is


def _utc(entry: ConferenceActivityLog) -> datetime:
    """A log row's time on the UTC clock, whichever way it was written."""
    return entry.timestamp if written_before(entry) else entry.timestamp - INDIA_OFFSET


def _session_marks(logs: list[ConferenceActivityLog]) -> dict[str, dict[str, datetime]]:
    """Per training, the UTC time of its first session start and its last session end."""
    marks: dict[str, dict[str, datetime]] = {}
    for entry in logs:  # in the order written
        action = log_action(entry)
        if action not in (SESSION_STARTED, SESSION_ENDED):
            continue
        times = marks.setdefault(entry.conferenceUid, {})
        if action == SESSION_ENDED or SESSION_STARTED not in times:
            times[action] = _utc(entry)
    return marks


def _check_time(plan: Plan, conference: Conference, column: str, logged: Optional[datetime]) -> None:
    stored = getattr(conference, column)
    if stored is None:
        return
    where = f"{conference.conferenceUid} {column} {stored:{_STAMP}}"
    if logged is None:
        plan.left_alone.append(f"{where}: no {TIME_COLUMNS[column]} entry to check it against")
    elif abs(stored - logged) <= TOLERANCE:
        plan.changes.append(Change("conference", conference.id, column, as_text(stored), as_text(stored + INDIA_OFFSET)))
    elif abs(stored - (logged + INDIA_OFFSET)) <= TOLERANCE:
        plan.already_india += 1
    else:
        plan.left_alone.append(f"{where}: matches neither clock (log {logged:{_STAMP}} UTC)")


def _convert_log_row(plan: Plan, entry: ConferenceActivityLog, conference: Optional[Conference]) -> None:
    """An older log row as the other system's row: its module ID, action and India time."""
    # A training that is gone has no question set to name the module by: "Quiz_0" and the like.
    stored = log_columns(conference or _NO_TRAINING, log_module(entry), log_action(entry))
    plan.log_rows += 1
    for column, after in (*stored.items(), ("timestamp", as_text(entry.timestamp + INDIA_OFFSET))):
        before = as_text(getattr(entry, column))
        if before != after:
            plan.changes.append(Change("conference_activity_log", entry.id, column, before, after))


def make_plan(db: Session) -> Plan:
    plan = Plan()
    logs = db.query(ConferenceActivityLog).order_by(ConferenceActivityLog.id).all()
    conferences = {c.conferenceUid: c for c in db.query(Conference).order_by(Conference.id)}
    marks = _session_marks(logs)
    for conference in conferences.values():
        for column, action in TIME_COLUMNS.items():
            _check_time(plan, conference, column, marks.get(conference.conferenceUid, {}).get(action))
    for entry in logs:
        if written_before(entry):
            _convert_log_row(plan, entry, conferences.get(entry.conferenceUid))
    return plan


def apply(db: Session, plan: Plan, tenant: str) -> tuple[int, Path]:
    """Makes the planned changes, saving every one to backups/ before committing."""
    return value_changes.apply(db, _TABLES, plan.changes, BACKUP_DIR, "align-conference-history", tenant)


def undo(db: Session, backup: Path, tenant: str) -> tuple[int, int]:
    """Puts back the values a backup lists, on rows still holding what the script wrote."""
    return value_changes.undo(db, _TABLES, backup, tenant)


def report(plan: Plan) -> None:
    times = [c for c in plan.changes if c.table == "conference"]
    print(f"{len(times)} start / end time(s) saved in UTC -> India time:")
    for change in times:
        print(f"  conference #{change.id}  {change.column}  {change.before}  ->  {change.after}")
    print(f"\n{plan.already_india} start / end time(s) already in India time - left alone.")
    if plan.left_alone:
        print(f"\n{len(plan.left_alone)} time(s) left as they are:")
        for line in plan.left_alone:
            print(f"  {line}")
    log_changes = [c for c in plan.changes if c.table == "conference_activity_log"]
    print(f"\n{plan.log_rows} Execution Flow row(s) written the older way -> the other system's way "
          f"({len(log_changes)} value(s); module ID, action, India time).")
    for change in log_changes[:30]:
        print(f"  log #{change.id}  {change.column}  {change.before!r}  ->  {change.after!r}")
    if len(log_changes) > 30:
        print(f"  ... and {len(log_changes) - 30} more (all in the undo file after --apply)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="make the changes (default: preview only)")
    parser.add_argument("--undo", type=Path, metavar="BACKUP", help="put back exactly what a backup lists")
    parser.add_argument("--tenant", default=settings.DEFAULT_TENANT_ID)
    args = parser.parse_args()
    if args.apply and args.undo:
        parser.error("give --apply or --undo, not both")

    from scripts._tenant_db import tenant_engine  # local: needs the app's settings, never the test ones

    engine = tenant_engine(args.tenant)
    print(f"Tenant {args.tenant!r} - database {engine.url.render_as_string(hide_password=True)}\n")
    with sessionmaker(bind=engine)() as db:
        if args.undo:
            done, listed = undo(db, args.undo, args.tenant)
            print(f"Put back {done} of {listed} value(s) from {args.undo}")
            return
        plan = make_plan(db)
        report(plan)
        if not args.apply:
            print(f"\nPreview only: {len(plan.changes)} value(s) would change. Run again with --apply to change them.")
            return
        done, backup = apply(db, plan, args.tenant)
        print(f"\nChanged {done} value(s). Undo file: {backup}")


if __name__ == "__main__":
    main()
