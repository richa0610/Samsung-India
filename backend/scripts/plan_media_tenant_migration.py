"""DRY RUN ONLY - plans moving uploads made before the per-tenant media folders (Phase 2.1) into
those folders. Reads the databases and lists the media folder; never moves, copies, renames or
deletes a file. The planning itself lives in app/services/media_migration.py (the same logic
production serves at GET /admin/maintenance/media-plan, for a host without a shell).

    cd backend
    venv/Scripts/python.exe scripts/plan_media_tenant_migration.py --report media_plan.json
    venv/Scripts/python.exe scripts/plan_media_tenant_migration.py --media-root D:/copy/of/media
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from app.core.media import MEDIA_ROOT  # noqa: E402
from app.services.media_migration import build_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry run: plan moving pre-split uploads into tenant folders.")
    parser.add_argument("--media-root", type=Path, default=MEDIA_ROOT, help="media folder to inspect (read only)")
    parser.add_argument("--report", type=Path, help="write the full plan as JSON here")
    args = parser.parse_args()

    from app.database.common import CommonSessionLocal
    from app.database.tenant import tenant_manager

    common_db = CommonSessionLocal()
    try:
        report = build_report(common_db, lambda uid: tenant_manager.get_session(uid, common_db), args.media_root)
    finally:
        common_db.close()

    for action, count in report["summary"].items():
        print(f"{action:18} {count}")
    for tenant_uid in report["unreadableTenants"]:
        print(f"! tenant {tenant_uid}: not readable - its files show as orphans")
    if args.report:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"full plan written to {args.report}")
    print("dry run only - nothing was moved.")


if __name__ == "__main__":
    main()
