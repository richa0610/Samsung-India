"""Gives every question set (`assessmentsuite`) an ID in the app's own format - ASM<YY><5 digits>,
e.g. ASM2610009 - replacing the older `default:<name>` and hand-written ones (`quiz-galaxy-...`),
and rewrites every place that stores a question set's ID, in one transaction:

    assessmentsuite.assessmentSuiteUid                  the question set itself
    questions / assessment / assessment_results          its questions, answers and scores
        .assessmentSuiteUid
    conference.preAssessmentUid / postAssessmentUid /    a training's tests and survey
        surveyUid
    conference.sessionConfig (JSON)                      every "assessmentSuiteUid" inside it - the
                                                         only link a training has to its Live Quiz

IDs already in the ASM format keep theirs (results and approved demo data point at them); the
others continue after the highest one in use, in the order the rows were created (by id), and
uid_sequence's ASM counter is moved past the last, so the app's next new question set can't
collide. Activity-log text keeps the old IDs - it is history, not a link.

    cd backend
    venv/Scripts/python.exe scripts/migrate_suite_uids.py                      # dry run: the plan only
    venv/Scripts/python.exe scripts/migrate_suite_uids.py --apply              # write it
    venv/Scripts/python.exe scripts/migrate_suite_uids.py --rollback <file>    # put the old IDs back

The target is the tenant's own database, found the way the app finds it (--tenant, default the
default tenant), printed before anything else. --apply first saves the old -> new list to
backups/ (the file --rollback takes). The whole run is one transaction: if any link would end up
pointing at a question set that doesn't exist - and didn't before - nothing is written.
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import text
from sqlalchemy.engine import Connection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.date_utils import ist_now  # noqa: E402
from app.utils.uid import START  # noqa: E402
from scripts._tenant_db import tenant_engine  # noqa: E402

PREFIX = "ASM"
SUITE_ID = re.compile(rf"^{PREFIX}\d{{2}}(\d{{5}})$")

# Every column that holds a question set's ID, besides the question set's own.
REFERENCES = (
    ("questions", "assessmentSuiteUid"),
    ("assessment", "assessmentSuiteUid"),
    ("assessment_results", "assessmentSuiteUid"),
    ("conference", "preAssessmentUid"),
    ("conference", "postAssessmentUid"),
    ("conference", "surveyUid"),
)
CONFIG_KEY = "assessmentSuiteUid"  # inside conference.sessionConfig, at any depth

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"


@dataclass(frozen=True)
class Rename:
    id: int  # assessmentsuite.id - the row, whatever its ID says
    old: Optional[str]
    new: str


def new_suite_id(sequence: int) -> str:
    return f"{PREFIX}{ist_now().year % 100:02d}{sequence:05d}"


# --- plan --------------------------------------------------------------------------------------

def plan(conn: Connection) -> list[Rename]:
    """Which question sets get which new ID: every one not already in the ASM format, by id,
    numbered after the highest ASM number in use and the ASM counter. Reads only."""
    rows = conn.execute(text("SELECT id, assessmentSuiteUid FROM assessmentsuite ORDER BY id")).fetchall()
    in_use = [int(m.group(1)) for _, uid in rows if uid and (m := SUITE_ID.match(uid))]
    sequence = max(max(in_use, default=START - 1) + 1, _counter(conn) or START)
    renames = []
    for row_id, uid in rows:
        if uid and SUITE_ID.match(uid):
            continue
        renames.append(Rename(row_id, uid or None, new_suite_id(sequence)))
        sequence += 1
    return renames


def _counter(conn: Connection) -> Optional[int]:
    return conn.execute(text("SELECT next_val FROM uid_sequence WHERE prefix = :p"), {"p": PREFIX}).scalar()


def reference_counts(conn: Connection, ids: Iterable[str]) -> dict[str, int]:
    """How many rows / training configs point at each of `ids` - what the rename will touch."""
    ids = set(ids)
    counts = {uid: 0 for uid in ids}
    for table, column in REFERENCES:
        for (value,) in conn.execute(text(f"SELECT `{column}` FROM `{table}` WHERE `{column}` IS NOT NULL")):
            if value in counts:
                counts[value] += 1
    for _, config in _configs(conn):
        for value in _config_suite_ids(config):
            if value in counts:
                counts[value] += 1
    return counts


# --- apply / rollback --------------------------------------------------------------------------

def apply(conn: Connection, renames: list[Rename]) -> None:
    """Renames every planned question set and everything that points at it, moves the ASM counter
    past them, and checks nothing was left behind - raising (so the caller's transaction rolls
    back) if a link now points nowhere that didn't before, or an old-format ID remains."""
    _rewrite(conn, [(r.id, r.new) for r in renames], {r.old: r.new for r in renames if r.old})
    _move_counter_past(conn, [r.new for r in renames])
    leftover = [uid for _, uid in conn.execute(text("SELECT id, assessmentSuiteUid FROM assessmentsuite"))
                if not (uid and SUITE_ID.match(uid))]
    if leftover:
        raise RuntimeError(f"{len(leftover)} question set(s) still not in the {PREFIX} format - nothing written")


def rollback(conn: Connection, renames: list[Rename]) -> None:
    """Puts the old IDs back from a saved plan (--apply's backup file). The ASM counter stays where
    it is - leaving numbers unused is harmless, reusing them isn't."""
    _rewrite(conn, [(r.id, r.old) for r in renames], {r.new: r.old for r in renames if r.old})


