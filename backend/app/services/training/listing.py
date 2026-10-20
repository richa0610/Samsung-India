"""The paged training and attendance lists, the Sessions screen's filter options and the trainer Home
summary - each restricted to what the caller's access grant authorizes, filtered and paged in SQL."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_SESSION_TITLE, UNKNOWN_TRAINEE_NAME
from app.core.exceptions import bad_request
from app.dependencies.filters import ConferenceFilters
from app.dependencies.paging import PageRequest
from app.models.admin import Admin
from app.models.conference import Conference
from app.repositories import (
    assessment_repository,
    attendance_repository,
    catalog_repository,
    conference_repository,
    dashboard_repository,
)
from app.schemas.training import (
    AttendanceListItemOut,
    AttendancePageResponse,
    TrainerSummaryOut,
    TrainingAgendaItem,
    TrainingFacetsOut,
    TrainingPageResponse,
)
from app.services import account_ids
from app.services.access_service import AccessScope, own_trainings_keys, resolve_scope
from app.utils.conference_format import assigned, location_label, session_status
from app.utils.date_utils import ist_now, to_venue_time
from app.utils.places import place_name
from app.utils.status import title_status


def _real_headcounts(db: Session, conference_uids: list[str]) -> dict[str, int]:
    """Real headcount per conference - the same "who actually showed up or
    attempted the test" definition used by the single-session dashboard
    (see `session_dashboard.build_dashboard`) - rather than the planned `batchSize` field,
    which is just whatever capacity number the trainer typed in at
    creation time and never reflects who was actually trained. Counted in SQL
    (dashboard_repository.count_trained_by_conference)."""
    return dashboard_repository.count_trained_by_conference(db, conference_uids)


def venue_names_for(db: Session, conferences: list[Conference]) -> dict[str, str]:
    venue_uids = {assigned(c.venueUid) for c in conferences} - {None}
    if not venue_uids:
        return {}
    return {v.venueUid: v.name for v in catalog_repository.get_venues_by_uids(db, venue_uids) if v.name}


def _updated_by_names_for(db: Session, conferences: list[Conference], common_db: Optional[Session] = None) -> dict[str, str]:
    """`conference.updatedBy` names whoever last saved the row - by account ID since 2026-10-17
    (account_ids), as a bare login name before - resolve those to display names in one batch, the
    same way `venue_names_for` resolves venue UIDs. Anything that doesn't match a real
    admin/agencyteam account (old seed-script rows, which stamped the script's filename instead)
    is left for the caller to fall back to the raw value."""
    stored = {c.updatedBy for c in conferences if c.updatedBy}
    if not stored:
        return {}
    # The request's own Common DB session when the caller has one (no extra connection).
    if common_db is not None:
        return account_ids.names_by_key(db, common_db, stored)

    from app.database.common import CommonSessionLocal

    common_db = CommonSessionLocal()
    try:
        return account_ids.names_by_key(db, common_db, stored)
    finally:
        common_db.close()


def _to_agenda_item(
    conference: Conference,
    trainee_count: int,
    venue_name_by_uid: dict[str, str],
    updated_by_name_by_username: dict[str, str],
) -> TrainingAgendaItem:
    return TrainingAgendaItem(
        conferenceUid=conference.conferenceUid,
        title=conference.suiteTitle or conference.trainingType or DEFAULT_SESSION_TITLE,
        trainerName=conference.trainerName,
        hoid=conference.trainerEmployeeId,
        zone=conference.zone,
        sessionType=conference.sessionType,
        conferenceDate=conference.conferenceDate,
        conferenceTime=to_venue_time(conference.conferenceTime),
        conferenceStatus=session_status(conference.conferenceStatus),
        approvalStatus=title_status(conference.status),
        location=location_label(conference),
        batchSize=conference.batchSize,
        trainingType=conference.trainingType,
        state=place_name(conference.state) or None,
        district=place_name(conference.district) or None,
        trainingHub=assigned(conference.trainingHub),
        venueName=venue_name_by_uid.get(conference.venueUid),
        updatedBy=(
            updated_by_name_by_username.get(conference.updatedBy, conference.updatedBy)
            if conference.updatedBy
            else None
        ),
        updationOn=conference.updationOn.strftime("%Y-%m-%d %H:%M:%S") if conference.updationOn else None,
        timestamp=conference.timestamp.strftime("%Y-%m-%d %H:%M:%S") if conference.timestamp else None,
        traineeCount=trainee_count,
    )


def _agenda_items(
    db: Session, conferences: list[Conference], common_db: Optional[Session]
) -> list[TrainingAgendaItem]:
    """List rows for these trainings, enriched in one batch each: headcounts, venue and updater names."""
    headcounts = _real_headcounts(db, [c.conferenceUid for c in conferences])
    venue_name_by_uid = venue_names_for(db, conferences)
    updated_by_name_by_username = _updated_by_names_for(db, conferences, common_db)
    return [
        _to_agenda_item(
            conference,
            headcounts.get(conference.conferenceUid, 0),
            venue_name_by_uid,
            updated_by_name_by_username,
        )
        for conference in conferences
    ]


def trainer_summary(
    db: Session,
    admin: Admin,
    start: Optional[str] = None,
    end: Optional[str] = None,
    common_db: Optional[Session] = None,
    tenant_id: Optional[str] = None,
) -> TrainerSummaryOut:
    """The trainer Home dashboard: its numbers for today (no range) or for start..end, counted in
    SQL (dashboard_repository.trainer_summary_counts - two statements, whatever the trainer's
    history), plus the Recent Sessions card - always the two most recently completed trainings,
    whatever the range. Only the trainer's own trainings, verified server-side."""
    trainer = own_trainings_keys(common_db, admin, tenant_id)
    counts = dashboard_repository.trainer_summary_counts(
        db, trainer, start, end, today=ist_now().date().isoformat(), today_ist=ist_now().date().isoformat()
    )
    total = counts["totalSessions"]
    recent = conference_repository.list_recent_completed_for_trainer(db, trainer, 2)
    pending_total = counts["pending"] + counts.get("pendingApproval", 0)
    return TrainerSummaryOut(
        **counts,
        executedPercentage=round(counts["completed"] / total * 100) if total else 0,
        pendingPercentage=round(pending_total / total * 100) if total else 0,
        recentCompleted=_agenda_items(db, recent, common_db),
    )


def _list_scope(admin: Optional[Admin], common_db: Optional[Session], tenant_id: Optional[str]) -> Optional[AccessScope]:
    """The access scope a paged list is restricted to. A real request always has `common_db` and
    `tenant_id`; one missing anyway is a caller bug and fails CLOSED (no access), never open.
    `admin=None` - only a direct internal call, never through the router - means no principal to
    check, so None: no scope condition at all."""
    if admin is None:
        return None
    if common_db is None:
        return AccessScope.denied(tenant_id or "", "no scope context")
    return resolve_scope(common_db, admin, tenant_id)


def list_trainings_page(
    db: Session,
    admin: Optional[Admin],
    filters: Optional[ConferenceFilters],
    approval: Optional[str],
    search: Optional[str],
    sort: str,
    descending: bool,
    paging: PageRequest,
    common_db: Optional[Session] = None,
    tenant_id: Optional[str] = None,
    *,
    on_date: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
) -> TrainingPageResponse:
    """One page (default 50 rows) of the admin org-wide Training / Pending list, restricted to
    what `admin`'s admin_access grant authorizes: a Super Admin sees every company, a Company
    Admin their own company, a Coordinator their zone, a Sub-coordinator their region - resolved
    the same way the session-operation authorization already does (access_service.resolve_scope),
    never from company/zone/region the client sends. `filters` only narrows further, inside that
    boundary; it can never widen past it. An active trainer gets the same list restricted to the
    trainings assigned to them (dashboard_repository.conference_authorization_conditions) - their
    own Training / Pending Training List.

    `common_db`/`tenant_id` are what resolve_scope needs (see `_list_scope` for how a missing one,
    or `admin=None`, is handled).

    `on_date` / `status` / `location` are the trainer Sessions screen's tab and filters
    (conference_repository.session_conditions), and `sort="session"` its grouped order.

    Filtering, searching, sorting and paging all happen in the database; only
    this page's rows are enriched (headcounts, venue and updater names), so the
    cost per request is the page size, not the size of the tenant."""
    scope = _list_scope(admin, common_db, tenant_id)
    filters = account_ids.with_trainer_ids(db, common_db, filters)
    conditions = dashboard_repository.conference_conditions(filters, include_cancelled=True)
    conditions += conference_repository.session_conditions(
        on_date, status, location, today=ist_now().date().isoformat()
    )
    if scope is not None:
        conditions += dashboard_repository.conference_authorization_conditions(scope)
    try:
        result = conference_repository.list_page(
            db, conditions, approval, search, sort, descending, paging.cursor, paging.limit, paging.page
        )
    except (ValueError, KeyError, TypeError):
        raise bad_request("Invalid page cursor")

    return TrainingPageResponse(items=_agenda_items(db, result.rows, common_db), **result.meta())


def training_facets(
    db: Session,
    admin: Admin,
    filters: Optional[ConferenceFilters],
    common_db: Optional[Session] = None,
    tenant_id: Optional[str] = None,
) -> TrainingFacetsOut:
    """The Sessions screen's filter options (training hubs, training types), taken from the
    trainings the caller may see within `filters` - the same authorization as the list, so an
    option never reveals a training outside it."""
    filters = account_ids.with_trainer_ids(db, common_db, filters)
    conditions = dashboard_repository.conference_conditions(filters, include_cancelled=True)
    conditions += dashboard_repository.conference_authorization_conditions(resolve_scope(common_db, admin, tenant_id))
    return TrainingFacetsOut(
        trainingHubs=catalog_repository.list_distinct_conference_values(db, Conference.trainingHub, conditions),
        trainingTypes=catalog_repository.list_distinct_conference_values(db, Conference.trainingType, conditions),
    )


def _stamp(value) -> Optional[str]:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else None


def list_attendance_page(
    db: Session,
    admin: Optional[Admin],
    filters: Optional[ConferenceFilters],
    mode: str,
    search: Optional[str],
    sort: str,
    descending: bool,
    paging: PageRequest,
    common_db: Optional[Session] = None,
    tenant_id: Optional[str] = None,
) -> AttendancePageResponse:
    """One page of the attendance list, restricted to what `admin`'s admin_access grant authorizes
    (or, for an active trainer, to attendance on the trainings assigned to them) - the same scope (access_service.resolve_scope), the same SQL condition
    builder (dashboard_repository.access_scope_conditions) and the same fail-closed convention
    as list_trainings_page (`_list_scope`).

    Same rows and same field values as `list_attendance(org=True)` (compared in
    tests/test_attendance_page.py), but filtering, searching, sorting and paging happen in SQL
    and only the page's rows are enriched: at most 4 statements per request (page, total - first
    page only, post-test results, tallies)."""
    scope = _list_scope(admin, common_db, tenant_id)
    filters = account_ids.with_trainer_ids(db, common_db, filters)
    conditions = dashboard_repository.conference_conditions(filters, include_cancelled=True)
    if scope is not None:
        conditions += dashboard_repository.conference_authorization_conditions(scope)
    try:
        page_result = attendance_repository.list_page(
            db, conditions, mode, search, sort, descending, paging.cursor, paging.limit, paging.page
        )
    except (ValueError, KeyError, TypeError):
        raise bad_request("Invalid page cursor")
    rows = page_result.rows

    tallies = attendance_repository.tallies_for_trainees(db, conditions, {r.trainee_uid for r in rows})
    results = assessment_repository.latest_post_test_results_for_pairs(
        db, {(r.conference_uid, r.trainee_uid) for r in rows}
    )

    items: list[AttendanceListItemOut] = []
    for r in rows:
        result = results.get((r.conference_uid, r.trainee_uid))
        post_test_score = None
        post_test_summary = None
        if result:
            total_marks = float(result.maxScore)
            correct = float(result.totalScore)
            post_test_score = f"{correct:g} / {total_marks:g} ({float(result.percentage):g}%)"
            post_test_summary = f"Total: {total_marks:g}, Correct: {correct:g}, Wrong: {total_marks - correct:g}"

        tally_total, tally_present, tally_pending = tallies.get(r.trainee_uid, (0, 0, 0))
        has_trainee = r.trainee_found is not None
        # The number marked on the attendance row; failing that, the trainee's registered one.
        phone = r.phone or (r.trainee_phone if has_trainee else None)
        items.append(
            AttendanceListItemOut(
                attendanceId=r.attendance_uid or str(r.id),
                region=r.region,
                product=r.training_type,
                session=r.session_type,
                audienceType=r.audience,
                conferenceDate=r.conference_date,
                trainerName=r.trainer_name,
                trainerHoId=r.trainer_employee_id,
                participantHoId=r.trainee_employee_id if has_trainee else None,
                participantName=r.trainee_name if has_trainee else UNKNOWN_TRAINEE_NAME,
                phone=str(phone) if phone is not None else None,
                state=r.state,
                location=", ".join(filter(None, [r.district, r.state])),
                district=r.district,
                reportingManagerOfPromoter=r.supervisor_name if has_trainee else None,
                attendanceStatus=r.status,
                markedAt=_stamp(r.timestamp),
                checkIn=r.marked_on,
                checkOut=_stamp(r.check_out_time),
                postTestScore=post_test_score,
                postTestScoreSummary=post_test_summary,
                sessionTypeMethod=r.session_type,
                conferenceId=r.conference_uid,
                lastUpdates=_stamp(r.timestamp),
                updatedBy=r.updated_by,
                updationOn=_stamp(r.updation_on),
                marked=r.status == "Present",
                trainerTrainingsTotal=tally_total,
                trainerTrainingsPresent=tally_present,
                trainerTrainingsPending=tally_pending,
            )
        )
    return AttendancePageResponse(items=items, **page_result.meta())
