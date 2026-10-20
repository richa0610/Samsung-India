from types import SimpleNamespace
from typing import Optional

from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.exceptions import forbidden, unauthorized
from app.core.media import resolve_trainer_avatar
from app.core.security import create_access_token, verify_password
from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.repositories import admin_repository, dashboard_repository
from app.repositories.dashboard_repository import DashboardSnapshot
from app.services.access_service import AccessScope, granted_companies, norm, resolve_scope
from app.schemas.admin import (
    AdminAuthSession,
    AdminDashboardStatsOut,
    AdminLoginRequest,
    AdminOut,
    AssessmentGapItem,
    AssessmentGapSection,
    AssessmentStatsOut,
    AudienceSection,
    AudienceStatsOut,
    AudienceStatusItem,
    TrainerStatsOut,
    TrainerStatusItem,
    TrainerStatusSection,
    TrainingStatsOut,
    TrainingTypeGroup,
    TrainingTypeStatusCount,
)
from app.services import device_sessions
from app.services.activity_log_service import log_activity
from app.services.device_sessions import Device
from app.services.training.session_dashboard import audience_class
from app.services.account_ids import account_keys, with_trainer_ids
from app.utils.conference_format import session_status
from app.utils.status import title_status


LOGIN_SCOPE = "admin-login"   # rate_limit's key prefix for staff sign-in failure counts
LOGIN_FAILED = "Invalid username or password"
NOT_AUTHORIZED = "Not authorized for this tenant"


def login(
    common_db: Session,
    db: Session,
    payload: AdminLoginRequest,
    tenant_id: str,
    ip_address: str | None = None,
    device: Optional[Device] = None,
) -> AdminAuthSession:
    """`Admin` (superadmin/internal accounts) lives in the shared Common
    Database; `AgencyTeam` (partner-agency trainers) lives in the caller's
    own tenant database - see the DB-per-tenant split in app/database/."""
    # Per-account failure limit (the only login limit - none per caller IP): wrong passwords for
    # one username, from however many addresses, lock only that username in this tenant for a while.
    account = f"{tenant_id}:{payload.username}"
    rate_limit.ensure_account_not_locked(LOGIN_SCOPE, account)
    admin = admin_repository.get_admin_by_username(common_db, payload.username)
    if admin and admin.password and verify_password(payload.password, admin.password):
        rate_limit.clear_account_failures(LOGIN_SCOPE, account)
        # Correct credentials alone aren't enough: the account must actually hold an
        # admin_access grant for the tenant it's trying to log into - reusing the exact same
        # check that already gates every admin-panel request (access_service.resolve_scope), so
        # this can never fall out of sync with what a token is later allowed to do. A Super
        # Admin's global grant passes for any tenant; anyone else needs a grant naming this one.
        if not resolve_scope(common_db, admin, tenant_id).allowed:
            raise forbidden(NOT_AUTHORIZED)
        return admin_signed_in(db, admin, tenant_id, ip_address)

    # Real trainers live in `agencyteam`, not `admin` - fall back to it so
    # they can sign in the same way once they're not seeded into `admin`.
    # The login field doubles as "Company ID / Phone No", so match either
    # `username` (phone) or `offerId` (employee ID).
    agent = admin_repository.get_agency_by_username_or_offer_id(db, payload.username)
    if agent and agent.password and verify_password(payload.password, agent.password):
        rate_limit.clear_account_failures(LOGIN_SCOPE, account)
        # Only an agency account with the trainer role signs in as a trainer - a NULL or any other
        # role is refused (the approved rule; `status` is deliberately not checked). Same message
        # as an admin without a grant, so the refusal reveals nothing beyond "not allowed here".
        if not resolve_scope(common_db, agent, tenant_id).is_trainer:
            raise forbidden(NOT_AUTHORIZED)
        return trainer_signed_in(db, agent, tenant_id, ip_address, common_db=common_db, device=device)

    rate_limit.record_account_failure(LOGIN_SCOPE, account)
    raise unauthorized(LOGIN_FAILED)


