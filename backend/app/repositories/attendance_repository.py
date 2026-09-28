import base64
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import String, and_, case, cast, func, or_, select, tuple_
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import FunctionElement

from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.utils.date_utils import utc_now


def get_for_conference_and_trainee(db: Session, conference_uid: str, trainee_uid: str) -> Optional[Attendance]:
    return (
        db.query(Attendance)
        .filter(Attendance.conferenceUid == conference_uid, Attendance.traineeUid == trainee_uid)
        .first()
    )


def list_for_conference(db: Session, conference_uid: str) -> list[Attendance]:
    return db.query(Attendance).filter(Attendance.conferenceUid == conference_uid).all()


def list_for_conferences(db: Session, conference_uids: list[str]) -> list[Attendance]:
    if not conference_uids:
        return []
    return (
        db.query(Attendance)
        .filter(Attendance.conferenceUid.in_(conference_uids))
        .order_by(Attendance.timestamp.desc())
        .all()
    )


def list_present_pairs(db: Session, conference_uids: list[str]) -> list[tuple[str, str]]:
    """(conferenceUid, traineeUid) pairs for trainees marked Present - used to
    compute real headcounts, as opposed to the planned `batchSize`."""
    if not conference_uids:
        return []
    rows = (
        db.query(Attendance.conferenceUid, Attendance.traineeUid)
        .filter(Attendance.conferenceUid.in_(conference_uids), Attendance.status == "Present")
        .all()
    )
    return [(row.conferenceUid, row.traineeUid) for row in rows]


def list_for_trainee(db: Session, trainee_uid: str) -> list[Attendance]:
    return db.query(Attendance).filter(Attendance.traineeUid == trainee_uid).all()


def count_by_status(db: Session, status: str) -> int:
    """Org-wide count, all conferences - the admin dashboard's Audience card."""
    return db.query(Attendance).filter(Attendance.status == status).count()


def list_attended_trainee_uids(db: Session) -> set[str]:
    """Trainees marked Present in at least one training - the population the
    dashboard ranks (a brand-new trainee who's never attended is excluded)."""
    rows = db.query(Attendance.traineeUid).filter(Attendance.status == "Present").distinct().all()
    return {row.traineeUid for row in rows}


def create(db: Session, attendance: Attendance) -> Attendance:
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def delete(db: Session, attendance: Attendance) -> None:
    db.delete(attendance)
    db.commit()


def delete_for_conference_and_trainee(db: Session, conference_uid: str, trainee_uid: str) -> None:
    db.query(Attendance).filter(
        Attendance.conferenceUid == conference_uid, Attendance.traineeUid == trainee_uid
    ).delete()
    db.commit()


def save(db: Session) -> None:
    db.commit()


# --- attendance_logs (one row per conference+trainee+module, upserted) --------

def upsert_attendance_log(
    db: Session, conference_uid: str, trainee_uid: str, module_id: str, status: str
) -> None:
    """`attendance_logs` has UNIQUE(conferenceUid, traineeUid, moduleId), so
    it's a per-module snapshot, not an append log - update the existing row
    or insert a new one."""
    existing = (
        db.query(AttendanceLog)
        .filter(
            AttendanceLog.conferenceUid == conference_uid,
            AttendanceLog.traineeUid == trainee_uid,
            AttendanceLog.moduleId == module_id,
        )
        .first()
    )
    if existing:
        existing.status = status
        existing.markedAt = utc_now()
    else:
        db.add(
            AttendanceLog(
                conferenceUid=conference_uid,
                traineeUid=trainee_uid,
                moduleId=module_id,
                markedAt=utc_now(),
                status=status,
            )
        )


# ---------------------------------------------------------------------------
# Paged admin attendance list
# ---------------------------------------------------------------------------

MAX_PAGE_SIZE = 200
EPOCH = datetime(1970, 1, 1)


def _text(column):
    return func.coalesce(cast(column, String), "")


