"""Phase C step 2: DRY-RUN planning of the first `admin_access` grants.

This module only READS. It turns the reviewed assignment file (which account gets which role)
plus what the databases already say (zone assignments in `data_scopes`, company on each account)
into a list of planned grants, checks the plan for lock-outs and mistakes, and shows who would
see what before and after. It never writes: there is no write code in it, and the CLI
(scripts/seed_admin_access.py) opens both databases read-only and refuses any statement that
is not a read (`make_read_only`). Applying the plan is a later, separately approved step.

NOT WIRED INTO THE APP. Nothing in the running backend imports this module.
"""

import json
import re
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Optional

from sqlalchemy import create_engine, event, func, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
from app.models.admin_access import AccessBase, AdminAccess
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.data_scope import DataScope
from app.models.logs_master import LogsMaster
from app.services.access_service import AccessRole, company_admin_key, norm, resolve_scope
from app.services.data_scope_service import apply_identity_scope
from app.utils.zones import zone_key

VALID_ROLES = {r.value for r in AccessRole}


# ----------------------------------------------------------------------------- read-only guard
# Only plain reads, plus the two statements that TURN ON read-only mode and SQLAlchemy's schema
# look-ups. Anything that could turn read-only mode off (PRAGMA query_only = OFF, READ WRITE),
# a second statement after a ';', or a SELECT that writes a file does not match and is refused.
_READ_ONLY_STATEMENT = re.compile(
    r"^\s*(select|show|explain|describe|desc)\b"
    r"|^\s*set\s+session\s+transaction\s+read\s+only\s*$"
    r"|^\s*pragma\s+query_only\s*=\s*on\s*$"
    r"|^\s*pragma\s+((main|temp)\.)?(table_info|table_xinfo|table_list|index_list|index_info|index_xinfo|foreign_key_list)\b",
    re.I,
)
_SECOND_STATEMENT = re.compile(r";\s*\S")
_WRITES_A_FILE = re.compile(r"\binto\s+(outfile|dumpfile)\b", re.I)


def is_read_statement(statement: str) -> bool:
    return bool(_READ_ONLY_STATEMENT.match(statement)) and not _SECOND_STATEMENT.search(statement) and not _WRITES_A_FILE.search(statement)


def make_read_only(engine: Engine) -> Engine:
    """Belt and braces for the CLI: (1) MySQL opens every connection with
    `SET SESSION TRANSACTION READ ONLY` (SQLite: `PRAGMA query_only`), so the SERVER itself
    rejects a write; (2) any statement that is not a plain read raises before it is sent."""

    @event.listens_for(engine, "connect")
    def _read_only_session(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        try:
            if engine.dialect.name == "sqlite":
                cursor.execute("PRAGMA query_only = ON")
            else:
                cursor.execute("SET SESSION TRANSACTION READ ONLY")
        finally:
            cursor.close()

    @event.listens_for(engine, "before_cursor_execute")
    def _only_reads(_conn, _cursor, statement, _parameters, _context, _executemany):
        if not is_read_statement(statement):
            raise RuntimeError(f"dry run: refusing a non-read statement: {statement[:60]!r}")

    return engine


# ----------------------------------------------------------------------------- data shapes
@dataclass(frozen=True)
class Assignment:
    admin_id: int
    role: str
    company: Optional[str] = None  # only needed for company_admin (coordinators use the account's own company)


@dataclass
class PlannedGrant:
    admin_id: int
    role: str
    tenant_uid: Optional[str]
    company: Optional[str] = None
    zone: Optional[str] = None
    region: Optional[str] = None
    status: str = "planned"  # "planned" or "held" (not granted until something is confirmed)
    note: str = ""

    @property
    def key(self) -> Optional[str]:
        return company_admin_key(self.tenant_uid or "", self.company or "") if self.role == "company_admin" and self.status == "planned" else None

    def sql(self) -> str:
        """The row a later, approved apply would write - shown for review only, never executed."""
        q = lambda v: "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"
        return (
            "INSERT INTO admin_access (admin_id, role, tenant_uid, company, zone, region, active, granted_by, company_admin_key) VALUES "
            f"({self.admin_id}, {q(self.role)}, {q(self.tenant_uid)}, {q(self.company)}, {q(self.zone)}, {q(self.region)}, 1, 'phase-c-seed', {q(self.key)});"
        )


@dataclass
class Finding:
    level: str  # OK | WARN | BLOCK
    text: str


@dataclass
class Plan:
    tenant_uid: str
    grants: list[PlannedGrant] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    accounts: list[dict] = field(default_factory=list)  # one row per existing account (masked)
    visibility: list[dict] = field(default_factory=list)  # before / after, per account
    super_admin_evidence: dict = field(default_factory=dict)

    def add(self, level: str, text: str):
        self.findings.append(Finding(level, text))

    @property
    def blockers(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "BLOCK"]


def load_assignments(path: str) -> tuple[str, list[Assignment]]:
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)
    return spec["tenant"], [Assignment(int(a["admin_id"]), a["role"], a.get("company")) for a in spec["assignments"]]


