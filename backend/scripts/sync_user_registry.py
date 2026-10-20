"""Fills / refreshes the central user registry (`user_registry`, Common DB) from every company's
trainees and trainers - services/user_registry_service.reconcile_tenant, run once per company.

DRY RUN by default: reads everything and prints what it would add, update, disable or remove, plus
every ID / username / HO ID it can't copy because another account holds it - nothing is written.
--apply writes it. Company databases are opened without the app's pool or schema sync
(scripts/_tenant_db.py); only the Common DB's `user_registry` is ever written.

    cd backend
    venv/Scripts/python.exe scripts/sync_user_registry.py                  # dry run, every company
    venv/Scripts/python.exe scripts/sync_user_registry.py --tenant demo    # dry run, one company
    venv/Scripts/python.exe scripts/sync_user_registry.py --apply
"""

import argparse
import sys

from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, ".")
from scripts._tenant_db import tenant_engine  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill / refresh the central user registry (dry run unless --apply).")
    parser.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    parser.add_argument("--tenant", help="only this company (its tenant ID)")
    args = parser.parse_args()

    from app.database.common import CommonSessionLocal, common_engine
    from app.repositories import tenant_repository
    from app.services.user_registry_service import reconcile_tenant

    if not inspect(common_engine).has_table("user_registry"):
        sys.exit("The Common DB has no user_registry table yet - deploy the app first (it creates the table on start).")

    common_db = CommonSessionLocal()
    try:
        tenants = [args.tenant] if args.tenant else tenant_repository.list_active_uids(common_db)
        for tenant_uid in tenants:
            engine = tenant_engine(tenant_uid)
            tenant_db = sessionmaker(bind=engine)()
            try:
                report = reconcile_tenant(common_db, tenant_db, tenant_uid, apply=args.apply)
            finally:
                tenant_db.close()
                engine.dispose()
            print(f"{tenant_uid}: add {report.added}, update {report.updated}, unchanged {report.unchanged}, "
                  f"disable {report.disabled}, remove {report.removed}, skipped {len(report.skipped)}")
            for user_uid, reason in report.skipped:
                print(f"    skipped {user_uid}: {reason}")
    finally:
        common_db.close()
    print("applied." if args.apply else "dry run - nothing was written. Run again with --apply to write it.")


if __name__ == "__main__":
    main()