# Text shown as the participant's phone: the attendance row's own phone when it has
# one (a 0 / NULL phone counts as none), otherwise the trainee's - exactly the
# fallback the Python list uses.
_PHONE = case(
    (and_(Attendance.phone.is_not(None), Attendance.phone != 0), cast(Attendance.phone, String)),
    else_=cast(Trainee.phone, String),
)
class _IdAsText(FunctionElement):
    """A number as text, safe to mix with the tables' text columns.

    MySQL refuses to compare / LIKE-match "a text column, or else CAST(id AS CHAR)":
    the cast has a different collation from the column ("Illegal mix of
    collations"). A number turned into text by CONCAT('', id) has no collation of
    its own, so it takes the column's - which is what makes the attendance-ID
    fallback searchable and pageable. Other databases (SQLite in the tests) use a
    plain CAST."""

    type = String()
    inherit_cache = True


@compiles(_IdAsText)
def _id_as_text_default(element, compiler, **kw):
    return "CAST(%s AS VARCHAR)" % compiler.process(element.clauses, **kw)


@compiles(_IdAsText, "mysql")
def _id_as_text_mysql(element, compiler, **kw):
    return "CONCAT('', %s)" % compiler.process(element.clauses, **kw)


# The attendance ID shown in the list: the row's own ID, else its numeric row id.
_ATTENDANCE_ID = func.coalesce(Attendance.attendanceUid, _IdAsText(Attendance.id))

# sort key -> (SQL expression, "text" | "datetime"). NULLs are replaced (text -> "",
# datetime -> the epoch) so keyset comparisons never meet a NULL.
SORT_COLUMNS = {
    "markedAt": (Attendance.timestamp, "datetime"),  # the default, and the old list's order
    "conferenceDate": (_text(Conference.conferenceDate), "text"),
    "region": (_text(Conference.region), "text"),
    "product": (_text(Conference.trainingType), "text"),
    "session": (_text(Conference.sessionType), "text"),
    "audienceType": (_text(Conference.audience), "text"),
    "trainerName": (_text(Conference.trainerName), "text"),
    "trainerHoId": (_text(Conference.trainerEmployeeId), "text"),
    "participantHoId": (_text(Trainee.employee_id), "text"),
    "participantName": (func.coalesce(Trainee.name, "Unknown Trainee"), "text"),
    "phone": (func.coalesce(_PHONE, ""), "text"),
    "state": (_text(Conference.state), "text"),
    "district": (_text(Conference.district), "text"),
    "reportingManagerOfPromoter": (_text(Trainee.supervisorName), "text"),
    "attendanceStatus": (_text(Attendance.status), "text"),
    "checkIn": (_text(Attendance.markedOn), "text"),
    "checkOut": (func.coalesce(Attendance.checkOutTime, EPOCH), "datetime"),
    "attendanceId": (_ATTENDANCE_ID, "text"),
    "conferenceId": (_text(Attendance.conferenceUid), "text"),
}

# Text a free-text search looks in (contains, case-insensitive).
SEARCH_EXPRESSIONS = (
    _text(Trainee.name),
    _text(Trainee.employee_id),
    func.coalesce(_PHONE, ""),
    _text(Conference.trainerName),
    _text(Conference.trainerEmployeeId),
    _text(Conference.region),
    _text(Conference.trainingType),
    _text(Conference.sessionType),
    _text(Conference.audience),
    _text(Conference.state),
    _text(Conference.district),
    _text(Attendance.conferenceUid),
    _ATTENDANCE_ID,
    _text(Attendance.status),
    _text(Conference.conferenceDate),
)

_PAGE_COLUMNS = (
    Attendance.id.label("id"),
    Attendance.attendanceUid.label("attendance_uid"),
    Attendance.conferenceUid.label("conference_uid"),
    Attendance.traineeUid.label("trainee_uid"),
    Attendance.phone.label("phone"),
    Attendance.markedOn.label("marked_on"),
    Attendance.timestamp.label("timestamp"),
    Attendance.checkOutTime.label("check_out_time"),
    Attendance.updatedBy.label("updated_by"),
    Attendance.updationOn.label("updation_on"),
    Attendance.status.label("status"),
    Conference.region.label("region"),
    Conference.trainingType.label("training_type"),
    Conference.sessionType.label("session_type"),
    Conference.audience.label("audience"),
    Conference.conferenceDate.label("conference_date"),
    Conference.trainerName.label("trainer_name"),
    Conference.trainerEmployeeId.label("trainer_employee_id"),
    Conference.state.label("state"),
    Conference.district.label("district"),
    Trainee.traineeUid.label("trainee_found"),
    Trainee.name.label("trainee_name"),
    Trainee.employee_id.label("trainee_employee_id"),
    Trainee.phone.label("trainee_phone"),
    Trainee.supervisorName.label("supervisor_name"),
)


