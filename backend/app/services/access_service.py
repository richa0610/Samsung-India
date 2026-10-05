"""Who may see what: the single place that turns "this account, in this tenant" into an
`AccessScope`.

Rules (see the approved Phase C plan):
  - Deny by default. No applicable grant = no access. There is no "no company means
    unrestricted" fallback; only an explicitly granted Super Admin sees everything.
  - Tenant membership is explicit for admin-table accounts (`admin_access` rows). Agency-team
    trainers live inside their tenant's own database and are members of it implicitly.
  - Roles come from trusted server-side rows, never from a token claim or a client header.
  - The tenant passed in must already be the verified one (the signed token's claim); this
    module never reads a request.

WIRING STATUS: two approved uses so far, both scoped to one conference at a time or one query at
a time - never a blanket switch.
  - `training_service._get_owned_conference` (and `live_quiz_service._owned_live_conference`)
    call `resolve_scope` so an admin-table account can start/operate a conference - and its
    modules, attendance, live quiz, edits, approvals, detail, report, dashboard, performers -
    inside their granted scope, the same as the assigned trainer (the approved "admin can start
    training like trainers" change, later widened to the read/edit endpoints around the same
    conference in the Training List RBAC task's Phase 2).
  - `dashboard_repository.access_scope_conditions` turns an `AccessScope` into SQL conditions, so
    the admin Training List (`training_service.list_trainings_page`) and the admin Attendance
    List (`list_attendance_page`, and the non-paged `list_attendance(org=True)` via
    `AccessScope.allows_row` in Python) are scoped at the query level - count, search, sort,
    paging, export all included (the Training List RBAC task's Phases 1 and 4).
  - Trainer authorization (Trainer Flow Phase 1): an active trainer is `AccessScope.is_trainer`
    (agency-team role "trainer", or an admin-table trainer grant). conference_access turns the
    scope into SQL via dashboard_repository.conference_authorization_conditions for every
    conference-level endpoint, the Live Quiz controls and the live WebSocket room;
    `own_trainings_username` gates the trainer's own Home / Training / Attendance lists; and
    dashboard_repository.trainee_authorization_conditions gates the Trainee List.
`GET /admin/access/scope` (`scope_summary`) additionally exposes the caller's own scope to the
frontend, for hiding filter options it isn't authorized for - display only, grants nothing.
Everything else is untouched: trainee lists, dashboard stats, login/tenant-membership, etc.
still use the legacy `data_scope_service.apply_identity_scope` or no scope check at all, and
enforcement for those resources needs its own approval (see the audit in that task's write-up
for what was found there).
tests/test_access_model.py pins that the module IS imported by the running app; it does not pin
that the table can be created by app startup (a separate, unaffected guarantee - see
test_app_startup_cannot_create_the_table).
"""

import enum
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import forbidden
from app.models.admin import Admin
from app.models.admin_access import AdminAccess
from app.models.agency_team import AgencyTeam


class AccessRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    COMPANY_ADMIN = "company_admin"
    COORDINATOR = "coordinator"
    SUB_COORDINATOR = "sub_coordinator"
    TRAINER = "trainer"


_RANK = {
    AccessRole.SUPER_ADMIN: 5,
    AccessRole.COMPANY_ADMIN: 4,
    AccessRole.COORDINATOR: 3,
    AccessRole.SUB_COORDINATOR: 2,
    AccessRole.TRAINER: 1,
}
_ADMIN_PANEL_ROLES = {AccessRole.SUPER_ADMIN, AccessRole.COMPANY_ADMIN, AccessRole.COORDINATOR, AccessRole.SUB_COORDINATOR}


def norm(value: Optional[str]) -> str:
    """Company / zone / region are compared trimmed and lower-cased, exactly like the existing
    admin filters (ConferenceFilters), so both agree on what "the same" means."""
    return (value or "").strip().lower()


def company_admin_key(tenant_uid: str, company: str) -> str:
    """The value stored in `admin_access.company_admin_key` for an active company_admin grant.
    Two spellings of one company ("Samsung India", " samsung india ") give the same key, so the
    database's UNIQUE constraint allows exactly one Company Admin per company in a tenant."""
    return f"{(tenant_uid or '').strip()}|{norm(company)}"


