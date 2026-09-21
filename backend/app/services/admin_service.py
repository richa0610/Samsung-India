from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import PASS_THRESHOLD_PERCENT
from app.core.exceptions import unauthorized
from app.core.media import resolve_trainer_avatar
from app.core.security import create_access_token, verify_password
from app.dependencies.filters import ConferenceFilters
from app.models.attendance import Attendance
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
    all_conferences = conference_repository.list_all(db)
    # A cancelled training is excluded from every number on this dashboard -
    # its attendance and test results included.
    cancelled_uids = {c.conferenceUid for c in all_conferences if title_status(c.conferenceStatus) == "Cancelled"}
    # The admin panel's shared filter (date, trainer, zone, ...) narrows every
    # number the same way: anything outside it is excluded like a cancelled one.
    if filters is not None and filters.active:
        cancelled_uids |= {c.conferenceUid for c in all_conferences if not filters.matches(c)}
    conferences = [c for c in all_conferences if c.conferenceUid not in cancelled_uids]
    total = len(conferences)
    completed = sum(1 for c in conferences if title_status(c.conferenceStatus) == "Completed")
    pending = total - completed

    breakdown_map: dict[str, dict[str, int]] = {}
    for c in conferences:
        t_type = (c.trainingType or "").strip() or "Other"
        raw_status = (c.conferenceStatus or "").strip()
        status_title = title_status(raw_status)
        if status_title == "Ongoing":
            display_status = "Session Started"
        elif status_title == "Completed":
            display_status = "Session Completed"
        elif status_title in ("Scheduled", "Approved", "Pending"):
            display_status = "Session Not Started"
        elif not raw_status:
            display_status = "Unknown"
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
    filtering = filters is not None and filters.active
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

    for c in conferences:
        t_type = (c.trainingType or "").strip() or "Other"
        try:
            pax_val = int(c.confirmedPax or c.batchSize or 0)
        except (ValueError, TypeError):
            pax_val = 0
        type_pax_map[t_type] = type_pax_map.get(t_type, 0) + pax_val

    for att in all_attendances:
        c = conf_by_uid.get(att.conferenceUid)
        t_type = (c.trainingType or "").strip() or "Other" if c else "Other"
        type_stats_map.setdefault(t_type, {"present": 0, "unplanned": 0, "unallocated": 0})
        if att.status == "Present":
            type_stats_map[t_type]["present"] += 1
            if att.geofenceBypass or (att.remarks and "unplanned" in str(att.remarks).lower()):
                type_stats_map[t_type]["unplanned"] += 1

    for t_type, pax_val in type_pax_map.items():
        type_stats_map.setdefault(t_type, {"present": 0, "unplanned": 0, "unallocated": 0})
        pres = type_stats_map[t_type]["present"]
        type_stats_map[t_type]["unallocated"] = max(pax_val - pres, 0)
        if type_stats_map[t_type]["unplanned"] == 0 and pax_val > 0 and pres > pax_val:
            type_stats_map[t_type]["unplanned"] = pres - pax_val

    total_pax = sum(type_pax_map.values())
    global_present = sum(s["present"] for s in type_stats_map.values()) if type_stats_map else present
    global_unplanned = sum(s["unplanned"] for s in type_stats_map.values())
    global_unallocated = sum(s["unallocated"] for s in type_stats_map.values())

    audience_breakdown: list[AudienceSection] = []
    if type_pax_map or type_stats_map:
        pax_items = [AudienceStatusItem(label="Total Pax", count=total_pax)]
        for t_type, cnt in sorted(type_pax_map.items()):
            pax_items.append(AudienceStatusItem(label=t_type, count=cnt))
        audience_breakdown.append(AudienceSection(title="Pax Count", items=pax_items))

        audience_breakdown.append(
            AudienceSection(
                title="Global Totals",
                items=[
                    AudienceStatusItem(label="Present", count=global_present, color="#16A34A"),
                    AudienceStatusItem(label="Unplanned (Fresh)", count=global_unplanned, color="#0EA5E9"),
                    AudienceStatusItem(label="UnAllocated (Ex)", count=global_unallocated, color="#64748B"),
                ],
            )
        )

        for t_type, s in sorted(type_stats_map.items()):
            tot = s["present"] + s["unplanned"] + s["unallocated"]
            audience_breakdown.append(
                AudienceSection(
                    title=f"{t_type} ({tot if tot > 0 else s['present']})",
                    items=[
                        AudienceStatusItem(label="Present", count=s["present"], color="#16A34A"),
                        AudienceStatusItem(label="Unplanned", count=s["unplanned"], color="#0EA5E9"),
                        AudienceStatusItem(label="UnAllocated", count=s["unallocated"], color="#64748B"),
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
    # a trainer can be seeded into both `admin` and `agencyteam`.
    trainer_usernames = {t.username for t in admin_repository.list_admin_trainers(common_db) if t.username}
    trainer_usernames |= {t.username for t in admin_repository.list_agency_trainers(db) if t.username}
    pool = len(trainer_usernames)
    ongoing_trainer_usernames = {
        c.trainerEmployeeId
        for c in conferences
        if c.trainerEmployeeId and title_status(c.conferenceStatus) == "Ongoing"
    }
    in_training = len(ongoing_trainer_usernames & trainer_usernames) if trainer_usernames else 0
    idle = max(pool - in_training, 0)

    # Status Analysis: "In Training" broken down by training type
    in_training_by_type: dict[str, int] = {}
    for c in conferences:
        if c.trainerEmployeeId and title_status(c.conferenceStatus) == "Ongoing":
            if not trainer_usernames or c.trainerEmployeeId in trainer_usernames:
                t_type = (c.trainingType or "").strip() or "Other"
                in_training_by_type[t_type] = in_training_by_type.get(t_type, 0) + 1

    distinct_types = {
        (c.trainingType or "").strip()
        for c in conferences
        if (c.trainingType or "").strip()
    }
    order_priority = {"webinar": 1, "classroom training": 2, "product training": 3}
    sorted_types = sorted(distinct_types, key=lambda x: (order_priority.get(x.lower(), 99), x))

    trainer_status_analysis: list[TrainerStatusSection] = []
    if sorted_types:
        trainer_status_analysis.append(
            TrainerStatusSection(
                title="In Training",
                items=[
                    TrainerStatusItem(label=t_type, count=in_training_by_type.get(t_type, 0))
                    for t_type in sorted_types
                ],
            )
        )

    trainers = TrainerStatsOut(
        pool=pool,
        inTraining=in_training,
        idle=idle,
        utilizationPercent=round(in_training / pool * 100, 1) if pool else 0.0,
        statusAnalysis=trainer_status_analysis,
    )

    results = [
        r
        for r in assessment_repository.list_all_submitted_results(db)
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
    capture_rate = round((attempts / present) * 100) if present else 0
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