def admin_signed_in(db: Session, admin: Admin, tenant_id: str, ip_address: str | None = None) -> AdminAuthSession:
    """The session for an admin-table account whose sign-in to `tenant_id` was just verified."""
    token = create_access_token(subject=f"admin:{admin.username}", tenant_id=tenant_id, role=admin.role, version=admin.tokenVersion)
    # `logsmaster` is a per-tenant table (see app/models/logs_master.py) -
    # write via `db` (this tenant), never `common_db`, even though the
    # account itself was found in the Common DB.
    log_activity(db, action="LOGIN", username=admin.username, role=admin.role, ip_address=ip_address, issued_token=token)
    return AdminAuthSession(
        access_token=token,
        admin=AdminOut(
            username=admin.username,
            name=admin.name,
            role=admin.role,
            company=admin.company,
            tenant_id=tenant_id,
            profilePicture=resolve_trainer_avatar(admin.profilePhoto, admin.gender),
        ),
    )


def trainer_signed_in(
    db: Session,
    agent: AgencyTeam,
    tenant_id: str,
    ip_address: str | None = None,
    *,
    common_db: Optional[Session] = None,
    device: Optional[Device] = None,
) -> AdminAuthSession:
    """The session for an agency trainer whose sign-in to `tenant_id` was just verified. A trainer in
    the central user registry is signed in on this device (services/device_sessions)."""
    session_id = device_sessions.begin(common_db, agent, tenant_id, device) if common_db is not None else None
    token = create_access_token(
        subject=f"agencyteam:{agent.username}", tenant_id=tenant_id, role="trainer", version=agent.tokenVersion, session_id=session_id
    )
    log_activity(db, action="LOGIN", username=agent.username, role="trainer", ip_address=ip_address, issued_token=token)
    return AdminAuthSession(
        access_token=token,
        admin=AdminOut(
            username=agent.username,
            name=agent.name or agent.username,
            role="trainer",
            offerId=agent.offerId,
            company=agent.company,
            tenant_id=tenant_id,
            profilePicture=resolve_trainer_avatar(agent.profilePhoto, agent.gender),
        ),
    )


def build_admin_dashboard_stats(
    common_db: Session,
    db: Session,
    filters: Optional[ConferenceFilters] = None,
    admin=None,
    tenant_id: Optional[str] = None,
) -> AdminDashboardStatsOut:
    """Org-wide (every trainer, every conference in this tenant) summary for
    the admin dashboard's four overview cards - unlike the trainer agenda
    and session-dashboard endpoints, which are all scoped to one trainer.

    Everything is counted in the database (see dashboard_repository): the
    filter scope is part of each query's WHERE clause, and rows come back as
    small GROUP BY results, never one row per training.

    Authorization is the caller's admin_access grant (access_service.resolve_scope), the same
    scope the Training List, Attendance list and Trainee list already use - not the legacy
    `apply_identity_scope` company/zone columns `filters` used to carry. `admin=None` (only
    possible from a direct internal call, never through the router) skips the scope condition
    entirely, the same convention list_trainings_page/list_attendance_page use."""
    scope = None if admin is None else resolve_scope(common_db, admin, tenant_id)
    conditions = dashboard_repository.conference_conditions(with_trainer_ids(db, common_db, filters))
    if scope is not None:
        conditions += dashboard_repository.access_scope_conditions(scope)
    trainer_companies = _trainer_companies(scope, filters)
    # Every aggregate below comes from this ONE database round trip.
    snapshot = dashboard_repository.dashboard_snapshot(db, conditions, trainer_companies)

    training, counted_by_type = _training_stats(snapshot)
    audience = _audience_stats(snapshot)
    trainers = _trainer_stats(common_db, scope, tenant_id, trainer_companies, snapshot, counted_by_type)
    assessment = _assessment_stats(snapshot, audience.present)
    return AdminDashboardStatsOut(training=training, audience=audience, trainers=trainers, assessment=assessment)


def _trainer_companies(scope: Optional[AccessScope], filters: Optional[ConferenceFilters]) -> Optional[set[str] | frozenset[str]]:
    """The trainer pool follows the same grant as the trainings: every company the caller's rules
    name (a grant can span several), all of this tenant for a Super Admin, none for no grant.
    Zone/region can't narrow it - no trainer record carries a zone of its own."""
    if scope is not None:
        return granted_companies(scope)
    # A direct internal call (never through the router): unscoped, as before, unless it
    # passes an explicit `filters.company`.
    return {norm(filters.company)} if filters is not None and filters.company else None


