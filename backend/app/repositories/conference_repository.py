from typing import Optional

from sqlalchemy import and_, case, false, func, or_
from sqlalchemy.orm import Session

from app.models.conference import Conference
from app.repositories import keyset


def get_by_uid(db: Session, conference_uid: str) -> Optional[Conference]:
    return db.query(Conference).filter(Conference.conferenceUid == conference_uid).first()


def trainer_condition(trainer_employee_id: Optional[str]):
    """SQL condition for "this conference is assigned to this trainer" - the one trainer-ownership
    rule every trainer query below uses. A blank/None username matches nothing (never
    `trainerEmployeeId IS NULL`), so an unresolved identity can't claim unassigned trainings."""
    if not (trainer_employee_id or "").strip():
        return false()
    return Conference.trainerEmployeeId == trainer_employee_id


def get_authorized(db: Session, conference_uid: str, authorization_conditions: list) -> Optional[Conference]:
    """One conference, only if it also satisfies the caller's authorization conditions (see
    dashboard_repository.conference_authorization_conditions) - checked in the query itself, so
    an out-of-scope row is never loaded."""
    return db.query(Conference).filter(Conference.conferenceUid == conference_uid, *authorization_conditions).first()


def get_authorized_by_file(db: Session, file_path: str, authorization_conditions: list) -> Optional[Conference]:
    """The conference whose trainer check-in photo, check-out photo or attendance sheet is
    `file_path`, only if it also satisfies the caller's authorization conditions."""
    return (
        db.query(Conference)
        .filter(
            or_(
                Conference.startConferenceImage == file_path,
                Conference.conferenceImage == file_path,
                Conference.attendanceSheet == file_path,
            ),
            *authorization_conditions,
        )
        .first()
    )


def approval_conditions(approval: Optional[str]) -> list:
    """The approval split the Training lists use: "pending" = awaiting review, "reviewed" =
    anything else (approved or rejected - the admin's list), "approved" = approved only (the
    trainer's own Training List). None = no split."""
    approval_status = func.lower(Conference.status)
    if approval == "pending":
        return [approval_status == "pending"]
    if approval == "reviewed":
        return [or_(Conference.status.is_(None), approval_status != "pending")]
    if approval == "approved":
        return [approval_status == "approved"]
    return []


def list_filtered(db: Session, conditions: list, approval: Optional[str] = None) -> list[Conference]:
    """Org-wide list for the admin Training / Pending lists, filtered in the
    database (newest first) instead of loading every row and filtering in
    Python. `approval`: "pending" = awaiting review, "reviewed" = anything else
    (approved or rejected)."""
    query = db.query(Conference).filter(*conditions, *approval_conditions(approval))
    return query.order_by(Conference.timestamp.desc()).all()


def list_all_for_trainer(db: Session, trainer_employee_id: str) -> list[Conference]:
    return (
        db.query(Conference)
        .filter(trainer_condition(trainer_employee_id))
        .order_by(Conference.timestamp.desc())
        .all()
    )


