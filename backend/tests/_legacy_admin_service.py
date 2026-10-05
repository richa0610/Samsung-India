from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import PASS_THRESHOLD_PERCENT
from app.core.exceptions import unauthorized
from app.core.media import resolve_trainer_avatar
from app.core.security import create_access_token, verify_password
from app.dependencies.filters import ConferenceFilters
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.repositories import admin_repository, assessment_repository, conference_repository
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
from tests import _legacy_queries as legacy_queries


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
    admin = admin_repository.get_admin_by_username(common_db, payload.username)
    if admin and admin.password and verify_password(payload.password, admin.password):
        token = create_access_token(subject=f"admin:{admin.username}", tenant_id=tenant_id, role=admin.role)
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
        token = create_access_token(
            subject=f"agencyteam:{agent.username}", tenant_id=tenant_id, role=agent.role or "trainer"
        )
        log_activity(db, action="LOGIN", username=agent.username, role=agent.role or "trainer", ip_address=ip_address)
        return AdminAuthSession(
            access_token=token,
            admin=AdminOut(
                username=agent.username,
                name=agent.name or agent.username,
                role=agent.role or "trainer",
                offerId=agent.offerId,
                company=agent.company,
                tenant_id=tenant_id,
                profilePicture=resolve_trainer_avatar(agent.profilePhoto, agent.gender),
            ),
        )

    raise unauthorized("Invalid username or password")


