from types import SimpleNamespace
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import PASS_THRESHOLD_PERCENT
from app.core import rate_limit
from app.core.exceptions import forbidden, unauthorized
from app.core.media import resolve_trainer_avatar
from app.core.security import create_access_token, verify_password
from app.dependencies.filters import ConferenceFilters
from app.repositories import admin_repository, dashboard_repository
from app.services.access_service import norm, resolve_scope
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
from app.services.activity_log_service import log_activity
from app.services.training_service import _audience_class
from app.utils.status import title_status


def login(
    common_db: Session,
    db: Session,
    payload: AdminLoginRequest,
    tenant_id: str,
    ip_address: str | None = None,
) -> AdminAuthSession:
    """`Admin` (superadmin/internal accounts) lives in the shared Common
    Database; `AgencyTeam` (partner-agency trainers) lives in the caller's
    own tenant database - see the DB-per-tenant split in app/database/."""
    # Per-account failure limit on top of the per-IP one (routers/admin.py): wrong passwords for
    # one username, from however many addresses, lock only that username in this tenant for a while.
    account = f"{tenant_id}:{payload.username}"
    rate_limit.ensure_account_not_locked("admin-login", account)
    admin = admin_repository.get_admin_by_username(common_db, payload.username)
    if admin and admin.password and verify_password(payload.password, admin.password):
        rate_limit.clear_account_failures("admin-login", account)
        # Correct credentials alone aren't enough: the account must actually hold an
        # admin_access grant for the tenant it's trying to log into - reusing the exact same
        # check that already gates every admin-panel request (access_service.resolve_scope), so
        # this can never fall out of sync with what a token is later allowed to do. A Super
        # Admin's global grant passes for any tenant; anyone else needs a grant naming this one.
        if not resolve_scope(common_db, admin, tenant_id).allowed:
            raise forbidden("Not authorized for this tenant")
        token = create_access_token(subject=f"admin:{admin.username}", tenant_id=tenant_id, role=admin.role, version=admin.tokenVersion)
        # `logsmaster` is a per-tenant table (see app/models/logs_master.py) -
        # write via `db` (this tenant), never `common_db`, even though the
        # account itself was found in the Common DB.
        log_activity(db, action="LOGIN", username=admin.username, role=admin.role, ip_address=ip_address)
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

    # Real trainers live in `agencyteam`, not `admin` - fall back to it so
    # they can sign in the same way once they're not seeded into `admin`.
    # The login field doubles as "Company ID / Phone No", so match either
    # `username` (phone) or `offerId` (employee ID).
    agent = admin_repository.get_agency_by_username_or_offer_id(db, payload.username)
    if agent and agent.password and verify_password(payload.password, agent.password):
        rate_limit.clear_account_failures("admin-login", account)
        # Only an agency account with the trainer role signs in as a trainer - a NULL or any other
        # role is refused (the approved rule; `status` is deliberately not checked). Same message
        # as an admin without a grant, so the refusal reveals nothing beyond "not allowed here".
        if not resolve_scope(common_db, agent, tenant_id).is_trainer:
            raise forbidden("Not authorized for this tenant")
        token = create_access_token(subject=f"agencyteam:{agent.username}", tenant_id=tenant_id, role="trainer", version=agent.tokenVersion)
        log_activity(db, action="LOGIN", username=agent.username, role="trainer", ip_address=ip_address)
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

    rate_limit.record_account_failure("admin-login", account)
    raise unauthorized("Invalid username or password")


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
    conditions = dashboard_repository.conference_conditions(filters)
    if scope is not None:
        conditions += dashboard_repository.access_scope_conditions(scope)
    # The trainer pool follows the same grant as the trainings: every company the caller's rules
    # name (a grant can span several), all of this tenant for a Super Admin, none for no grant.
    # Zone/region can't narrow it - no trainer record carries a zone of its own.
    if scope is not None:
        trainer_companies = None if scope.is_super else {rule.company for rule in scope.rules}
    else:
        # A direct internal call (never through the router): unscoped, as before, unless it
        # passes an explicit `filters.company`.
        trainer_companies = {norm(filters.company)} if filters is not None and filters.company else None
    # Every aggregate below comes from this ONE database round trip.
    snapshot = dashboard_repository.dashboard_snapshot(db, conditions, trainer_companies)

    # The Training and Trainers cards are built from ONE shared list so their
    # numbers always agree: a training counts once it's Completed, or once an
    # admin has approved it and it's still to run (Scheduled or Ongoing).
    # Awaiting-approval / rejected ones have their own "awaiting review"
    # banner and stay out of these totals. (Approval `status` is separate from
    # the session's `conferenceStatus`.)
    total = 0
    completed = 0
    breakdown_map: dict[str, dict[str, int]] = {}
    counted_by_type: dict[str, int] = {}
    for raw_type, raw_conf_status, raw_approval, count in snapshot.status_groups:
        conf_status = title_status(raw_conf_status)
        is_completed = conf_status == "Completed"
        is_pending = title_status(raw_approval) == "Approved" and conf_status in ("Scheduled", "Ongoing")
        if not (is_completed or is_pending):
            continue

        total += count
        if is_completed:
            completed += count

        t_type = (raw_type or "").strip() or "Other"
        counted_by_type[t_type] = counted_by_type.get(t_type, 0) + count

        raw_status = (raw_conf_status or "").strip()
        status_title = title_status(raw_status)
        if status_title == "Ongoing":
            display_status = "Session Started"
        elif status_title == "Completed":
            display_status = "Session Completed"
        elif status_title in ("Scheduled", "Approved", "Pending") or not raw_status:
            display_status = "Session Not Started"
        else:
            display_status = raw_status

        breakdown_map.setdefault(t_type, {})
        breakdown_map[t_type][display_status] = breakdown_map[t_type].get(display_status, 0) + count
    pending = total - completed

    type_breakdown: list[TrainingTypeGroup] = [
        TrainingTypeGroup(
            type=t_type,
            statuses=[
                TrainingTypeStatusCount(status=st, count=cnt)
                for st, cnt in status_counts.items()
            ],
        )
        for t_type, status_counts in breakdown_map.items()
    ]

    training = TrainingStatsOut(
        planned=total,
        completed=completed,
        pending=pending,
        ratePercent=round(completed / total * 100, 1) if total else 0.0,
        typeBreakdown=type_breakdown,
    )

    # `confirmedPax` only ever holds a real number once the trainer has
    # actually checked out and reported it (training_service.end_training) -
    # same field the website's Training List shows as "Total Pax (Trainer)".
    # No `batchSize` fallback: that's just the pre-planned capacity from
    # when the training was created, not a real headcount, and counting it
    # for a training nobody has checked out of yet inflates this total with
    # bookings that haven't happened. Grouped by distinct value, so each
    # free-text pax value is converted once, not once per training.
    type_pax_map: dict[str, int] = {}
    for raw_type, raw_pax, count in snapshot.pax_groups:
        t_type = (raw_type or "").strip() or "Other"
        try:
            pax_val = int(raw_pax or 0)
        except (ValueError, TypeError):
            pax_val = 0
        type_pax_map[t_type] = type_pax_map.get(t_type, 0) + pax_val * count

    # Unplanned(Fresh) comes from the same ASSIGNED/UNASSIGNED/FRESH
    # classification the single-session dashboard uses (_audience_class,
    # reading Attendance.sessionMeta written at join_session time) - not a
    # separate heuristic, so this card can never disagree with the
    # per-training Audience Breakdown card on who counts as Fresh.
    # UnAllocated(Ex) is everyone else present (ASSIGNED or UNASSIGNED alike -
    # "existing" as opposed to "Fresh"), so Present always equals exactly
    # Unplanned + UnAllocated, with no third unlabeled bucket. Attendance
    # comes back grouped by (training type, status, audience meta) - a few
    # dozen rows however many trainees attended.
    def _blank_stats() -> dict[str, int]:
        return {"present": 0, "absent": 0, "notMarked": 0, "unplanned": 0, "unallocated": 0}

    type_stats_map: dict[str, dict[str, int]] = {}
    for raw_type, att_status, session_meta, count in snapshot.attendance_groups:
        t_type = (raw_type or "").strip() or "Other"
        stats = type_stats_map.setdefault(t_type, _blank_stats())
        if att_status == "Present":
            stats["present"] += count
            if _audience_class(SimpleNamespace(sessionMeta=session_meta)) == "FRESH":
                stats["unplanned"] += count
            else:
                stats["unallocated"] += count
        elif att_status == "Absent":
            stats["absent"] += count
        else:
            stats["notMarked"] += count

    for t_type in type_pax_map:
        type_stats_map.setdefault(t_type, _blank_stats())

    present = sum(s["present"] for s in type_stats_map.values())
    absent = sum(s["absent"] for s in type_stats_map.values())
    participants = present + absent

    total_pax = sum(type_pax_map.values())
    global_present = present
    global_unplanned = sum(s["unplanned"] for s in type_stats_map.values())
    global_unallocated = sum(s["unallocated"] for s in type_stats_map.values())
    global_absent = absent
    global_not_marked = sum(s["notMarked"] for s in type_stats_map.values())

    audience_breakdown: list[AudienceSection] = []
    if type_pax_map or type_stats_map:
        pax_items = [AudienceStatusItem(label="Total Pax", count=total_pax)]
        for t_type, cnt in sorted(type_pax_map.items()):
            pax_items.append(AudienceStatusItem(label=t_type, count=cnt))
        audience_breakdown.append(AudienceSection(title="Pax Count", items=pax_items))

        # Only fields with a nonzero count are shown - an all-empty scope
        # (e.g. nothing marked yet) collapses to nothing rather than a wall
        # of zeroes.
        global_candidates = [
            ("Present", global_present, "#16A34A"),
            ("Absent", global_absent, "#DC2626"),
            ("Not Marked", global_not_marked, "#F59E0B"),
            ("Unplanned (Fresh)", global_unplanned, "#0EA5E9"),
            ("UnAllocated (Ex)", global_unallocated, "#64748B"),
        ]
        global_items = [
            AudienceStatusItem(label=label, count=cnt, color=color)
            for label, cnt, color in global_candidates
            if cnt > 0
        ]
        audience_breakdown.append(
            AudienceSection(
                title="Global Totals",
                items=global_items,
            )
        )

        for t_type, s in sorted(type_stats_map.items()):
            type_candidates = [
                ("Present", s["present"], "#16A34A"),
                ("Absent", s["absent"], "#DC2626"),
                ("Not Marked", s["notMarked"], "#F59E0B"),
                ("Unplanned (Fresh)", s["unplanned"], "#0EA5E9"),
                ("UnAllocated (Ex)", s["unallocated"], "#64748B"),
            ]
            audience_breakdown.append(
                AudienceSection(
                    # The bracket is the Present count. Unplanned (Fresh) and
                    # UnAllocated (Ex) are already inside Present, so summing
                    # them again would double count.
                    title=f"{t_type} ({s['present']})",
                    items=[
                        AudienceStatusItem(label=label, count=cnt, color=color)
                        for label, cnt, color in type_candidates
                        if cnt > 0
                    ],
                )
            )

    audience = AudienceStatsOut(
        participants=participants,
        present=present,
        absent=absent,
        presentPercent=round(present / participants * 100, 1) if participants else 0.0,
        absentPercent=round(absent / participants * 100, 1) if participants else 0.0,
        typeBreakdown=audience_breakdown,
    )

    # Same merge-and-dedupe-by-username as trainer_service.list_trainers - a trainer can be seeded
    # into both `admin` and `agencyteam`. Admin-table trainers live in the shared Common DB, so a
    # real request only counts those with a trainer grant for THIS tenant.
    admin_trainers = (
        admin_repository.list_admin_trainers_for_tenant(common_db, tenant_id, trainer_companies)
        if scope is not None
        else admin_repository.list_admin_trainers(common_db, company=next(iter(trainer_companies)) if trainer_companies else None)
    )
    trainer_usernames = {t.username for t in admin_trainers if t.username}
    trainer_usernames |= snapshot.agency_trainers
    pool = len(trainer_usernames)
    # Trainers with at least one counted training (same list the Training
    # card uses) are "in training"; everyone else in the pool is idle, so
    # In Training + Idle always equals the pool.
    busy_trainer_usernames = snapshot.busy_trainers & trainer_usernames
    in_training = len(busy_trainer_usernames)
    idle = max(pool - in_training, 0)

    # Status Analysis: the same counted trainings, broken down by training
    # type, so these numbers always add up to the Training card's Planned
    # total (Completed + Pending). Deliberately NOT limited to the trainer pool
    # - a training whose trainer isn't in the pool list would otherwise be in
    # Planned but missing here. Already scoped to this admin's company/zone
    # because `conferences` is.
    in_training_by_type = counted_by_type

    # Always show the three standard types, even with a 0 count when this
    # admin's scope has no conferences of that type yet - plus any other
    # type actually present in the data, appended after them.
    STANDARD_TYPES = ["Webinar", "Classroom Training", "Product Training"]
    extra_types = sorted(set(in_training_by_type) - set(STANDARD_TYPES))
    sorted_types = STANDARD_TYPES + extra_types

    trainer_status_analysis: list[TrainerStatusSection] = [
        TrainerStatusSection(
            title="In Training",
            items=[
                TrainerStatusItem(label=t_type, count=in_training_by_type.get(t_type, 0))
                for t_type in sorted_types
            ],
        )
    ]

    trainers = TrainerStatsOut(
        pool=pool,
        inTraining=in_training,
        idle=idle,
        utilizationPercent=round(in_training / pool * 100, 1) if pool else 0.0,
        statusAnalysis=trainer_status_analysis,
    )

    attempts, passed, percent_total = snapshot.attempts, snapshot.passed, snapshot.percent_total
    fail_count = attempts - passed
    avg_percent = round(percent_total / attempts, 1) if attempts else 0.0

    # Build Eligibility & Gaps analysis
    present_pair_count, missed_count = snapshot.present_pairs, snapshot.missed_pairs
    submitted_pair_count = snapshot.submitted_pairs
    # % of present trainees who submitted at least one assessment - counted
    # once per trainee (a conference can have Pre-Test/Post-Test/Survey as
    # separate suites, and a trainee can retake the same one), not once per
    # submission, so this stays a real 0-100% rate instead of `attempts`
    # (every submission, suites and retakes both) potentially exceeding it.
    capture_rate = round((submitted_pair_count / present_pair_count) * 100) if present_pair_count else 0
    pass_rate = round((passed / attempts) * 100) if attempts else 0

    eligibility_gaps: list[AssessmentGapSection] = []
    if attempts > 0 or present > 0:
        eligibility_gaps = [
            AssessmentGapSection(
                title="Participation",
                items=[
                    AssessmentGapItem(
                        label="Capture Rate (Pres/Att)",
                        value=f"{capture_rate}%",
                        color="#2563EB",
                    ),
                    AssessmentGapItem(
                        label="Missed (No Attempt)",
                        value=str(missed_count),
                        color="#EA580C",
                    ),
                ],
            ),
            AssessmentGapSection(
                title="Performance",
                items=[
                    AssessmentGapItem(
                        label="Pass Rate",
                        value=f"{pass_rate}%",
                        color="#16A34A",
                    ),
                    AssessmentGapItem(
                        label="Global Avg. Score",
                        value=f"{avg_percent}%",
                        color="#0D9488",
                    ),
                ],
            ),
        ]

    assessment = AssessmentStatsOut(
        attempts=attempts,
        passCount=passed,
        failCount=fail_count,
        avgPercent=avg_percent,
        eligibilityGaps=eligibility_gaps,
    )

    return AdminDashboardStatsOut(training=training, audience=audience, trainers=trainers, assessment=assessment)