def _decode_cursor(sort: str, cursor: str):
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    if data["s"] != sort:
        raise ValueError("cursor was issued for a different sort")
    value = data["v"]
    if SORT_COLUMNS[sort][1] == "datetime":
        value = datetime.fromisoformat(value)
    elif not isinstance(value, str):
        raise ValueError("bad cursor value")
    return value, int(data["id"])


def list_page(
    db: Session,
    conditions: list,
    mode: str = "all",
    search: Optional[str] = None,
    sort: str = "markedAt",
    descending: bool = True,
    cursor: Optional[str] = None,
    limit: int = 10,
    page: Optional[int] = None,
):
    """One page of the admin attendance list: attendance JOIN conference (the
    admin's scope, `conditions`) LEFT JOIN trainee, filtered by `mode`, searched,
    sorted and limited in SQL. Returns (rows, next_cursor, total).

    Paging: `cursor` = "the rows after this one" (keyset - stable while rows are
    added, used to walk everything for export) or `page` = a 1-based page number
    (OFFSET - can drift if rows are added between page requests). Order is (sort
    expression, attendance.id) so ties are never ambiguous. `total` is computed only
    for the first page. Only the columns the list shows are selected (no ORM
    entities, no relationship loading)."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    sort = sort if sort in SORT_COLUMNS else "markedAt"
    sort_expr, kind = SORT_COLUMNS[sort]

    base = (
        select(*_PAGE_COLUMNS, sort_expr.label("sort_value"))
        .select_from(Attendance)
        .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
        .outerjoin(Trainee, Trainee.traineeUid == Attendance.traineeUid)
        .where(*conditions)
    )
    if mode == "confirmed":
        base = base.where(Attendance.status == "Present")
    elif mode == "pending":
        base = base.where(or_(Attendance.status.is_(None), Attendance.status != "Present"))

    text = (search or "").strip().lower()
    if text:
        base = base.where(or_(*[func.lower(expr).contains(text, autoescape=True) for expr in SEARCH_EXPRESSIONS]))

    total = None
    if cursor is None and page in (None, 1):
        total = int(db.execute(select(func.count()).select_from(base.with_only_columns(Attendance.id).subquery())).scalar() or 0)

    query = base
    if cursor:
        value, last_id = _decode_cursor(sort, cursor)
        after = tuple_(sort_expr, Attendance.id)
        query = query.where(after < tuple_(value, last_id) if descending else after > tuple_(value, last_id))

    order = (sort_expr.desc(), Attendance.id.desc()) if descending else (sort_expr.asc(), Attendance.id.asc())
    query = query.order_by(*order)
    if page and page > 1 and not cursor:
        query = query.offset((page - 1) * limit)
    rows = db.execute(query.limit(limit + 1)).all()

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        value = last.sort_value
        if isinstance(value, datetime):
            value = value.isoformat()
        next_cursor = base64.urlsafe_b64encode(
            json.dumps({"s": sort, "v": value if value is not None else "", "id": last.id}).encode()
        ).decode()
    return rows, next_cursor, total


def tallies_for_trainees(db: Session, conditions: list, trainee_uids: set[str]) -> dict[str, tuple[int, int, int]]:
    """{traineeUid: (total, present, pending)} across EVERY in-scope training's
    attendance rows (not just the page, and not narrowed by mode or search) -
    the same numbers the Python list computes with Counters. "Pending" here means
    status Pending or Joined (unrelated to the Pending screen's "not Present")."""
    if not trainee_uids:
        return {}
    rows = db.execute(
        select(
            Attendance.traineeUid,
            func.count(),
            func.coalesce(func.sum(case((Attendance.status == "Present", 1), else_=0)), 0),
            func.coalesce(func.sum(case((Attendance.status.in_(("Pending", "Joined")), 1), else_=0)), 0),
        )
        .select_from(Attendance)
        .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
        .where(*conditions, Attendance.traineeUid.in_(trainee_uids))
        .group_by(Attendance.traineeUid)
    ).all()
    return {uid: (int(total), int(present), int(pending)) for uid, total, present, pending in rows}