def _type_label(raw_type: Optional[str]) -> str:
    return (raw_type or "").strip() or "Other"


# --------------------------------------------------------------------------- Training card
def _training_stats(snapshot: DashboardSnapshot) -> tuple[TrainingStatsOut, dict[str, int]]:
    """The Training card, plus the counted trainings per type (the Trainers card's Status Analysis).

    The Training and Trainers cards are built from ONE shared list so their
    numbers always agree: a training counts once it's Completed, or once an
    admin has approved it and it's still to run (Scheduled or Ongoing).
    Awaiting-approval / rejected ones have their own "awaiting review"
    banner and stay out of these totals. (Approval `status` is separate from
    the session's `conferenceStatus`.)"""
    total = 0
    completed = 0
    breakdown_map: dict[str, dict[str, int]] = {}
    counted_by_type: dict[str, int] = {}
    for raw_type, raw_conf_status, raw_approval, count in snapshot.status_groups:
        conf_status = session_status(raw_conf_status)
        is_completed = conf_status == "Completed"
        is_pending = title_status(raw_approval) == "Approved" and conf_status in ("Scheduled", "Ongoing")
        if not (is_completed or is_pending):
            continue

        total += count
        if is_completed:
            completed += count

        t_type = _type_label(raw_type)
        counted_by_type[t_type] = counted_by_type.get(t_type, 0) + count
        statuses = breakdown_map.setdefault(t_type, {})
        display_status = _display_status(raw_conf_status)
        statuses[display_status] = statuses.get(display_status, 0) + count

    training = TrainingStatsOut(
        planned=total,
        completed=completed,
        pending=total - completed,
        ratePercent=round(completed / total * 100, 1) if total else 0.0,
        typeBreakdown=[
            TrainingTypeGroup(
                type=t_type,
                statuses=[TrainingTypeStatusCount(status=st, count=cnt) for st, cnt in status_counts.items()],
            )
            for t_type, status_counts in breakdown_map.items()
        ],
    )
    return training, counted_by_type


def _display_status(raw_conf_status: Optional[str]) -> str:
    raw_status = (raw_conf_status or "").strip()
    status_title = session_status(raw_status)
    if status_title == "Ongoing":
        return "Session Started"
    if status_title == "Completed":
        return "Session Completed"
    if status_title in ("Scheduled", "Approved", "Pending") or not raw_status:
        return "Session Not Started"
    return raw_status


# --------------------------------------------------------------------------- Audience card
# (label, stats key, colour) of each audience figure, in display order.
_AUDIENCE_FIELDS = (
    ("Present", "present", "#16A34A"),
    ("Absent", "absent", "#DC2626"),
    ("Not Marked", "notMarked", "#F59E0B"),
    ("Unplanned (Fresh)", "unplanned", "#0EA5E9"),
    ("UnAllocated (Ex)", "unallocated", "#64748B"),
)


def _blank_stats() -> dict[str, int]:
    return {"present": 0, "absent": 0, "notMarked": 0, "unplanned": 0, "unallocated": 0}


def _audience_stats(snapshot: DashboardSnapshot) -> AudienceStatsOut:
    type_pax_map = _pax_by_type(snapshot)
    type_stats_map = _attendance_by_type(snapshot, type_pax_map)
    totals = {key: sum(s[key] for s in type_stats_map.values()) for key in _blank_stats()}
    present, absent = totals["present"], totals["absent"]
    participants = present + absent
    return AudienceStatsOut(
        participants=participants,
        present=present,
        absent=absent,
        presentPercent=round(present / participants * 100, 1) if participants else 0.0,
        absentPercent=round(absent / participants * 100, 1) if participants else 0.0,
        typeBreakdown=_audience_sections(type_pax_map, type_stats_map, totals),
    )