def list_for_trainer(
    db: Session,
    trainer_employee_id: str,
    *,
    exact_date: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> list[Conference]:
    query = db.query(Conference).filter(trainer_condition(trainer_employee_id))
    if exact_date is not None:
        query = query.filter(Conference.conferenceDate == exact_date)
    else:
        if start:
            query = query.filter(Conference.conferenceDate >= start)
        if end:
            query = query.filter(Conference.conferenceDate <= end)
    return query.order_by(Conference.timestamp.desc()).all()


def list_all(db: Session) -> list[Conference]:
    """Every conference org-wide, all trainers - the admin dashboard's
    overview cards (unlike everything else here, which is scoped to one
    trainer)."""
    return db.query(Conference).all()


def list_recent_completed_for_trainer(db: Session, trainer_employee_id: str, limit: int) -> list[Conference]:
    return (
        db.query(Conference)
        .filter(trainer_condition(trainer_employee_id), Conference.conferenceStatus == "Completed")
        .order_by(Conference.timestamp.desc())
        .limit(limit)
        .all()
    )


def list_by_uids(db: Session, conference_uids: set[str], limit: Optional[int] = None) -> list[Conference]:
    if not conference_uids:
        return []
    query = db.query(Conference).filter(Conference.conferenceUid.in_(conference_uids)).order_by(
        Conference.timestamp.desc()
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def create(db: Session, conference: Conference) -> Conference:
    db.add(conference)
    db.commit()
    db.refresh(conference)
    return conference


def save(db: Session, conference: Conference) -> Conference:
    db.commit()
    db.refresh(conference)
    return conference


# What the user sees in the UI:
# - If approval status is 'Rejected' -> 'Rejected'
# - If approval status is NOT 'Approved' (e.g. 'Pending') -> 'Pending'
# - If approved and conferenceStatus is 'Ongoing' -> 'Started'
# - Otherwise -> conferenceStatus ('Scheduled', 'Completed', 'Cancelled')
EFFECTIVE_STATUS = case(
    (func.lower(func.coalesce(Conference.status, "")) == "rejected", "rejected"),
    (func.lower(func.coalesce(Conference.status, "")) != "approved", "pending"),
    (func.lower(func.coalesce(Conference.conferenceStatus, "")) == "ongoing", "started"),
    else_=func.lower(func.coalesce(Conference.conferenceStatus, "")),
)

# For searching: also match "ongoing" when the session is Ongoing/Started
EFFECTIVE_STATUS_ONGOING = case(
    (
        and_(
            func.lower(func.coalesce(Conference.status, "")) == "approved",
            func.lower(func.coalesce(Conference.conferenceStatus, "")) == "ongoing",
        ),
        "ongoing",
    ),
    else_="",
)

# Columns the admin list can be sorted by (client column key -> model column or expression).
SORT_COLUMNS = {
    "timestamp": Conference.timestamp,
    "conferenceDate": Conference.conferenceDate,
    "conferenceTime": Conference.conferenceTime,
    "conferenceUid": Conference.conferenceUid,
    "trainerName": Conference.trainerName,
    "zone": Conference.zone,
    "sessionType": Conference.sessionType,
    "trainingType": Conference.trainingType,
    "trainingHub": Conference.trainingHub,
    "state": Conference.state,
    "district": Conference.district,
    "conferenceStatus": EFFECTIVE_STATUS,
}

# Text columns / expressions a free-text search looks in.
SEARCH_COLUMNS = (
    Conference.conferenceUid,
    Conference.trainerName,
    Conference.trainerEmployeeId,
    Conference.zone,
    Conference.region,
    Conference.sessionType,
    Conference.trainingType,
    Conference.trainingHub,
    Conference.state,
    Conference.district,
    Conference.conferenceDate,
    Conference.conferenceTime,
    Conference.suiteTitle,
    EFFECTIVE_STATUS,
    EFFECTIVE_STATUS_ONGOING,
)

MAX_PAGE_SIZE = keyset.MAX_PAGE_SIZE


def _sort_expression(sort: str):
    column = SORT_COLUMNS.get(sort, Conference.timestamp)
    # Text columns sort with NULL as "" so keyset comparisons never see NULL;
    # `timestamp` is NOT NULL and compared as-is.
    return column if column is Conference.timestamp else func.coalesce(column, "")


def _cursor_value(sort: str, row: Conference):
    """The row's value for `sort`, as stored in the next-page cursor."""
    if sort == "conferenceStatus":
        status = (row.status or "").lower()
        conf_status = (row.conferenceStatus or "").lower()
        if status == "rejected":
            return "rejected"
        if status != "approved":
            return "pending"
        if conf_status == "ongoing":
            return "started"
        return conf_status
    return getattr(row, SORT_COLUMNS.get(sort, Conference.timestamp).key)


def list_page(
    db: Session,
    conditions: list,
    approval: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "timestamp",
    descending: bool = True,
    cursor: Optional[str] = None,
    limit: int = 50,
    page: Optional[int] = None,
) -> tuple[list[Conference], Optional[str], Optional[int]]:
    """One page of the Training List: `conditions` (the caller's authorization AND its filters),
    the approval split and the search are all in the WHERE before anything is counted, sorted or
    paged - see keyset.paginate for the paging itself. Returns (rows, next_cursor, total)."""
    query = db.query(Conference).filter(
        *conditions, *approval_conditions(approval), *keyset.search_conditions(SEARCH_COLUMNS, search)
    )
    return keyset.paginate(
        query,
        _sort_expression(sort),
        Conference.id,
        descending=descending,
        cursor=cursor,
        limit=limit,
        page=page,
        cursor_value=lambda row: _cursor_value(sort, row),
        datetime_sort=SORT_COLUMNS.get(sort, Conference.timestamp) is Conference.timestamp,
    )
