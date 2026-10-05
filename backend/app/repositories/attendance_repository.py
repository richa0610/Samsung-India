from datetime import datetime
from typing import Optional

from sqlalchemy import String, and_, case, cast, func, or_, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import FunctionElement

from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import keyset
from app.utils.date_utils import utc_now


def get_for_conference_and_trainee(
    db: Session, conference_uid: str, trainee_uid: str, *, lock: bool = False
) -> Optional[Attendance]:
    """`lock=True` holds the row (SELECT ... FOR UPDATE) until the transaction ends."""
    query = db.query(Attendance).filter(Attendance.conferenceUid == conference_uid, Attendance.traineeUid == trainee_uid)
    if lock:
        query = query.with_for_update()
    return query.first()


def get_by_check_in_photo(db: Session, file_path: str) -> Optional[Attendance]:
    """The attendance row whose check-in photo is `file_path` (it records whose photo it is and
    for which conference)."""
    return db.query(Attendance).filter(Attendance.checkInPhoto == file_path).first()


def list_for_conference(db: Session, conference_uid: str) -> list[Attendance]:
    return db.query(Attendance).filter(Attendance.conferenceUid == conference_uid).all()


def list_for_trainee(db: Session, trainee_uid: str) -> list[Attendance]:
    return db.query(Attendance).filter(Attendance.traineeUid == trainee_uid).all()


def create(db: Session, attendance: Attendance) -> Attendance:
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def delete(db: Session, attendance: Attendance) -> None:
    db.delete(attendance)
    db.commit()


def delete_for_conference_and_trainee(db: Session, conference_uid: str, trainee_uid: str) -> int:
    """Deletes the trainee's attendance for this conference; returns how many rows went."""
    deleted = db.query(Attendance).filter(
        Attendance.conferenceUid == conference_uid, Attendance.traineeUid == trainee_uid
    ).delete()
    db.commit()
    return deleted


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


# Sorts that read trainee columns - with these (or any search, which looks in the trainee's name
# and employee id too) the trainee join is part of which rows match and in what order.
_TRAINEE_SORTS = frozenset({"participantHoId", "participantName", "phone", "reportingManagerOfPromoter"})


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
) -> keyset.Page:
    """One page of the attendance list: attendance JOIN conference (the caller's authorization,
    `conditions`) LEFT JOIN trainee, filtered by `mode`, searched, then counted, sorted and paged
    in SQL (keyset.paginate). Both joins are on unique keys (conference.conferenceUid,
    trainee.traineeUid), so a row can never appear twice. Only the columns the list shows are
    selected (no ORM entities, no relationship loading).

    Without a search or a trainee-column sort, the trainee join can't change which rows match or
    their order, so it is deferred: the count and the sort/limit run on attendance JOIN conference
    alone, and the trainee (and display) columns are joined onto the page's rows only, in the same
    statement (keyset.paginate `enrich`). Measured on the 100k-attendance perf dataset, a trainer's
    first page: 140 -> ~30 ms for the page, 54 -> ~20 ms for the count (perf/results)."""
    sort = sort if sort in SORT_COLUMNS else "markedAt"
    sort_expr, kind = SORT_COLUMNS[sort]
    deferred = not (search or "").strip() and sort not in _TRAINEE_SORTS

    if deferred:
        stmt = (
            select(Attendance.id.label("id"), sort_expr.label("sort_value"))
            .select_from(Attendance)
            .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
            .where(*conditions)
        )
    else:
        stmt = (
            select(*_PAGE_COLUMNS, sort_expr.label("sort_value"))
            .select_from(Attendance)
            .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
            .outerjoin(Trainee, Trainee.traineeUid == Attendance.traineeUid)
            .where(*conditions)
        )
    if mode == "confirmed":
        stmt = stmt.where(Attendance.status == "Present")
    elif mode == "pending":
        stmt = stmt.where(or_(Attendance.status.is_(None), Attendance.status != "Present"))
    stmt = stmt.where(*keyset.search_conditions(SEARCH_EXPRESSIONS, search))

    order = keyset.SortOrder.keyset(
        sort,
        sort_expr,
        Attendance.id,
        descending=descending,
        cursor_value=lambda row: row.sort_value,
        datetime_value=kind == "datetime",
    )
    enrich = None
    if deferred:
        def enrich(page_rows):
            return (
                select(*_PAGE_COLUMNS, page_rows.c.sort_value)
                .select_from(page_rows)
                .join(Attendance, Attendance.id == page_rows.c.id)
                .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
                .outerjoin(Trainee, Trainee.traineeUid == Attendance.traineeUid)
            )
    return keyset.paginate(db, stmt, order, cursor=cursor, limit=limit, page=page, entities=False, enrich=enrich)


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