def _pax_by_type(snapshot: DashboardSnapshot) -> dict[str, int]:
    """`confirmedPax` only ever holds a real number once the trainer has
    actually checked out and reported it (training.session_control.end_training) -
    same field the website's Training List shows as "Total Pax (Trainer)".
    No `batchSize` fallback: that's just the pre-planned capacity from
    when the training was created, not a real headcount, and counting it
    for a training nobody has checked out of yet inflates this total with
    bookings that haven't happened. Grouped by distinct value, so each
    free-text pax value is converted once, not once per training."""
    type_pax_map: dict[str, int] = {}
    for raw_type, raw_pax, count in snapshot.pax_groups:
        t_type = _type_label(raw_type)
        try:
            pax_val = int(raw_pax or 0)
        except (ValueError, TypeError):
            pax_val = 0
        type_pax_map[t_type] = type_pax_map.get(t_type, 0) + pax_val * count
    return type_pax_map


def _attendance_by_type(snapshot: DashboardSnapshot, type_pax_map: dict[str, int]) -> dict[str, dict[str, int]]:
    """Unplanned(Fresh) comes from the same ASSIGNED/UNASSIGNED/FRESH
    classification the single-session dashboard uses (audience_class,
    reading Attendance.sessionMeta written at join_session time) - not a
    separate heuristic, so this card can never disagree with the
    per-training Audience Breakdown card on who counts as Fresh.
    UnAllocated(Ex) is everyone else present (ASSIGNED or UNASSIGNED alike -
    "existing" as opposed to "Fresh"), so Present always equals exactly
    Unplanned + UnAllocated, with no third unlabeled bucket. Attendance
    comes back grouped by (training type, status, audience meta) - a few
    dozen rows however many trainees attended. Every type with pax gets a row too."""
    type_stats_map: dict[str, dict[str, int]] = {}
    for raw_type, att_status, session_meta, count in snapshot.attendance_groups:
        stats = type_stats_map.setdefault(_type_label(raw_type), _blank_stats())
        if att_status == "Present":
            stats["present"] += count
            fresh = audience_class(SimpleNamespace(sessionMeta=session_meta)) == "FRESH"
            stats["unplanned" if fresh else "unallocated"] += count
        elif att_status == "Absent":
            stats["absent"] += count
        else:
            stats["notMarked"] += count

    for t_type in type_pax_map:
        type_stats_map.setdefault(t_type, _blank_stats())
    return type_stats_map


def _audience_items(stats: dict[str, int]) -> list[AudienceStatusItem]:
    """Only fields with a nonzero count are shown - an all-empty scope
    (e.g. nothing marked yet) collapses to nothing rather than a wall
    of zeroes."""
    return [
        AudienceStatusItem(label=label, count=stats[key], color=color)
        for label, key, color in _AUDIENCE_FIELDS
        if stats[key] > 0
    ]


def _audience_sections(
    type_pax_map: dict[str, int], type_stats_map: dict[str, dict[str, int]], totals: dict[str, int]
) -> list[AudienceSection]:
    if not (type_pax_map or type_stats_map):
        return []
    pax_items = [AudienceStatusItem(label="Total Pax", count=sum(type_pax_map.values()))]
    pax_items += [AudienceStatusItem(label=t_type, count=cnt) for t_type, cnt in sorted(type_pax_map.items())]
    sections = [
        AudienceSection(title="Pax Count", items=pax_items),
        AudienceSection(title="Global Totals", items=_audience_items(totals)),
    ]
    # The bracket is the Present count. Unplanned (Fresh) and UnAllocated (Ex) are already
    # inside Present, so summing them again would double count.
    sections += [
        AudienceSection(title=f"{t_type} ({s['present']})", items=_audience_items(s))
        for t_type, s in sorted(type_stats_map.items())
    ]
    return sections


# --------------------------------------------------------------------------- Trainers card
# Always shown, even with a 0 count when this admin's scope has no conferences of that type yet -
# plus any other type actually present in the data, appended after them.
_STANDARD_TYPES = ["Webinar", "Classroom Training", "Product Training"]


