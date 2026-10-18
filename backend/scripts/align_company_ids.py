"""Brings the trainings and trainees already in a tenant's database in line with the rule new ones
follow since 2026-10-17/18 (user): their `company` holds the company's agency ID from the shared
registry (`agency.agencyUid`), not its name - the same lookup Add Training and trainee registration
use (company_ids.registered_id / tenant_company).

    cd backend
    venv/Scripts/python.exe scripts/align_company_ids.py --tenant samsung                 # preview - writes nothing
    venv/Scripts/python.exe scripts/align_company_ids.py --tenant samsung --apply         # convert
    venv/Scripts/python.exe scripts/align_company_ids.py --tenant samsung --undo backups/align-company-ids-<...>.json

  - A stored name becomes the agency ID registered under it (any spelling - spacing and letter case
    don't matter). A name nobody registered is reported and left as it is: register the company
    first (scripts/add_agency.py), then run this again.
  - A trainee with no company (self-registered before 2026-10-18) gets the tenant's company - every
    trainee now does, and without one a company-scoped admin can't see them. A training with no
    company is only reported.
  - A value that already is a registered agency ID is left alone, so running it again changes nothing.

What --apply changes (each row's old and new value) is saved to backups/ before it is committed; --undo
puts back exactly those values, on rows that still hold what this script wrote.

Run it only once the backend that reads a stored agency ID (company_ids.company_keys / company_names) is
live everywhere it serves this database (Render and any local server): an older backend compares the
company by name only, so a Company Admin there would stop seeing the converted rows.
"""

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app.models  # noqa: E402,F401 - registers every table
from app.core.config import settings  # noqa: E402
from app.models.conference import Conference  # noqa: E402
from app.models.trainee import Trainee  # noqa: E402
from app.services.company_ids import company_names, registered_id, tenant_company  # noqa: E402
from scripts import _value_changes as value_changes  # noqa: E402
from scripts._value_changes import Change  # noqa: E402

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
_TABLES = {"conference": Conference, "trainee": Trainee}
# Rows with no company that get the tenant's (every trainee belongs to its tenant's company).
FILL_BLANK = {"trainee"}


@dataclass
class TablePlan:
    already_ids: int = 0
    blank: int = 0  # rows with no company, left as they are
    not_registered: dict[str, int] = field(default_factory=dict)  # stored name -> rows holding it


@dataclass
class Plan:
    changes: list[Change] = field(default_factory=list)
    tables: dict[str, TablePlan] = field(default_factory=lambda: {table: TablePlan() for table in _TABLES})


def _rows_by_value(db: Session, model) -> dict[Optional[str], list[int]]:
    rows: dict[Optional[str], list[int]] = defaultdict(list)
    for row_id, stored in db.query(model.id, model.company).order_by(model.id):
        rows[stored].append(row_id)
    return rows


def make_plan(db: Session, common_db: Session, tenant_id: str) -> Plan:
    """Each row's company as its agency ID - looked up once per distinct stored value."""
    plan = Plan()
    tenant = tenant_company(common_db, tenant_id)
    by_table = {table: _rows_by_value(db, model) for table, model in _TABLES.items()}
    registered = company_names(common_db, (value for rows in by_table.values() for value in rows))
    for table, rows in by_table.items():
        counts = plan.tables[table]
        for stored, row_ids in rows.items():
            name = (stored or "").strip()
            if not name:
                if table in FILL_BLANK and tenant is not None:
                    plan.changes += [Change(table, row_id, "company", stored, tenant.stored) for row_id in row_ids]
                else:
                    counts.blank += len(row_ids)
            elif name in registered:
                counts.already_ids += len(row_ids)
            elif (agency_id := registered_id(common_db, name)) is None:
                counts.not_registered[stored] = len(row_ids)
            else:
                plan.changes += [Change(table, row_id, "company", stored, agency_id) for row_id in row_ids]
    return plan


def apply(db: Session, plan: Plan, tenant: str) -> tuple[int, Path]:
    """Makes the planned changes, saving every one to backups/ before committing."""
    return value_changes.apply(db, _TABLES, plan.changes, BACKUP_DIR, "align-company-ids", tenant)


def undo(db: Session, backup: Path, tenant: str) -> tuple[int, int]:
    """Puts back the values a backup lists, on rows still holding what the script wrote."""
    return value_changes.undo(db, _TABLES, backup, tenant)


def report(plan: Plan) -> None:
    for table, counts in plan.tables.items():
        converted: dict[tuple[Optional[str], Optional[str]], int] = defaultdict(int)
        for change in plan.changes:
            if change.table == table:
                converted[(change.before, change.after)] += 1
        print(f"{table}: {sum(converted.values())} row(s) to change:")
        for (before, after), count in converted.items():
            print(f"  {before!r}  ->  {after!r}   ({count} row(s))")
        print(f"  {counts.already_ids} row(s) already store an agency ID - left alone.")
        if counts.blank:
            print(f"  {counts.blank} row(s) with no company - left as they are.")
        for name, count in counts.not_registered.items():
            print(f"  {name!r} isn't registered in `agency` - {count} row(s) left as they are.")
        print()
    if any(counts.not_registered for counts in plan.tables.values()):
        print("Register a company with scripts/add_agency.py (companyName spelled as above), then run this again.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="make the changes (default: preview only)")
    parser.add_argument("--undo", type=Path, metavar="BACKUP", help="put back exactly what a backup lists")
    parser.add_argument("--tenant", default=settings.DEFAULT_TENANT_ID)
    args = parser.parse_args()
    if args.apply and args.undo:
        parser.error("give --apply or --undo, not both")

    # local: needs the app's settings, never the test ones
    from app.database.common import CommonSessionLocal
    from scripts._tenant_db import tenant_engine

    engine = tenant_engine(args.tenant)
    print(f"Tenant {args.tenant!r} - database {engine.url.render_as_string(hide_password=True)}\n")
    with sessionmaker(bind=engine)() as db:
        if args.undo:
            done, listed = undo(db, args.undo, args.tenant)
            print(f"Put back {done} of {listed} value(s) from {args.undo}")
            return
        with CommonSessionLocal() as common_db:
            plan = make_plan(db, common_db, args.tenant)
        report(plan)
        if not args.apply:
            print(f"Preview only: {len(plan.changes)} value(s) would change. Run again with --apply to change them.")
            return
        done, backup = apply(db, plan, args.tenant)
        print(f"Changed {done} value(s). Undo file: {backup}")


if __name__ == "__main__":
    main()