def mask(text: Optional[str]) -> str:
    text = text or ""
    return (text[:2] + "*" * max(len(text) - 2, 1)) if text else "-"


# ----------------------------------------------------------------------------- planning
def build_plan(
    common_db: Session,
    tenant_db: Session,
    tenant_uid: str,
    assignments: list[Assignment],
    confirmed_super_admins: frozenset[int] = frozenset(),
) -> Plan:
    plan = Plan(tenant_uid)
    admins = {a.id: a for a in common_db.query(Admin).order_by(Admin.id).all()}
    conf_zones = {zone_key(z) for (z,) in tenant_db.query(Conference.zone).distinct() if zone_key(z)}

    _check_tenant(plan, common_db)
    existing_keys, existing_by_admin = _existing_grants(plan, common_db)
    planner = _AssignmentPlanner(plan, tenant_db, admins, conf_zones, existing_keys, confirmed_super_admins)
    for assignment in assignments:
        planner.add(assignment)
    _check_every_account_decided(plan, admins, existing_by_admin)

    plan.accounts = [_account_row(a, [g for g in plan.grants if g.admin_id == a.id]) for a in admins.values()]
    _simulate(plan, tenant_db, admins)
    _warn_unscoped_trainings(plan, tenant_db)
    return plan


def _check_tenant(plan: Plan, common_db: Session) -> None:
    tenant_uid = plan.tenant_uid
    tenant = common_db.query(Tenant).filter(Tenant.tenant_uid == tenant_uid).first()
    if tenant is None:
        plan.add("WARN", f"tenant '{tenant_uid}' has no row in the tenant registry (it works only as the default tenant)")
    elif (tenant.status or "").lower() != "active":
        plan.add("BLOCK", f"tenant '{tenant_uid}' is {tenant.status!r}, not active")
    else:
        plan.add("OK", f"tenant '{tenant_uid}' is registered and active")


def _existing_grants(plan: Plan, common_db: Session) -> tuple[set[str], dict[int, int]]:
    """Grants that already exist (the table may not exist yet): the Company Admin keys taken, and
    how many active grants each account holds."""
    existing_keys: set[str] = set()
    existing_by_admin: dict[int, int] = {}
    if not inspect(common_db.get_bind()).has_table("admin_access"):
        plan.add("OK", "admin_access does not exist yet (created by the reviewed SQL, not by this tool) - planning from empty")
        return existing_keys, existing_by_admin
    for row in common_db.query(AdminAccess).filter(AdminAccess.active == 1).all():
        existing_by_admin[row.admin_id] = existing_by_admin.get(row.admin_id, 0) + 1
        if row.company_admin_key:
            existing_keys.add(row.company_admin_key)
    plan.add("OK", f"admin_access exists with {sum(existing_by_admin.values())} active grant(s)")
    return existing_keys, existing_by_admin