@dataclass(frozen=True)
class ScopeRule:
    """One slice of data: a company, optionally narrowed to a zone and/or a region.
    `None` means "any". A row with a blank zone never matches a rule that names a zone."""

    company: str
    zone: Optional[str] = None
    region: Optional[str] = None

    def matches(self, company: Optional[str], zone: Optional[str], region: Optional[str]) -> bool:
        return (
            norm(company) == self.company
            and (self.zone is None or norm(zone) == self.zone)
            and (self.region is None or norm(region) == self.region)
        )


@dataclass(frozen=True)
class AccessScope:
    allowed: bool
    tenant_uid: str
    role: Optional[AccessRole] = None  # the most privileged grant held
    is_super: bool = False
    rules: tuple[ScopeRule, ...] = ()  # union of the company / zone / region slices granted
    trainer_username: Optional[str] = None  # set for trainers: their own trainings / assigned trainees
    reason: str = ""  # why access was denied (for logs only, never shown to clients)

    @classmethod
    def denied(cls, tenant_uid: str, reason: str) -> "AccessScope":
        return cls(allowed=False, tenant_uid=tenant_uid, reason=reason)

    @property
    def is_admin_panel(self) -> bool:
        return self.allowed and self.role in _ADMIN_PANEL_ROLES

    @property
    def is_trainer(self) -> bool:
        """An active trainer with a resolved username - the only scope that owns trainings by
        assignment. A blank username never counts, so it can't match unassigned rows."""
        return self.allowed and self.role == AccessRole.TRAINER and bool((self.trainer_username or "").strip())

    def allows_row(self, company: Optional[str], zone: Optional[str], region: Optional[str]) -> bool:
        """Whether a training / trainee / attendance row with this company, zone and region is
        inside the scope. Trainers are not company-scoped (their access is by assignment), so
        they never match here."""
        if not self.allowed:
            return False
        if self.is_super:
            return True
        return any(rule.matches(company, zone, region) for rule in self.rules)


def resolve_scope(common_db: Session, principal: object, tenant_id: Optional[str]) -> AccessScope:
    """The access `principal` has in `tenant_id`.

    `principal` is what authentication already resolved: an `Admin` (shared database) or an
    `AgencyTeam` trainer (tenant database). `tenant_id` must be the verified tenant."""
    tenant = (tenant_id or "").strip()
    if not tenant:
        return AccessScope.denied("", "no tenant")

    if isinstance(principal, AgencyTeam):
        if norm(principal.role) != "trainer":
            return AccessScope.denied(tenant, "agency-team account is not a trainer")
        return AccessScope(True, tenant, AccessRole.TRAINER, trainer_username=principal.username)

    if isinstance(principal, Admin):
        if common_db is None:
            return AccessScope.denied(tenant, "no common database to read grants from")
        return _resolve_admin(common_db, principal, tenant)

    return AccessScope.denied(tenant, "unknown principal")


def granted_companies(scope: AccessScope) -> Optional[frozenset[str]]:
    """The companies (normalized) an admin-panel grant covers: None = every company (a Super
    Admin), otherwise the companies its rules name - empty for no admin-panel access. Zone/region
    can't narrow it: no trainer record carries a zone of its own. The one rule for "which
    companies' trainers may this admin see or assign" (trainer dropdowns, assignment, the
    dashboard's trainer pool)."""
    if not scope.is_admin_panel:
        return frozenset()
    if scope.is_super:
        return None
    return frozenset(rule.company for rule in scope.rules)


def reject_outside_scope(scope: AccessScope, company: Optional[str], zone: Optional[str], region: Optional[str]) -> None:
    """For an admin-panel account creating or moving a record (a training, a trainee): the
    company/zone/region it will carry must be inside the caller's grant - the same `allows_row`
    test that decides what the caller can read, so nobody can place a record where they couldn't
    see it (or into someone else's scope). A Super Admin passes; no grant never does."""
    if not scope.allows_row(company, zone, region):
        raise forbidden("This company, zone or region is outside your authorized scope")


