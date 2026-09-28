import base64
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, tuple_
from sqlalchemy.orm import Session

from app.models.conference import Conference


def get_by_uid(db: Session, conference_uid: str) -> Optional[Conference]:
    return db.query(Conference).filter(Conference.conferenceUid == conference_uid).first()


def get_owned_by_trainer(db: Session, trainer_employee_id: str, conference_uid: str) -> Optional[Conference]:
    return (
        db.query(Conference)
        .filter(
            Conference.conferenceUid == conference_uid,
            Conference.trainerEmployeeId == trainer_employee_id,
        )
        .first()
    )


def list_filtered(db: Session, conditions: list, approval: Optional[str] = None) -> list[Conference]:
    """Org-wide list for the admin Training / Pending lists, filtered in the
    database (newest first) instead of loading every row and filtering in
    Python. `approval`: "pending" = awaiting review, "reviewed" = anything else
    (approved or rejected)."""
    query = db.query(Conference).filter(*conditions)
    approval_status = func.lower(Conference.status)
    if approval == "pending":
        query = query.filter(approval_status == "pending")
    elif approval == "reviewed":
        query = query.filter(or_(Conference.status.is_(None), approval_status != "pending"))
    return query.order_by(Conference.timestamp.desc()).all()


def list_all_for_trainer(db: Session, trainer_employee_id: str) -> list[Conference]:
    return (
        db.query(Conference)
        .filter(Conference.trainerEmployeeId == trainer_employee_id)
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
    query = db.query(Conference).filter(Conference.trainerEmployeeId == trainer_employee_id)
    if exact_date is not None:
        query = query.filter(Conference.conferenceDate == exact_date)
    else:
        if start:
            query = query.filter(Conference.conferenceDate >= start)
        if end:
            query = query.filter(Conference.conferenceDate <= end)
    return query.order_by(Conference.timestamp.desc()).all()


def list_pending(db: Session) -> list[Conference]:
    return db.query(Conference).filter(Conference.status == "Pending").order_by(Conference.timestamp.desc()).all()


def list_all(db: Session) -> list[Conference]:
    """Every conference org-wide, all trainers - the admin dashboard's
    overview cards (unlike everything else here, which is scoped to one
    trainer)."""
    return db.query(Conference).all()


def list_recent_completed_for_trainer(db: Session, trainer_employee_id: str, limit: int) -> list[Conference]:
    return (
        db.query(Conference)
        .filter(Conference.trainerEmployeeId == trainer_employee_id, Conference.conferenceStatus == "Completed")
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


# Columns the admin list can be sorted by (client column key -> model column).
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
    "conferenceStatus": Conference.conferenceStatus,
}

# Text columns a free-text search looks in.
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
    Conference.conferenceStatus,
    Conference.status,
    Conference.suiteTitle,
)

MAX_PAGE_SIZE = 200


def _sort_expression(sort: str):
    column = SORT_COLUMNS.get(sort, Conference.timestamp)
    # Text columns sort with NULL as "" so keyset comparisons never see NULL;
    # `timestamp` is NOT NULL and compared as-is.
    return column if column is Conference.timestamp else func.coalesce(column, "")


def _encode_cursor(sort: str, row: Conference) -> str:
    value = getattr(row, SORT_COLUMNS.get(sort, Conference.timestamp).key)
    if isinstance(value, datetime):
        value = value.isoformat()
    return base64.urlsafe_b64encode(json.dumps({"v": value if value is not None else "", "id": row.id}).encode()).decode()


def _decode_cursor(sort: str, cursor: str):
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    value = data["v"]
    if SORT_COLUMNS.get(sort, Conference.timestamp) is Conference.timestamp and isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value, int(data["id"])


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
    """One page of the org-wide list, using keyset ("rows after this one")
    paging so a page stays correct - no skipped or repeated rows - even while
    trainings are being added, and each page costs the same however deep it is
    (an OFFSET would re-read every earlier row). Ordering is (sort column, id),
    the id breaking ties. Returns (rows, next_cursor, total); `total` is only
    computed for the first page (no cursor, and page 1 when a page number is
    used) since it doesn't change as you move through the pages.

    Two ways to move: `cursor` ("the rows after this one" - what "load more" and
    export use) or `page` (1-based, jump straight to a numbered page - what the
    table's page buttons use; an OFFSET, fine at these sizes)."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    query = db.query(Conference).filter(*conditions)

    approval_status = func.lower(Conference.status)
    if approval == "pending":
        query = query.filter(approval_status == "pending")
    elif approval == "reviewed":
        query = query.filter(or_(Conference.status.is_(None), approval_status != "pending"))

    text = (search or "").strip().lower()
    if text:
        query = query.filter(
            or_(*[func.lower(func.coalesce(column, "")).contains(text, autoescape=True) for column in SEARCH_COLUMNS])
        )

    total = query.count() if cursor is None and page in (None, 1) else None

    sort_expr = _sort_expression(sort)
    if cursor:
        value, last_id = _decode_cursor(sort, cursor)
        after = tuple_(sort_expr, Conference.id)
        query = query.filter(after < tuple_(value, last_id) if descending else after > tuple_(value, last_id))

    order = (sort_expr.desc(), Conference.id.desc()) if descending else (sort_expr.asc(), Conference.id.asc())
    query = query.order_by(*order)
    if page and page > 1 and not cursor:
        query = query.offset((page - 1) * limit)
    rows = query.limit(limit + 1).all()

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = _encode_cursor(sort, rows[-1])
    return rows, next_cursor, total