@dataclass
class _AssignmentPlanner:
    """One pass over the assignments: each one is checked, then becomes planned grant(s) - or a
    finding saying why not."""

    plan: Plan
    tenant_db: Session
    admins: dict[int, Admin]
    conf_zones: set[str]
    existing_keys: set[str]
    confirmed_super_admins: frozenset[int]
    seen_pairs: set[tuple[int, str]] = field(default_factory=set)
    company_admin_keys: dict[str, int] = field(default_factory=dict)

    def add(self, a: Assignment) -> None:
        admin = self._account_for(a)
        if admin is None:
            return
        if a.role == "trainer":
            self._trainer(a, admin)
        elif norm(admin.role) != "admin":
            self.plan.add("BLOCK", f"account {a.admin_id}: assigned {a.role!r} but the account role is {admin.role!r} (admin-panel roles need an 'admin' account)")
        elif a.role == "super_admin":
            self._super_admin(a, admin)
        elif a.role == "company_admin":
            self._company_admin(a, admin)
        elif a.role == "coordinator":
            self._coordinator(a, admin)
        elif a.role == "sub_coordinator":
            self.plan.add("BLOCK", f"account {a.admin_id}: Sub-coordinator needs a region and none is defined in the plan")

    def _account_for(self, a: Assignment) -> Optional[Admin]:
        """The assignment's account, or None once it is blocked: an unknown role, an account that
        does not exist, or the same role assigned to it twice."""
        admin = self.admins.get(a.admin_id)
        if a.role not in VALID_ROLES:
            self.plan.add("BLOCK", f"account {a.admin_id}: unknown role {a.role!r}")
            return None
        if admin is None:
            self.plan.add("BLOCK", f"account {a.admin_id}: not found in the shared database")
            return None
        if (a.admin_id, a.role) in self.seen_pairs:
            self.plan.add("BLOCK", f"account {a.admin_id}: assigned {a.role!r} more than once")
            return None
        self.seen_pairs.add((a.admin_id, a.role))
        return admin

    def _trainer(self, a: Assignment, admin: Admin) -> None:
        if norm(admin.role) != "trainer":
            self.plan.add("BLOCK", f"account {a.admin_id}: assigned 'trainer' but the account role is {admin.role!r}")
            return
        self.plan.grants.append(PlannedGrant(a.admin_id, "trainer", self.plan.tenant_uid, note="tenant membership only; existing trainer permissions unchanged"))

    def _super_admin(self, a: Assignment, admin: Admin) -> None:
        evidence = super_admin_evidence(self.tenant_db, admin)
        self.plan.super_admin_evidence[a.admin_id] = evidence
        if a.admin_id in self.confirmed_super_admins:
            self.plan.grants.append(PlannedGrant(a.admin_id, "super_admin", None, note="global; explicitly confirmed"))
        else:
            self.plan.grants.append(PlannedGrant(a.admin_id, "super_admin", None, status="held",
                                                 note="HELD - authorization not confirmed; denied until confirmed"))
            self.plan.add("WARN", f"account {a.admin_id}: Super Admin is HELD (not granted) until its authorization is confirmed")
        if evidence["has_company"]:
            self.plan.add("WARN", f"account {a.admin_id}: has a company set, which is unusual for the global account")

    def _company_admin(self, a: Assignment, admin: Admin) -> None:
        tenant_uid = self.plan.tenant_uid
        company = (a.company or admin.company or "").strip()
        if not company:
            self.plan.add("BLOCK", f"account {a.admin_id}: Company Admin needs a company")
            return
        if admin.company and norm(admin.company) != norm(company):
            self.plan.add("WARN", f"account {a.admin_id}: plan company {company!r} differs from the account's own company {admin.company!r}")
        key = company_admin_key(tenant_uid, company)
        if key in self.existing_keys:
            self.plan.add("BLOCK", f"a Company Admin for {company!r} in '{tenant_uid}' already exists in admin_access")
            return
        if key in self.company_admin_keys:
            self.plan.add("BLOCK", f"two accounts ({self.company_admin_keys[key]} and {a.admin_id}) are assigned Company Admin of {company!r}")
            return
        self.company_admin_keys[key] = a.admin_id
        self.plan.grants.append(PlannedGrant(a.admin_id, "company_admin", tenant_uid, company, note="the one Company Admin for this company"))

    def _coordinator(self, a: Assignment, admin: Admin) -> None:
        company = (admin.company or "").strip()
        zones = self._data_scope_zones(a.admin_id)
        if not company:
            self.plan.add("BLOCK", f"account {a.admin_id}: Coordinator needs the account to have a company")
            return
        if not zones:
            self.plan.add("BLOCK", f"account {a.admin_id}: Coordinator has no zone in data_scopes, so it could see nothing")
            return
        for zone in dict.fromkeys(zones):
            if zone_key(zone) not in self.conf_zones:
                self.plan.add("WARN", f"account {a.admin_id}: zone {zone!r} matches no training's zone (would see nothing)")
            self.plan.grants.append(PlannedGrant(a.admin_id, "coordinator", self.plan.tenant_uid, company, zone=zone, note="zone carried over from data_scopes"))

    def _data_scope_zones(self, admin_id: int) -> list[str]:
        """The zones data_scopes gives this account, blanks dropped."""
        rows = self.tenant_db.query(DataScope).filter(
            DataScope.table_type == "admin", DataScope.user_id == admin_id, DataScope.scope_type == "zone")
        return [row.scope_value.strip() for row in rows if row.scope_value and row.scope_value.strip()]


