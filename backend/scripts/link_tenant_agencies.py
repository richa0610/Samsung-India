"""Fills `tenants.agency_uid` (user, 2026-10-18): each tenant's company as the shared registry knows it
(`agency.agencyUid`), found by the tenant's `company_name` - any spelling, spacing and letter case
don't matter (company_ids.registered_id, the lookup Add / Edit Training uses).

    cd backend
    venv/Scripts/python.exe scripts/link_tenant_agencies.py                  # preview - writes nothing
    venv/Scripts/python.exe scripts/link_tenant_agencies.py --apply          # fill it
    venv/Scripts/python.exe scripts/link_tenant_agencies.py --undo backups/link-tenant-agencies-<...>.json

Only an empty agency_uid is filled, so running it again changes nothing. Reported, never changed: a
tenant whose company isn't registered yet (register it with scripts/add_agency.py, then run this
again), and one already linked to an ID other than the one its name is registered under.

What --apply changes (each row's old and new value) is saved to backups/ before it is committed; --undo
puts back exactly those values, on rows that still hold what this script wrote.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models.common.tenant_registry import Tenant  # noqa: E402
from app.services.company_ids import registered_id  # noqa: E402
from scripts import _value_changes as value_changes  # noqa: E402
from scripts._value_changes import Change  # noqa: E402

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
# The registry is shared, not one tenant's: the undo file is checked against this instead.
SCOPE = "common"
_TABLES = {"tenants": Tenant}


@dataclass
class Plan:
    changes: list[Change] = field(default_factory=list)
    already_linked: int = 0
    linked_elsewhere: list[str] = field(default_factory=list)
    not_registered: list[str] = field(default_factory=list)


def make_plan(common_db: Session) -> Plan:
    plan = Plan()
    for tenant in common_db.query(Tenant).order_by(Tenant.id):
        agency_id = registered_id(common_db, tenant.company_name)
        stored = (tenant.agency_uid or "").strip()
        label = f"{tenant.tenant_uid} ({tenant.company_name!r})"
        if stored:
            if agency_id is None or stored == agency_id:
                plan.already_linked += 1
            else:
                plan.linked_elsewhere.append(f"{label}: holds {stored}, its name is registered as {agency_id}")
        elif agency_id is None:
            plan.not_registered.append(label)
        else:
            plan.changes.append(Change("tenants", tenant.id, "agency_uid", tenant.agency_uid, agency_id))
    return plan


def apply(common_db: Session, plan: Plan) -> tuple[int, Path]:
    """Makes the planned changes, saving every one to backups/ before committing."""
    return value_changes.apply(common_db, _TABLES, plan.changes, BACKUP_DIR, "link-tenant-agencies", SCOPE)


def undo(common_db: Session, backup: Path) -> tuple[int, int]:
    """Puts back the values a backup lists, on rows still holding what the script wrote."""
    return value_changes.undo(common_db, _TABLES, backup, SCOPE)


def report(plan: Plan, common_db: Session) -> None:
    names = {t.id: f"{t.tenant_uid} ({t.company_name!r})" for t in common_db.query(Tenant)}
    print(f"{len(plan.changes)} tenant(s) to link to their agency:")
    for change in plan.changes:
        print(f"  {names[change.id]}  agency_uid {change.before!r}  ->  {change.after!r}")
    print(f"\n{plan.already_linked} tenant(s) already linked - left alone.")
    if plan.linked_elsewhere:
        print(f"\n{len(plan.linked_elsewhere)} tenant(s) linked to another ID than their name's - left as they are:")
        for line in plan.linked_elsewhere:
            print(f"  {line}")
    if plan.not_registered:
        print(f"\n{len(plan.not_registered)} tenant(s) whose company isn't registered in `agency` yet - left empty:")
        for line in plan.not_registered:
            print(f"  {line}")
        print("Register it with scripts/add_agency.py (companyName = the tenant's company_name), then run this again.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="make the changes (default: preview only)")
    parser.add_argument("--undo", type=Path, metavar="BACKUP", help="put back exactly what a backup lists")
    args = parser.parse_args()
    if args.apply and args.undo:
        parser.error("give --apply or --undo, not both")

    from app.database.common import CommonSessionLocal  # local: needs the app's settings, never the test ones

    with CommonSessionLocal() as common_db:
        print(f"Common database {common_db.get_bind().url.render_as_string(hide_password=True)}\n")
        if args.undo:
            done, listed = undo(common_db, args.undo)
            print(f"Put back {done} of {listed} value(s) from {args.undo}")
            return
        plan = make_plan(common_db)
        report(plan, common_db)
        if not args.apply:
            print(f"\nPreview only: {len(plan.changes)} value(s) would change. Run again with --apply to change them.")
            return
        done, backup = apply(common_db, plan)
        print(f"\nChanged {done} value(s). Undo file: {backup}")


if __name__ == "__main__":
    main()
