from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import String, cast, exists, false, func, or_, select, union
from sqlalchemy.orm import Session, aliased

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import conference_repository, keyset


def get_by_phone(db: Session, phone: int) -> Trainee | None:
    return db.query(Trainee).filter(Trainee.phone == phone).first()


def get_by_uid(db: Session, trainee_uid: str) -> Trainee | None:
    return db.query(Trainee).filter(Trainee.traineeUid == trainee_uid).first()


def get_authorized_by_uid(db: Session, trainee_uid: str, authorization_conditions: list) -> Trainee | None:
    """The trainee `trainee_uid`, only if the caller's authorization conditions also allow them."""
    return db.query(Trainee).filter(Trainee.traineeUid == trainee_uid, *authorization_conditions).first()


def get_authorized_by_photo(db: Session, file_path: str, authorization_conditions: list) -> Trainee | None:
    """The trainee whose profile photo is `file_path`, only if the caller's authorization
    conditions (dashboard_repository.trainee_authorization_conditions) also allow them."""
    return db.query(Trainee).filter(Trainee.profilePhoto == file_path, *authorization_conditions).first()


def get_by_phone_or_email(db: Session, phone: int, email: str | None) -> Trainee | None:
    return db.query(Trainee).filter((Trainee.phone == phone) | (Trainee.email == email)).first()


def get_update_conflict(db: Session, trainee_id: int, phone, email) -> Trainee | None:
    return (
        db.query(Trainee)
        .filter(Trainee.id != trainee_id, (Trainee.phone == phone) | (Trainee.email == email))
        .first()
    )


def get_admin_registration_conflict(
    db: Session, phone: int, email: str | None, username: str | None, trainee_uid: str
) -> Trainee | None:
    return (
        db.query(Trainee)
        .filter(
            (Trainee.phone == phone)
            | (Trainee.email == email)
            | (Trainee.username == username)
            | (Trainee.traineeUid == trainee_uid)
        )
        .first()
    )


def get_by_uids(db: Session, trainee_uids: set[str]) -> list[Trainee]:
    if not trainee_uids:
        return []
    return db.query(Trainee).filter(Trainee.traineeUid.in_(trainee_uids)).all()


# Trainee List sort keys (the table's column keys) -> column. Nullable text sorts as "" so keyset
# comparisons never see NULL; `timestamp` is NOT NULL.
PAGE_SORT_COLUMNS = {
    "timestamp": Trainee.timestamp,
    "traineeUid": Trainee.traineeUid,
    "name": Trainee.name,
    "trainerName": Trainee.trainerName,
    "supervisorName": Trainee.supervisorName,
    "district": Trainee.district,
    "updatedBy": Trainee.updatedBy,
    "status": Trainee.status,
}

PAGE_SEARCH_COLUMNS = (
    Trainee.traineeUid,
    Trainee.name,
    Trainee.email,
    cast(Trainee.phone, String),
    Trainee.employee_id,
    Trainee.username,
    Trainee.trainerName,
    Trainee.supervisorName,
    Trainee.designation,
    Trainee.state,
    Trainee.district,
    Trainee.zone,
    Trainee.region,
    Trainee.company,
    Trainee.status,
    Trainee.updatedBy,
)


def registered_between(start: Optional[date], end: Optional[date]) -> list:
    """WHERE conditions for trainees registered from `start` through `end` (whole days, as the
    list shows each one's `timestamp`). A plain range on the column, so its index still applies."""
    conditions = []
    if start:
        conditions.append(Trainee.timestamp >= datetime.combine(start, time.min))
    if end:
        conditions.append(Trainee.timestamp < datetime.combine(end + timedelta(days=1), time.min))
    return conditions


def list_page(
    db: Session,
    conditions: list,
    mode: str = "all",
    search: Optional[str] = None,
    sort: str = "timestamp",
    descending: bool = True,
    cursor: Optional[str] = None,
    limit: int = 10,
    page: Optional[int] = None,
) -> keyset.Page:
    """One page of the Trainee List: `conditions` (the caller's authorization), the Pending split
    (`mode="pending"` = approval status Pending, the same test the screen used client-side) and
    the search are all in the WHERE before counting, sorting and paging (keyset.paginate)."""
    sort = sort if sort in PAGE_SORT_COLUMNS else "timestamp"
    column = PAGE_SORT_COLUMNS[sort]
    sort_expr = column if column is Trainee.timestamp else func.coalesce(column, "")
    mode_conditions = [func.lower(Trainee.status) == "pending"] if mode == "pending" else []
    stmt = select(Trainee).where(*conditions, *mode_conditions, *keyset.search_conditions(PAGE_SEARCH_COLUMNS, search))
    order = keyset.SortOrder.keyset(
        sort,
        sort_expr,
        Trainee.id,
        descending=descending,
        cursor_value=lambda row: getattr(row, column.key),
        datetime_value=column is Trainee.timestamp,
    )
    return keyset.paginate(db, stmt, order, cursor=cursor, limit=limit, page=page)


def trainer_owned_condition(trainer_username: str):
    """A trainee this trainer may see: assigned to them directly (`trainerEmployeeId`), or with
    any attendance row (including the pre-seeded "Pending" roster entry made when a training is
    scheduled) on one of their own conferences - so a trainee who was put on a trainer's roster
    is visible to that trainer even if the trainee's own `trainerEmployeeId` column points
    elsewhere or is blank."""
    if not (trainer_username or "").strip():
        return false()
    on_their_roster = exists().where(
        Attendance.traineeUid == Trainee.traineeUid,
        Attendance.conferenceUid == Conference.conferenceUid,
        conference_repository.trainer_condition(trainer_username),
    )
    return or_(Trainee.trainerEmployeeId == trainer_username, on_their_roster)


def trainer_owned_list_condition(trainer_username: str):
    """The same set as `trainer_owned_condition`, shaped for LISTING and COUNTING many trainees:
    `traineeUid IN (derived table: assigned UNION on-their-roster)`. The derived table is built once
    from the trainer's indexes (ix_trainee_trainer, ix_conference_trainer -> attendance by
    conference), instead of the OR + EXISTS form, which can't use an index and runs its subquery
    for every trainee in the tenant (perf/phase6_experiments.py owned: 564 -> 52 ms count, 580 ->
    38 ms page, same 9,770 rows, 100k-attendance dataset). For checking ONE known trainee keep
    `trainer_owned_condition` - its EXISTS probe is cheaper than building the whole set."""
    if not (trainer_username or "").strip():
        return false()
    assigned = aliased(Trainee)
    owned = union(
        select(assigned.traineeUid.label("traineeUid")).where(assigned.trainerEmployeeId == trainer_username),
        select(Attendance.traineeUid)
        .join(Conference, Conference.conferenceUid == Attendance.conferenceUid)
        .where(conference_repository.trainer_condition(trainer_username)),
    ).subquery("owned_trainees")
    return Trainee.traineeUid.in_(select(owned.c.traineeUid))


def create(db: Session, trainee: Trainee) -> Trainee:
    db.add(trainee)
    db.commit()
    db.refresh(trainee)
    return trainee


def save(db: Session, trainee: Trainee) -> Trainee:
    db.commit()
    db.refresh(trainee)
    return trainee
