from typing import Optional

from sqlalchemy import Integer, and_, case, cast, false, func, or_, select
from sqlalchemy.orm import Session

from app.models.conference import Conference
from app.repositories import keyset


def get_by_uid(db: Session, conference_uid: str) -> Optional[Conference]:
    return db.query(Conference).filter(Conference.conferenceUid == conference_uid).first()


def claim_active_module(db: Session, conference_uid: str, expected: Optional[str], new: Optional[str]) -> bool:
    """Atomically moves the session's active module from `expected` to `new` - True only for the
    one request whose UPDATE matched. Two concurrent starts/advances can both have read the same
    activeModuleId; only one may act on it (the other matches 0 rows and backs off), so the
    Execution Flow never logs a module as started twice. The UPDATE row-locks until commit."""
    current = Conference.activeModuleId.is_(None) if expected is None else Conference.activeModuleId == expected
    matched = (
        db.query(Conference)
        .filter(Conference.conferenceUid == conference_uid, current)
        .update({"activeModuleId": new}, synchronize_session=False)
    )
    return bool(matched)


def claim_end(db: Session, conference_uid: str, ends_on: str) -> bool:
    """Atomically marks the session ended - True only for the one request that did it."""
    matched = (
        db.query(Conference)
        .filter(Conference.conferenceUid == conference_uid, Conference.conferenceEndsOn.is_(None))
        .update({"conferenceEndsOn": ends_on}, synchronize_session=False)
    )
    return bool(matched)


def lock_for_roster_change(db: Session, conference_uid: str) -> Optional[Conference]:
    """The conference, with its row held (SELECT ... FOR UPDATE) until the transaction ends. Every
    path that may create a trainee's attendance row for this session (check-in, QR join) takes it
    first, so two concurrent requests can't both see "no row yet" and create two."""
    return db.query(Conference).filter(Conference.conferenceUid == conference_uid).with_for_update().first()


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

# --- the trainer Sessions screen ---------------------------------------------------------------

_CONFERENCE_STATUS = func.lower(func.coalesce(Conference.conferenceStatus, ""))


def session_conditions(
    on_date: Optional[str],
    status: Optional[str],
    location: Optional[str],
    today: Optional[str] = None,
) -> list:
    """The Sessions screen's own narrowing: its "Today" tab (`on_date`, the device's date), its
    "Completed" tab or card filter (`status="completed" | "ongoing" | "planned" | "missed"`) and
    its location filter - a training's hub, or its state when it has no hub."""
    conditions = []
    if on_date:
        conditions.append(Conference.conferenceDate == on_date)
    if status:
        norm_status = status.lower()
        approval_status = func.lower(func.coalesce(Conference.status, ""))
        if norm_status in ("total", "all"):
            conditions.append(_CONFERENCE_STATUS != "cancelled")
        elif norm_status == "completed":
            conditions.append(_CONFERENCE_STATUS == "completed")
        elif norm_status in ("ongoing", "live"):
            conditions.append(_CONFERENCE_STATUS.in_(("ongoing", "live")))
        elif norm_status in ("planned", "pending"):
            conds = [
                approval_status == "approved",
                _CONFERENCE_STATUS.notin_(("ongoing", "live", "completed", "cancelled")),
            ]
            if today:
                conds.append(or_(Conference.conferenceDate >= today, func.coalesce(Conference.conferenceDate, "") == ""))
            conditions.append(and_(*conds))
        elif norm_status == "missed":
            conds = [
                approval_status == "approved",
                _CONFERENCE_STATUS.notin_(("ongoing", "live", "completed", "cancelled")),
            ]
            if today:
                conds.append(and_(Conference.conferenceDate < today, func.coalesce(Conference.conferenceDate, "") != ""))
            conditions.append(and_(*conds))
    if location:
        shown_location = func.coalesce(func.nullif(Conference.trainingHub, ""), Conference.state)
        conditions.append(shown_location == location)
    return conditions


def _minutes_of_day(time_column):
    """"hh:mm AM" / "hh:mm PM" -> minutes after midnight; anything without a colon -> 0
    (midnight), the same fallback the app used. Portable SQL (MySQL and SQLite)."""
    time = func.coalesce(time_column, "")
    colon = func.instr(time, ":")
    hours = cast(func.substr(time, 1, colon - 1), Integer) % 12
    pm = case((func.upper(func.substr(time, -2)) == "PM", 12), else_=0)
    minutes = cast(func.substr(time, colon + 1, 2), Integer)
    return case((colon > 1, (hours + pm) * 60 + minutes), else_=0)


# Live sessions first, then upcoming ones soonest first, then completed ones most recent first;
# inside each group a session without a date goes last. The order the Sessions screen used to
# sort into on the phone - now in SQL, so it can be paged.
_SESSION_GROUP = case((_CONFERENCE_STATUS == "ongoing", 0), (_CONFERENCE_STATUS == "completed", 2), else_=1)
_UNDATED = case((func.coalesce(Conference.conferenceDate, "") == "", 1), else_=0)
_SESSION_MINUTES = _minutes_of_day(Conference.conferenceTime)
SESSION_ORDER = (
    _SESSION_GROUP.asc(),
    _UNDATED.asc(),
    case((_SESSION_GROUP < 2, Conference.conferenceDate)).asc(),
    case((_SESSION_GROUP < 2, _SESSION_MINUTES)).asc(),
    case((_SESSION_GROUP == 2, Conference.conferenceDate)).desc(),
    case((_SESSION_GROUP == 2, _SESSION_MINUTES)).desc(),
)


# --- paging ----------------------------------------------------------------------------------


def _sort_order(sort: str, descending: bool) -> keyset.SortOrder:
    if sort == "session":
        return keyset.SortOrder.fixed("session", SESSION_ORDER, Conference.id)
    column = SORT_COLUMNS.get(sort, Conference.timestamp)
    # Text columns sort with NULL as "" so keyset comparisons never see NULL;
    # `timestamp` is NOT NULL and compared as-is.
    expression = column if column is Conference.timestamp else func.coalesce(column, "")
    return keyset.SortOrder.keyset(
        sort if sort in SORT_COLUMNS else "timestamp",
        expression,
        Conference.id,
        descending=descending,
        cursor_value=lambda row: _cursor_value(sort, row),
        datetime_value=column is Conference.timestamp,
    )


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
) -> keyset.Page:
    """One page of the Training List / Sessions: `conditions` (the caller's authorization AND its
    filters), the approval split and the search are all in the WHERE before anything is counted,
    sorted or paged - see keyset.paginate for the paging itself."""
    stmt = select(Conference).where(
        *conditions, *approval_conditions(approval), *keyset.search_conditions(SEARCH_COLUMNS, search)
    )
    return keyset.paginate(db, stmt, _sort_order(sort, descending), cursor=cursor, limit=limit, page=page)