def _check_every_account_decided(plan: Plan, admins: dict[int, Admin], existing_by_admin: dict[int, int]) -> None:
    """Every existing account must end up with a decision: a planned grant, a grant it already
    has, or a warning (held until confirmed, or about to be denied)."""
    granted = {g.admin_id for g in plan.grants if g.status == "planned"}
    held = {g.admin_id for g in plan.grants if g.status == "held"}
    for admin_id, admin in admins.items():
        if admin_id in granted:
            continue
        if admin_id in held:
            plan.add("WARN", f"account {admin_id}: no access until its held grant is confirmed")
        elif existing_by_admin.get(admin_id):
            continue
        else:
            plan.add("WARN", f"account {admin_id} ({admin.role}) has NO planned grant: it will be DENIED once enforcement is on")


def _warn_unscoped_trainings(plan: Plan, tenant_db: Session) -> None:
    zone_gaps = tenant_db.query(func.count()).select_from(Conference).filter(func.trim(func.coalesce(Conference.zone, "")) == "").scalar() or 0
    region_gaps = tenant_db.query(func.count()).select_from(Conference).filter(func.trim(func.coalesce(Conference.region, "")) == "").scalar() or 0
    if zone_gaps or region_gaps:
        plan.add("WARN", f"{zone_gaps} training(s) have no zone and {region_gaps} no region: only the Super Admin and the Company Admin can see them")


def super_admin_evidence(tenant_db: Session, admin: Admin) -> dict:
    """What the data can say about whether this really is the global account. It cannot prove
    authorization - that is a human confirmation - so this only gathers supporting facts."""
    logins = tenant_db.query(func.count(), func.max(LogsMaster.timestamp)).filter(
        LogsMaster.username == admin.username, LogsMaster.action == "LOGIN").one()
    return {
        "account_role": admin.role,
        "status": admin.status,
        "has_company": bool((admin.company or "").strip()),
        "has_password": bool(admin.password),
        "recorded_logins": int(logins[0] or 0),
        "last_login": logins[1].isoformat(timespec="minutes") if logins[1] else None,
    }


def _account_row(admin: Admin, grants: list[PlannedGrant]) -> dict:
    return {
        "id": admin.id, "username": mask(admin.username), "role": admin.role, "company": admin.company or "-", "status": admin.status,
        "grants": [f"{g.role}{'/' + g.zone if g.zone else ''}{'/' + g.region if g.region else ''}{' (HELD)' if g.status == 'held' else ''}" for g in grants],
    }


def _simulate(plan: Plan, tenant_db: Session, admins: dict[int, Admin]) -> None:
    """Who would see what BEFORE (today's rules) and AFTER (the planned grants). The planned
    grants go into a throw-away in-memory database; nothing is written anywhere real."""
    sim = _planned_grants_db(plan)
    confs = [SimpleNamespace(conferenceDate=c[0], trainerEmployeeId=c[1], zone=c[2], region=c[3], sessionType=c[4], trainingType=c[5], company=c[6])
             for c in tenant_db.query(Conference.conferenceDate, Conference.trainerEmployeeId, Conference.zone, Conference.region,
                                      Conference.sessionType, Conference.trainingType, Conference.company)]
    for admin in admins.values():
        scope = resolve_scope(sim, admin, plan.tenant_uid)
        if norm(admin.role) == "trainer":
            plan.visibility.append(_trainer_visibility(admin, scope, confs))
        else:
            plan.visibility.append(_admin_visibility(admin, scope, confs, tenant_db))


def _planned_grants_db(plan: Plan) -> Session:
    sim_engine = create_engine("sqlite://")
    AccessBase.metadata.create_all(sim_engine)
    sim = sessionmaker(bind=sim_engine)()
    for g in plan.grants:
        if g.status == "planned":
            sim.add(AdminAccess(admin_id=g.admin_id, role=g.role, tenant_uid=g.tenant_uid, company=g.company, zone=g.zone, region=g.region,
                                company_admin_key=g.key))
    sim.commit()
    return sim


