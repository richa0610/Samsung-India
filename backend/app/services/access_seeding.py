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
    conf_zones = {norm(z) for (z,) in tenant_db.query(Conference.zone).distinct() if norm(z)}

    # -- the tenant --------------------------------------------------------------
    tenant = common_db.query(Tenant).filter(Tenant.tenant_uid == tenant_uid).first()
    if tenant is None:
        plan.add("WARN", f"tenant '{tenant_uid}' has no row in the tenant registry (it works only as the default tenant)")
    elif (tenant.status or "").lower() != "active":
        plan.add("BLOCK", f"tenant '{tenant_uid}' is {tenant.status!r}, not active")
    else:
        plan.add("OK", f"tenant '{tenant_uid}' is registered and active")

    # -- grants that already exist (the table may not exist yet) ----------------------------
    existing_keys: set[str] = set()
    existing_by_admin: dict[int, int] = {}
    if inspect(common_db.get_bind()).has_table("admin_access"):
        for row in common_db.query(AdminAccess).filter(AdminAccess.active == 1).all():
            existing_by_admin[row.admin_id] = existing_by_admin.get(row.admin_id, 0) + 1
            if row.company_admin_key:
                existing_keys.add(row.company_admin_key)
        plan.add("OK", f"admin_access exists with {sum(existing_by_admin.values())} active grant(s)")
    else:
        plan.add("OK", "admin_access does not exist yet (created by the reviewed SQL, not by this tool) - planning from empty")

    # -- one pass over the assignments ---------------------------------------------------------
    seen_pairs: set[tuple[int, str]] = set()
    company_admin_keys: dict[str, int] = {}
    for a in assignments:
        admin = admins.get(a.admin_id)
        if a.role not in VALID_ROLES:
            plan.add("BLOCK", f"account {a.admin_id}: unknown role {a.role!r}")
            continue
        if admin is None:
            plan.add("BLOCK", f"account {a.admin_id}: not found in the shared database")
            continue
        if (a.admin_id, a.role) in seen_pairs:
            plan.add("BLOCK", f"account {a.admin_id}: assigned {a.role!r} more than once")
            continue
        seen_pairs.add((a.admin_id, a.role))
        account_role = norm(admin.role)

        if a.role == "trainer":
            if account_role != "trainer":
                plan.add("BLOCK", f"account {a.admin_id}: assigned 'trainer' but the account role is {admin.role!r}")
                continue
            plan.grants.append(PlannedGrant(a.admin_id, "trainer", tenant_uid, note="tenant membership only; existing trainer permissions unchanged"))
            continue

        if account_role != "admin":
            plan.add("BLOCK", f"account {a.admin_id}: assigned {a.role!r} but the account role is {admin.role!r} (admin-panel roles need an 'admin' account)")
            continue

        if a.role == "super_admin":
            evidence = super_admin_evidence(tenant_db, admin)
            plan.super_admin_evidence[a.admin_id] = evidence
            if a.admin_id in confirmed_super_admins:
                plan.grants.append(PlannedGrant(a.admin_id, "super_admin", None, note="global; explicitly confirmed"))
            else:
                plan.grants.append(PlannedGrant(a.admin_id, "super_admin", None, status="held",
                                                note="HELD - authorization not confirmed; denied until confirmed"))
                plan.add("WARN", f"account {a.admin_id}: Super Admin is HELD (not granted) until its authorization is confirmed")
            if evidence["has_company"]:
                plan.add("WARN", f"account {a.admin_id}: has a company set, which is unusual for the global account")

        elif a.role == "company_admin":
            company = (a.company or admin.company or "").strip()
            if not company:
                plan.add("BLOCK", f"account {a.admin_id}: Company Admin needs a company")
                continue
            if admin.company and norm(admin.company) != norm(company):
                plan.add("WARN", f"account {a.admin_id}: plan company {company!r} differs from the account's own company {admin.company!r}")
            key = company_admin_key(tenant_uid, company)
            if key in existing_keys:
                plan.add("BLOCK", f"a Company Admin for {company!r} in '{tenant_uid}' already exists in admin_access")
                continue
            if key in company_admin_keys:
                plan.add("BLOCK", f"two accounts ({company_admin_keys[key]} and {a.admin_id}) are assigned Company Admin of {company!r}")
                continue
            company_admin_keys[key] = a.admin_id
            plan.grants.append(PlannedGrant(a.admin_id, "company_admin", tenant_uid, company, note="the one Company Admin for this company"))

        elif a.role == "coordinator":
            company = (admin.company or "").strip()
            zones = [row.scope_value.strip() for row in tenant_db.query(DataScope).filter(
                DataScope.table_type == "admin", DataScope.user_id == a.admin_id, DataScope.scope_type == "zone") if row.scope_value and row.scope_value.strip()]
            if not company:
                plan.add("BLOCK", f"account {a.admin_id}: Coordinator needs the account to have a company")
                continue
            if not zones:
                plan.add("BLOCK", f"account {a.admin_id}: Coordinator has no zone in data_scopes, so it could see nothing")
                continue
            for zone in dict.fromkeys(zones):
                if norm(zone) not in conf_zones:
                    plan.add("WARN", f"account {a.admin_id}: zone {zone!r} matches no training's zone (would see nothing)")
                plan.grants.append(PlannedGrant(a.admin_id, "coordinator", tenant_uid, company, zone=zone, note="zone carried over from data_scopes"))

        elif a.role == "sub_coordinator":
            plan.add("BLOCK", f"account {a.admin_id}: Sub-coordinator needs a region and none is defined in the plan")

    # -- every existing account must end up with a decision ---------------------------------------
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

    plan.accounts = [_account_row(a, [g for g in plan.grants if g.admin_id == a.id]) for a in admins.values()]
    _simulate(plan, common_db, tenant_db, admins)

    zone_gaps = tenant_db.query(func.count()).select_from(Conference).filter(func.trim(func.coalesce(Conference.zone, "")) == "").scalar() or 0
    region_gaps = tenant_db.query(func.count()).select_from(Conference).filter(func.trim(func.coalesce(Conference.region, "")) == "").scalar() or 0
    if zone_gaps or region_gaps:
        plan.add("WARN", f"{zone_gaps} training(s) have no zone and {region_gaps} no region: only the Super Admin and the Company Admin can see them")
    return plan


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