def build_admin_dashboard_stats(
    common_db: Session, db: Session, filters: Optional[ConferenceFilters] = None
) -> AdminDashboardStatsOut:
    """Org-wide (every trainer, every conference in this tenant) summary for
    the admin dashboard's four overview cards - unlike the trainer agenda
    and session-dashboard endpoints, which are all scoped to one trainer."""
    all_conferences = legacy_queries.conference_list_all(db)
    # A cancelled training is excluded from every number on this dashboard -
    # its attendance and test results included.
    cancelled_uids = {c.conferenceUid for c in all_conferences if title_status(c.conferenceStatus) == "Cancelled"}
    # The admin panel's shared filter (date, trainer, zone, ...) narrows every
    # number the same way: anything outside it is excluded like a cancelled
    # one. Always run `.matches()` (not gated on `.active`) - `filters` can
    # carry a mandatory identity scope (company/zone, see data_scope_service)
    # with no optional filter chosen, and an all-empty filter still matches
    # everything, so this is a no-op when there's genuinely nothing to narrow.
    if filters is not None:
        cancelled_uids |= {c.conferenceUid for c in all_conferences if not filters.matches(c)}
    conferences = [c for c in all_conferences if c.conferenceUid not in cancelled_uids]
    # The Training and Trainers cards are built from ONE shared list so their
    # numbers always agree: a training counts once it's Completed, or once an
    # admin has approved it and it's still to run (Scheduled or Ongoing).
    # Awaiting-approval / rejected ones have their own "awaiting review"
    # banner and stay out of these totals. (Approval `status` is separate from
    # the session's `conferenceStatus`.)
    def _is_completed(c: Conference) -> bool:
        return title_status(c.conferenceStatus) == "Completed"

    def _is_pending(c: Conference) -> bool:
        return title_status(c.status) == "Approved" and title_status(c.conferenceStatus) in ("Scheduled", "Ongoing")

    counted = [c for c in conferences if _is_completed(c) or _is_pending(c)]
    total = len(counted)
    completed = sum(1 for c in counted if _is_completed(c))
    pending = total - completed

    breakdown_map: dict[str, dict[str, int]] = {}
    for c in counted:
        t_type = (c.trainingType or "").strip() or "Other"
        raw_status = (c.conferenceStatus or "").strip()
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
        breakdown_map[t_type][display_status] = breakdown_map[t_type].get(display_status, 0) + 1

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

    kept_uids = {c.conferenceUid for c in conferences}
    filtering = filters is not None
    all_attendances = [
        att
        for att in db.query(Attendance).all()
        if att.conferenceUid not in cancelled_uids and (not filtering or att.conferenceUid in kept_uids)
    ]
    present = sum(1 for att in all_attendances if att.status == "Present")
    absent = sum(1 for att in all_attendances if att.status == "Absent")
    participants = present + absent

    # Build Audience Type Breakdown
    conf_by_uid = {c.conferenceUid: c for c in conferences}
    type_pax_map: dict[str, int] = {}
    type_stats_map: dict[str, dict[str, int]] = {}

    # `confirmedPax` only ever holds a real number once the trainer has
    # actually checked out and reported it (training_service.end_training) -
    # same field the website's Training List shows as "Total Pax (Trainer)".
    # No `batchSize` fallback: that's just the pre-planned capacity from
    # when the training was created, not a real headcount, and counting it
    # for a training nobody has checked out of yet inflates this total with
    # bookings that haven't happened.
    for c in conferences:
        t_type = (c.trainingType or "").strip() or "Other"
        try:
            pax_val = int(c.confirmedPax or 0)
        except (ValueError, TypeError):
            pax_val = 0
        type_pax_map[t_type] = type_pax_map.get(t_type, 0) + pax_val

    # Unplanned(Fresh) comes from the same ASSIGNED/UNASSIGNED/FRESH
    # classification the single-session dashboard uses (_audience_class,
    # reading Attendance.sessionMeta written at join_session time) - not a
    # separate heuristic, so this card can never disagree with the
    # per-training Audience Breakdown card on who counts as Fresh.
    # UnAllocated(Ex) is everyone else present (ASSIGNED or UNASSIGNED alike -
    # "existing" as opposed to "Fresh"), so Present always equals exactly
    # Unplanned + UnAllocated, with no third unlabeled bucket.
    def _blank_stats() -> dict[str, int]:
        return {"present": 0, "absent": 0, "notMarked": 0, "unplanned": 0, "unallocated": 0}

    for att in all_attendances:
        c = conf_by_uid.get(att.conferenceUid)
        t_type = (c.trainingType or "").strip() or "Other" if c else "Other"
        type_stats_map.setdefault(t_type, _blank_stats())
        if att.status == "Present":
            type_stats_map[t_type]["present"] += 1
            if _audience_class(att) == "FRESH":
                type_stats_map[t_type]["unplanned"] += 1
            else:
                type_stats_map[t_type]["unallocated"] += 1
        elif att.status == "Absent":
            type_stats_map[t_type]["absent"] += 1
        else:
            type_stats_map[t_type]["notMarked"] += 1

    for t_type in type_pax_map:
        type_stats_map.setdefault(t_type, _blank_stats())

    total_pax = sum(type_pax_map.values())
    global_present = sum(s["present"] for s in type_stats_map.values()) if type_stats_map else present
    global_unplanned = sum(s["unplanned"] for s in type_stats_map.values())
    global_unallocated = sum(s["unallocated"] for s in type_stats_map.values())
    global_absent = sum(1 for att in all_attendances if att.status == "Absent")
    global_not_marked = sum(1 for att in all_attendances if att.status not in ("Present", "Absent"))

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

    # Same merge-and-dedupe-by-username as trainer_service.list_trainers -
    # a trainer can be seeded into both `admin` and `agencyteam`. Scoped to
    # the caller's own company (same as everything else on this dashboard) -
    # zone can't apply here, since no trainer record has a zone of its own.
    scope_company = filters.company if filters is not None else None
    trainer_usernames = {
        t.username for t in admin_repository.list_admin_trainers(common_db, company=scope_company) if t.username
    }
    trainer_usernames |= {
        t.username for t in admin_repository.list_agency_trainers(db, company=scope_company) if t.username
    }
    pool = len(trainer_usernames)
    # Trainers with at least one counted training (same list the Training
    # card uses) are "in training"; everyone else in the pool is idle, so
    # In Training + Idle always equals the pool.
    busy_trainer_usernames = {c.trainerEmployeeId for c in counted if c.trainerEmployeeId} & trainer_usernames
    in_training = len(busy_trainer_usernames)
    idle = max(pool - in_training, 0)

    # Status Analysis: the same counted trainings, broken down by training
    # type, so these numbers always add up to the Training card's Planned
    # total (Completed + Pending). Deliberately NOT limited to the trainer pool
    # - a training whose trainer isn't in the pool list would otherwise be in
    # Planned but missing here. Already scoped to this admin's company/zone
    # because `conferences` is.
    in_training_by_type: dict[str, int] = {}
    for c in counted:
        t_type = (c.trainingType or "").strip() or "Other"
        in_training_by_type[t_type] = in_training_by_type.get(t_type, 0) + 1

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

    results = [
        r
        for r in legacy_queries.list_all_submitted_results(db)
        if r.conferenceUid not in cancelled_uids and (not filtering or r.conferenceUid in kept_uids)
    ]
    attempts = len(results)
    passed = sum(1 for r in results if float(r.percentage) >= PASS_THRESHOLD_PERCENT)
    fail_count = attempts - passed
    avg_percent = round(sum(float(r.percentage) for r in results) / attempts, 1) if attempts else 0.0

    # Build Eligibility & Gaps analysis
    present_pairs = {
        (att.conferenceUid, att.traineeUid) for att in all_attendances if att.status == "Present"
    }
    submitted_pairs = {
        (r.conferenceUid, r.traineeUid)
        for r in results
        if r.conferenceUid and r.traineeUid
    }
    missed_count = len(present_pairs - submitted_pairs) if present_pairs else 0
    # % of present trainees who submitted at least one assessment - counted
    # once per trainee (a conference can have Pre-Test/Post-Test/Survey as
    # separate suites, and a trainee can retake the same one), not once per
    # submission, so this stays a real 0-100% rate instead of `attempts`
    # (every submission, suites and retakes both) potentially exceeding it.
    capture_rate = round((len(submitted_pairs) / len(present_pairs)) * 100) if present_pairs else 0
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
