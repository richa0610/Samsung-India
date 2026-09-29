"""DRY RUN ONLY - plans moving uploads made before the per-tenant media folders (Phase 2.1) into
those folders. It reads the databases and lists the media folder; it never moves, copies,
renames or deletes a file, and has no code that could.

    cd backend
    venv/Scripts/python.exe scripts/plan_media_tenant_migration.py --report media_plan.json
    venv/Scripts/python.exe scripts/plan_media_tenant_migration.py --media-root D:/copy/of/media

Ownership comes only from the database: a legacy file MEDIA_ROOT/<folder>/... belongs to the
tenant whose records reference that exact path. Every file gets one action:

    MOVE               exactly one tenant references it and its tenant folder has no file there
    SHARED             a default avatar - stays where it is, served to every tenant
    SKIP_ORPHAN        no record references it - already unreachable since Phase 2.1; review by hand
    FLAG_AMBIGUOUS     two or more tenants reference the same path - a pre-split name collision
                       (e.g. two tenants' agency_3.pdf); the file holds at most one of their
                       uploads and which one can't be told from the data
    FLAG_ACCOUNT_FILE  an admin-table account's photo/Aadhaar (the Common DB account is shared by
                       every tenant it is granted) - which tenant folder(s) should hold it needs a
                       decision; the report lists the account's granted tenants
    FLAG_CONFLICT      the tenant folder already has a file at that path

The report holds paths, actions and tenant ids only - no credentials, no personal data.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

sys.path.insert(0, ".")
from app.core.config import settings  # noqa: E402
from app.core.media import MEDIA_ROOT  # noqa: E402
from app.models.admin import Admin  # noqa: E402
from app.models.admin_access import AdminAccess  # noqa: E402
from app.models.agency_team import AgencyTeam  # noqa: E402
from app.models.attendance import Attendance  # noqa: E402
from app.models.conference import Conference  # noqa: E402
from app.models.trainee import Trainee  # noqa: E402
from app.services.media_access import KNOWN_FOLDERS, SHARED_FILES  # noqa: E402

# Every tenant-database column that stores an upload path (see the upload code in services/).
TENANT_REFERENCE_COLUMNS = (
    Conference.startConferenceImage,
    Conference.conferenceImage,
    Conference.attendanceSheet,
    Attendance.checkInPhoto,
    Trainee.profilePhoto,
    AgencyTeam.profilePhoto,
    AgencyTeam.aadharImage,
)
ALL_TENANTS = "*"  # a Super Admin grant


@dataclass
class PlanEntry:
    path: str
    action: str
    tenants: list[str] = field(default_factory=list)
    reason: str = ""


def collect_tenant_references(db: Session) -> set[str]:
    """Every upload path a tenant database refers to."""
    paths: set[str] = set()
    for column in TENANT_REFERENCE_COLUMNS:
        paths |= {value for (value,) in db.query(column).filter(column.isnot(None), column != "") if value}
    return paths


def collect_account_references(common_db: Session) -> dict[str, set[str]]:
    """Admin-table accounts' own files -> the tenants the account is actively granted."""
    grants: dict[int, set[str]] = defaultdict(set)
    for admin_id, tenant_uid in common_db.query(AdminAccess.admin_id, AdminAccess.tenant_uid).filter(AdminAccess.active == 1):
        grants[admin_id].add(tenant_uid or ALL_TENANTS)
    references: dict[str, set[str]] = defaultdict(set)
    for admin in common_db.query(Admin):
        for path in (admin.profilePhoto, admin.aadharImage):
            if path:
                references[path] |= grants.get(admin.id, set())
    return references


def legacy_files(media_root: Path) -> list[str]:
    """Relative paths of files still in the pre-split layout (MEDIA_ROOT/<known folder>/...)."""
    files = []
    for folder in sorted(KNOWN_FOLDERS):
        base = media_root / folder
        if base.is_dir():
            files += sorted(p.relative_to(media_root).as_posix() for p in base.rglob("*") if p.is_file())
    return files


def plan(
    media_root: Path, references_by_tenant: dict[str, set[str]], account_references: dict[str, set[str]]
) -> list[PlanEntry]:
    entries = []
    for path in legacy_files(media_root):
        tenants = sorted(t for t, paths in references_by_tenant.items() if path in paths)
        if path in SHARED_FILES:
            entries.append(PlanEntry(path, "SHARED", reason="default avatar, served to every tenant"))
        elif path in account_references:
            entries.append(PlanEntry(path, "FLAG_ACCOUNT_FILE", sorted(account_references[path]),
                                     "belongs to a shared admin-table account"))
        elif not tenants:
            entries.append(PlanEntry(path, "SKIP_ORPHAN", reason="no record references this file"))
        elif len(tenants) > 1:
            entries.append(PlanEntry(path, "FLAG_AMBIGUOUS", tenants, "referenced by more than one tenant"))
        elif (media_root / tenants[0] / path).exists():
            entries.append(PlanEntry(path, "FLAG_CONFLICT", tenants, "the tenant folder already has this file"))
        else:
            entries.append(PlanEntry(path, "MOVE", tenants, f"-> {tenants[0]}/{path}"))
    return entries


def _tenant_uids(common_db: Session) -> list[str]:
    from app.models.common.tenant_registry import Tenant

    uids = {uid for (uid,) in common_db.query(Tenant.tenant_uid)}
    uids.add(settings.DEFAULT_TENANT_ID)
    return sorted(uids)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry run: plan moving pre-split uploads into tenant folders.")
    parser.add_argument("--media-root", type=Path, default=MEDIA_ROOT, help="media folder to inspect (read only)")
    parser.add_argument("--report", type=Path, help="write the full plan as JSON here")
    args = parser.parse_args()

    from app.database.common import CommonSessionLocal
    from app.database.tenant import tenant_manager

    common_db = CommonSessionLocal()
    try:
        references = {}
        for tenant_uid in _tenant_uids(common_db):
            try:
                tenant_db = tenant_manager.get_session(tenant_uid, common_db)
            except Exception as exc:  # an unreachable tenant is reported, never guessed at
                print(f"! tenant {tenant_uid}: not readable ({type(exc).__name__}) - its files will show as orphans")
                continue
            try:
                references[tenant_uid] = collect_tenant_references(tenant_db)
            finally:
                tenant_db.close()
        entries = plan(args.media_root, references, collect_account_references(common_db))
    finally:
        common_db.close()

    for action, count in sorted(Counter(e.action for e in entries).items()):
        print(f"{action:18} {count}")
    if args.report:
        args.report.write_text(json.dumps([asdict(e) for e in entries], indent=2), encoding="utf-8")
        print(f"full plan written to {args.report}")
    print("dry run only - nothing was moved.")


if __name__ == "__main__":
    main()