def own_trainings_username(common_db: Optional[Session], principal: object, tenant_id: Optional[str]) -> str:
    """The verified username whose OWN trainings the caller's personal views list (trainer Home,
    Training List, Attendance List). A trainer gets their own username only once `resolve_scope`
    confirms they are an active trainer in this tenant (agency-team role "trainer", or an
    admin-table trainer grant). An admin-panel account keeps its existing "trainings assigned to
    my username" view. Anything else - no grant, wrong role, missing tenant - is refused."""
    scope = resolve_scope(common_db, principal, tenant_id)
    if scope.is_trainer:
        return scope.trainer_username
    if scope.is_admin_panel:
        return principal.username
    raise forbidden("This action requires an active trainer account")


def _resolve_admin(common_db: Session, admin: Admin, tenant: str) -> AccessScope:
    rows = (
        common_db.query(AdminAccess)
        .filter(
            AdminAccess.admin_id == admin.id,
            AdminAccess.active == 1,
            or_(AdminAccess.tenant_uid == tenant, AdminAccess.tenant_uid.is_(None)),
        )
        .all()
    )
    account_role = norm(admin.role)  # "admin" (admin panel) or "trainer"

    roles: list[AccessRole] = []
    rules: list[ScopeRule] = []
    is_super = False
    for row in rows:
        try:
            role = AccessRole(row.role)
        except ValueError:
            continue  # unknown role text: ignore the grant
        # Defence in depth against a mistaken grant: an admin-panel grant only counts on an
        # account whose role is "admin", and a trainer grant only on a "trainer" account.
        if (role in _ADMIN_PANEL_ROLES) != (account_role == "admin"):
            continue
        if role == AccessRole.SUPER_ADMIN:
            if row.tenant_uid is not None:
                continue  # a super admin grant is global by definition; a tenant-tagged one is malformed
            is_super = True
        elif row.tenant_uid != tenant:
            continue  # a tenant-less row is only valid for a super admin
        elif role == AccessRole.COMPANY_ADMIN and norm(row.company):
            rules.append(ScopeRule(norm(row.company)))
        elif role == AccessRole.COORDINATOR and norm(row.company) and norm(row.zone):
            rules.append(ScopeRule(norm(row.company), zone=norm(row.zone)))
        elif role == AccessRole.SUB_COORDINATOR and norm(row.company) and norm(row.region):
            rules.append(ScopeRule(norm(row.company), region=norm(row.region)))
        elif role != AccessRole.TRAINER:
            continue  # required fields missing: ignore the grant
        roles.append(role)

    if not roles:
        return AccessScope.denied(tenant, "no grant for this tenant")
    top = max(roles, key=lambda r: _RANK[r])
    return AccessScope(
        True,
        tenant,
        top,
        is_super=is_super,
        rules=tuple(dict.fromkeys(rules)),  # de-duplicated, order kept
        trainer_username=admin.username if top == AccessRole.TRAINER else None,
    )


def scope_summary(scope: AccessScope) -> dict:
    """The caller's own scope, shaped for the frontend to narrow its filter OPTIONS against
    (AdminFilterBar) - a usability convenience only, never an authorization decision; the
    backend still enforces the real boundary on every request via `resolve_scope` /
    `access_scope_conditions` regardless of what this returns.

    `None` for zones/regions means "not restricted on that axis" (a Company Admin sees every
    zone and region in their company; a Coordinator's zone rule carries no region, so they see
    every region within it). A list means "only these". Values are already the lower-cased,
    trimmed form `ConferenceFilters` sends on the wire, so a caller can compare them directly
    against a query param without re-normalizing."""
    if not scope.allowed:
        return {"allowed": False, "isSuper": False, "role": None, "zones": [], "regions": []}
    role = scope.role.value if scope.role else None
    if scope.is_super:
        return {"allowed": True, "isSuper": True, "role": role, "zones": None, "regions": None}
    zones = None if any(rule.zone is None for rule in scope.rules) else sorted({rule.zone for rule in scope.rules if rule.zone})
    regions = (
        None if any(rule.region is None for rule in scope.rules) else sorted({rule.region for rule in scope.rules if rule.region})
    )
    return {"allowed": True, "isSuper": False, "role": role, "zones": zones, "regions": regions}