def _rewrite(conn: Connection, suite_rows: list[tuple[int, Optional[str]]], mapping: dict[str, str]) -> None:
    dangling_before = _dangling(conn)
    for row_id, uid in suite_rows:
        conn.execute(text("UPDATE assessmentsuite SET assessmentSuiteUid = :uid WHERE id = :id"), {"uid": uid, "id": row_id})
    if mapping:
        for table, column in REFERENCES:
            conn.execute(
                text(f"UPDATE `{table}` SET `{column}` = :new WHERE `{column}` = :old"),
                [{"old": old, "new": new} for old, new in mapping.items()],
            )
        for row_id, config in _configs(conn):
            updated = _rename_in_config(config, mapping)
            if updated != config:
                conn.execute(text("UPDATE conference SET sessionConfig = :c WHERE id = :id"),
                             {"c": json.dumps(updated), "id": row_id})
    dangling_after = _dangling(conn)
    grown = {link: n for link, n in dangling_after.items() if n > dangling_before.get(link, 0)}
    if grown:
        raise RuntimeError(f"Links would point at missing question sets: {grown} - nothing written")


def _move_counter_past(conn: Connection, new_ids: list[str]) -> None:
    if not new_ids:
        return
    next_value = max(int(SUITE_ID.match(uid).group(1)) for uid in new_ids) + 1
    current = _counter(conn)
    if current is None:
        conn.execute(text("INSERT INTO uid_sequence (prefix, next_val) VALUES (:p, :v)"), {"p": PREFIX, "v": next_value})
    elif current < next_value:
        conn.execute(text("UPDATE uid_sequence SET next_val = :v WHERE prefix = :p"), {"p": PREFIX, "v": next_value})


# --- sessionConfig JSON ------------------------------------------------------------------------

def _configs(conn: Connection) -> list[tuple[int, object]]:
    """(conference id, parsed sessionConfig) for every training whose config is valid JSON - one
    that isn't is never touched (the app ignores it too)."""
    parsed = []
    for row_id, raw in conn.execute(text("SELECT id, sessionConfig FROM conference WHERE sessionConfig IS NOT NULL")):
        try:
            parsed.append((row_id, json.loads(raw)))
        except (TypeError, ValueError):
            continue
    return parsed


def _config_suite_ids(node) -> list[str]:
    if isinstance(node, dict):
        found = [node[CONFIG_KEY]] if isinstance(node.get(CONFIG_KEY), str) else []
        return found + [uid for value in node.values() for uid in _config_suite_ids(value)]
    if isinstance(node, list):
        return [uid for value in node for uid in _config_suite_ids(value)]
    return []


def _rename_in_config(node, mapping: dict[str, str]):
    """A copy of the config with every "assessmentSuiteUid" in `mapping` renamed; all else as is."""
    if isinstance(node, dict):
        return {
            key: mapping.get(value, value) if key == CONFIG_KEY and isinstance(value, str) else _rename_in_config(value, mapping)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_rename_in_config(value, mapping) for value in node]
    return node


def _dangling(conn: Connection) -> dict[str, int]:
    """Per link, how many point at a question set that doesn't exist."""
    existing = {uid for (uid,) in conn.execute(text("SELECT assessmentSuiteUid FROM assessmentsuite")) if uid}
    counts: dict[str, int] = {}
    for table, column in REFERENCES:
        values = conn.execute(text(f"SELECT `{column}` FROM `{table}` WHERE `{column}` IS NOT NULL AND `{column}` <> ''"))
        counts[f"{table}.{column}"] = sum(1 for (value,) in values if value not in existing)
    counts["conference.sessionConfig"] = sum(
        1 for _, config in _configs(conn) for uid in _config_suite_ids(config) if uid and uid not in existing
    )
    return counts


# --- command line ------------------------------------------------------------------------------

def _print_plan(conn: Connection, renames: list[Rename]) -> None:
    if not renames:
        print("Every question set already has an ASM ID - nothing to do.")
        return
    counts = reference_counts(conn, [r.old for r in renames if r.old])
    print(f"{len(renames)} question set(s) to rename:\n")
    for r in renames:
        uses = counts.get(r.old, 0) if r.old else 0
        print(f"  id {r.id:>4}  {r.old or '(no ID)'!s:<55} -> {r.new}   ({uses} link(s))")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    from app.core.config import settings

    parser.add_argument("--tenant", default=settings.DEFAULT_TENANT_ID)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="write the renames (default: dry run)")
    mode.add_argument("--rollback", metavar="FILE", help="put the old IDs back from a saved plan")
    args = parser.parse_args()

    engine = tenant_engine(args.tenant)
    print(f"Tenant {args.tenant!r} - database {engine.url.render_as_string(hide_password=True)}\n")

    if args.rollback:
        saved = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        renames = [Rename(**r) for r in saved["renames"]]
        with engine.begin() as conn:
            rollback(conn, renames)
        print(f"Rolled back {len(renames)} question set(s) to their old IDs.")
        return

    with engine.begin() as conn:
        renames = plan(conn)
        _print_plan(conn, renames)
        if not args.apply or not renames:
            if renames:
                print("\nDry run - nothing written. Run again with --apply to write it.")
            return
        BACKUP_DIR.mkdir(exist_ok=True)
        backup = BACKUP_DIR / f"suite-uid-migration-{args.tenant}-{datetime.now():%Y%m%d-%H%M%S}.json"
        backup.write_text(json.dumps({"tenant": args.tenant, "renames": [asdict(r) for r in renames]}, indent=2), encoding="utf-8")
        print(f"\nSaved the old -> new list to {backup} (for --rollback).")
        apply(conn, renames)
    print(f"Done: {len(renames)} question set(s) renamed, every link updated.")


if __name__ == "__main__":
    main()