def _trainer_visibility(admin: Admin, scope, confs: list) -> dict:
    """A trainer keeps seeing their own trainings - unless the plan denies the account."""
    own = sum(1 for c in confs if c.trainerEmployeeId == admin.username)
    after, verdict = (f"{own} own trainings", "unchanged") if scope.allowed else ("DENIED", "LOSES ACCESS")
    return {"id": admin.id, "role": admin.role, "before": f"{own} own trainings", "after": after, "verdict": verdict}


def _admin_visibility(admin: Admin, scope, confs: list, tenant_db: Session) -> dict:
    """Trainings an admin-panel account sees today (its data_scopes) and under the planned grant."""
    today = apply_identity_scope(tenant_db, admin, ConferenceFilters())
    before = sum(1 for c in confs if today.matches(c))
    after = sum(1 for c in confs if scope.allows_row(c.company, c.zone, c.region)) if scope.allowed else 0
    return {
        "id": admin.id,
        "role": scope.role.value if scope.allowed and scope.role else norm(admin.role),
        "before": f"{before} of {len(confs)}",
        "after": f"{after} of {len(confs)}" if scope.allowed else "DENIED",
        "verdict": _visibility_change(scope.allowed, before, after),
    }


def _visibility_change(allowed: bool, before: int, after: int) -> str:
    if not allowed:
        return "LOSES ACCESS" if before else "still no access"
    if after == before:
        return "unchanged"
    return f"{'widens' if after > before else 'narrows'} by {abs(after - before)}"


# ----------------------------------------------------------------------------- report
def _super_admin_lines(plan: Plan) -> list[str]:
    if not plan.super_admin_evidence:
        return ["   (no Super Admin in the plan)"]
    lines: list[str] = []
    for admin_id, e in plan.super_admin_evidence.items():
        held = any(g.admin_id == admin_id and g.status == "held" for g in plan.grants)
        lines.append(f"   account {admin_id}: role={e['account_role']!r} status={e['status']!r} company set={e['has_company']} password set={e['has_password']}")
        lines.append(f"      recorded logins in this tenant: {e['recorded_logins']} (latest: {e['last_login'] or 'none'})")
        lines.append(f"      => {'HELD: NOT granted; the account is denied until you confirm it is the authorized global account' if held else 'GRANTED (confirmed)'}")
    return lines


def render_report(plan: Plan) -> str:
    out: list[str] = []
    line = "=" * 100
    out += [line, f"DRY RUN - Phase C step 2: planned admin_access grants for tenant '{plan.tenant_uid}'",
            "Reads only. Both databases are opened read-only; NOTHING is written and NO SQL is run.", line, ""]

    out.append("1. ACCOUNTS AND PLANNED GRANTS (usernames masked)")
    out.append(f"   {'id':>3}  {'username':12} {'account role':12} {'company':15} {'status':9} planned grant(s)")
    for a in plan.accounts:
        out.append(f"   {a['id']:>3}  {a['username'][:12]:12} {a['role']:12} {a['company'][:15]:15} {str(a['status'])[:9]:9} {', '.join(a['grants']) or '-- none --'}")
    out.append("")

    out.append("2. SUPER ADMIN VERIFICATION (what the data can show; authorization itself needs your confirmation)")
    out += _super_admin_lines(plan)
    out.append("")

    out.append("3. PLANNED ROWS (for review only - not executed)")
    for g in plan.grants:
        out.append(f"   [{g.status.upper():7}] {g.sql()}")
        if g.note:
            out.append(f"             {g.note}")
    out.append("")

    out.append("4. WHO SEES WHAT: today  ->  after the plan   (trainings visible)")
    out.append(f"   {'id':>3}  {'new role':16} {'today':22} {'after':22} change")
    for v in plan.visibility:
        out.append(f"   {v['id']:>3}  {v['role']:16} {v['before']:22} {v['after']:22} {v['verdict']}")
    out.append("")

    out.append("5. CHECKS")
    for f in plan.findings:
        out.append(f"   [{f.level:5}] {f.text}")
    blockers = plan.blockers
    out += ["", line, f"RESULT: {'NOT READY - ' + str(len(blockers)) + ' blocking problem(s)' if blockers else 'no blocking problems'}; "
            f"{sum(1 for g in plan.grants if g.status == 'planned')} grant(s) planned, {sum(1 for g in plan.grants if g.status == 'held')} held. Nothing was written.", line]
    return "\n".join(out)
