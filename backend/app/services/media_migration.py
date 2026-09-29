"""READ-ONLY planning for moving uploads made before the per-tenant media folders (Phase 2.1) into
those folders. Used by scripts/plan_media_tenant_migration.py (local) and by
GET /admin/maintenance/media-plan (production, where the files live on the server's own disk).
Nothing here moves, copies, renames or deletes a file.

Ownership comes only from the database: a legacy file MEDIA_ROOT/<folder>/... belongs to the
tenant whose records reference that exact path. Every file gets one action:

    MOVE               exactly one tenant references it and its tenant folder has no file there
    SHARED             a default avatar - stays where it is, served to every tenant
    SKIP_ORPHAN        no record references it - already unreachable since Phase 2.1; review by hand
    FLAG_AMBIGUOUS     two or more tenants reference the same path - a pre-split name collision;
                       the file holds at most one of their uploads and which one can't be told
    FLAG_ACCOUNT_FILE  an admin-table account's photo/Aadhaar (a Common DB account shared by every
                       tenant it is granted); lists the account's granted tenants
    FLAG_CONFLICT      the tenant folder already has a file at that path

The plan holds paths, actions and tenant ids only - no credentials, no personal data."""

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.media import MEDIA_ROOT
from app.database.tenant import tenant_manager
from app.models.admin import Admin
from app.models.admin_access import AdminAccess
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.services.media_access import KNOWN_FOLDERS, SHARED_FILES

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


def tenant_uids(common_db: Session) -> list[str]:
    uids = {uid for (uid,) in common_db.query(Tenant.tenant_uid)}
    uids.add(settings.DEFAULT_TENANT_ID)
    return sorted(uids)


def build_report(common_db: Session, open_tenant_session, media_root: Path) -> dict:
    """The full plan for every tenant. `open_tenant_session(tenant_uid)` returns a session for
    that tenant's database; a tenant that can't be opened is listed in `unreadableTenants` (its
    files then show as orphans) - reported, never guessed at."""
    references: dict[str, set[str]] = {}
    unreadable: list[str] = []
    for tenant_uid in tenant_uids(common_db):
        try:
            tenant_db = open_tenant_session(tenant_uid)
        except Exception:
            unreadable.append(tenant_uid)
            continue
        try:
            references[tenant_uid] = collect_tenant_references(tenant_db)
        finally:
            tenant_db.close()
    entries = plan(media_root, references, collect_account_references(common_db))
    return {
        "dryRun": True,
        "summary": dict(sorted(Counter(e.action for e in entries).items())),
        "unreadableTenants": unreadable,
        "entries": [asdict(e) for e in entries],
    }


def current_report(common_db: Session) -> dict:
    """The plan for this server's own media folder and databases."""
    return build_report(common_db, lambda uid: tenant_manager.get_session(uid, common_db), MEDIA_ROOT)