def _trainer_stats(
    common_db: Session,
    scope: Optional[AccessScope],
    tenant_id: Optional[str],
    trainer_companies: Optional[set[str] | frozenset[str]],
    snapshot: DashboardSnapshot,
    counted_by_type: dict[str, int],
) -> TrainerStatsOut:
    # Same merge-and-dedupe-by-username as trainer_service.list_trainers - a trainer can be seeded
    # into both `admin` and `agencyteam`. Admin-table trainers live in the shared Common DB, so a
    # real request only counts those with a trainer grant for THIS tenant.
    if scope is not None:
        admin_trainers = admin_repository.list_admin_trainers_for_tenant(common_db, tenant_id, trainer_companies)
    else:
        # A direct internal call: `trainer_companies` is at most the one explicit `filters.company`.
        filter_company = next(iter(trainer_companies)) if trainer_companies else None
        admin_trainers = admin_repository.list_admin_trainers(common_db, company=filter_company)
    # Each trainer in the pool, by login name -> every value a training may name them by (their ID
    # since 2026-10-17, their login name before - account_ids.account_keys).
    trainer_keys: dict[str, set[str]] = {t.username: set(account_keys(t)) for t in admin_trainers if t.username}
    for username, uid in snapshot.agency_trainers.items():
        trainer_keys.setdefault(username, {username}).update({uid} if uid else set())
    pool = len(trainer_keys)
    # Trainers with at least one counted training (same list the Training
    # card uses) are "in training"; everyone else in the pool is idle, so
    # In Training + Idle always equals the pool.
    in_training = sum(1 for keys in trainer_keys.values() if keys & snapshot.busy_trainers)

    # Status Analysis: the same counted trainings, broken down by training
    # type, so these numbers always add up to the Training card's Planned
    # total (Completed + Pending). Deliberately NOT limited to the trainer pool
    # - a training whose trainer isn't in the pool list would otherwise be in
    # Planned but missing here. Already scoped to this admin's company/zone
    # because `conferences` is.
    sorted_types = _STANDARD_TYPES + sorted(set(counted_by_type) - set(_STANDARD_TYPES))
    status_analysis = [
        TrainerStatusSection(
            title="In Training",
            items=[TrainerStatusItem(label=t_type, count=counted_by_type.get(t_type, 0)) for t_type in sorted_types],
        )
    ]
    return TrainerStatsOut(
        pool=pool,
        inTraining=in_training,
        idle=max(pool - in_training, 0),
        utilizationPercent=round(in_training / pool * 100, 1) if pool else 0.0,
        statusAnalysis=status_analysis,
    )


# --------------------------------------------------------------------------- Assessment card
def _assessment_stats(snapshot: DashboardSnapshot, present: int) -> AssessmentStatsOut:
    attempts, passed, percent_total = snapshot.attempts, snapshot.passed, snapshot.percent_total
    avg_percent = round(percent_total / attempts, 1) if attempts else 0.0
    return AssessmentStatsOut(
        attempts=attempts,
        passCount=passed,
        failCount=attempts - passed,
        avgPercent=avg_percent,
        eligibilityGaps=_eligibility_gaps(snapshot, present, avg_percent),
    )


def _eligibility_gaps(snapshot: DashboardSnapshot, present: int, avg_percent: float) -> list[AssessmentGapSection]:
    """Eligibility & Gaps analysis - shown once anyone attempted or attended."""
    attempts, passed = snapshot.attempts, snapshot.passed
    if not (attempts > 0 or present > 0):
        return []
    present_pairs = snapshot.present_pairs
    # % of present trainees who submitted at least one assessment - counted
    # once per trainee (a conference can have Pre-Test/Post-Test/Survey as
    # separate suites, and a trainee can retake the same one), not once per
    # submission, so this stays a real 0-100% rate instead of `attempts`
    # (every submission, suites and retakes both) potentially exceeding it.
    capture_rate = round((snapshot.submitted_pairs / present_pairs) * 100) if present_pairs else 0
    pass_rate = round((passed / attempts) * 100) if attempts else 0
    return [
        AssessmentGapSection(
            title="Participation",
            items=[
                AssessmentGapItem(label="Capture Rate (Pres/Att)", value=f"{capture_rate}%", color="#2563EB"),
                AssessmentGapItem(label="Missed (No Attempt)", value=str(snapshot.missed_pairs), color="#EA580C"),
            ],
        ),
        AssessmentGapSection(
            title="Performance",
            items=[
                AssessmentGapItem(label="Pass Rate", value=f"{pass_rate}%", color="#16A34A"),
                AssessmentGapItem(label="Global Avg. Score", value=f"{avg_percent}%", color="#0D9488"),
            ],
        ),
    ]