def _simulate(plan: Plan, common_db: Session, tenant_db: Session, admins: dict[int, Admin]) -> None:
    """Who would see what BEFORE (today's rules) and AFTER (the planned grants). The planned
    grants go into a throw-away in-memory database; nothing is written anywhere real."""
    sim_engine = create_engine("sqlite://")
    AccessBase.metadata.create_all(sim_engine)
    sim = sessionmaker(bind=sim_engine)()
    for g in plan.grants:
        if g.status == "planned":
            sim.add(AdminAccess(admin_id=g.admin_id, role=g.role, tenant_uid=g.tenant_uid, company=g.company, zone=g.zone, region=g.region,
                                company_admin_key=g.key))
    sim.commit()

    confs = [SimpleNamespace(conferenceDate=c[0], trainerEmployeeId=c[1], zone=c[2], region=c[3], sessionType=c[4], trainingType=c[5], company=c[6])
             for c in tenant_db.query(Conference.conferenceDate, Conference.trainerEmployeeId, Conference.zone, Conference.region,
                                      Conference.sessionType, Conference.trainingType, Conference.company)]
    for admin in admins.values():
        scope = resolve_scope(sim, admin, plan.tenant_uid)
        if norm(admin.role) == "trainer":
            own = sum(1 for c in confs if c.trainerEmployeeId == admin.username)
            plan.visibility.append({"id": admin.id, "role": admin.role, "before": f"{own} own trainings", "after": f"{own} own trainings" if scope.allowed else "DENIED",
                                    "verdict": "unchanged" if scope.allowed else "LOSES ACCESS"})
            continue
        today = apply_identity_scope(tenant_db, admin, ConferenceFilters())
        before = sum(1 for c in confs if today.matches(c))
        after = sum(1 for c in confs if scope.allows_row(c.company, c.zone, c.region)) if scope.allowed else 0
        after_label = "DENIED" if not scope.allowed else f"{after} of {len(confs)}"
        if not scope.allowed:
            verdict = "LOSES ACCESS" if before else "still no access"
        elif after == before:
            verdict = "unchanged"
        else:
            verdict = f"{'widens' if after > before else 'narrows'} by {abs(after - before)}"
        plan.visibility.append({"id": admin.id, "role": scope.role.value if scope.allowed and scope.role else norm(admin.role),
                                "before": f"{before} of {len(confs)}", "after": after_label, "verdict": verdict})


# ----------------------------------------------------------------------------- report
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
    if not plan.super_admin_evidence:
        out.append("   (no Super Admin in the plan)")
    for admin_id, e in plan.super_admin_evidence.items():
        held = any(g.admin_id == admin_id and g.status == "held" for g in plan.grants)
        out.append(f"   account {admin_id}: role={e['account_role']!r} status={e['status']!r} company set={e['has_company']} password set={e['has_password']}")
        out.append(f"      recorded logins in this tenant: {e['recorded_logins']} (latest: {e['last_login'] or 'none'})")
        out.append(f"      => {'HELD: NOT granted; the account is denied until you confirm it is the authorized global account' if held else 'GRANTED (confirmed)'}")
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
