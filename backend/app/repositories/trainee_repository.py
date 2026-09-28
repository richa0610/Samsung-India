from sqlalchemy import exists, or_
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee


def get_by_phone(db: Session, phone: int) -> Trainee | None:
    return db.query(Trainee).filter(Trainee.phone == phone).first()


def get_by_uid(db: Session, trainee_uid: str) -> Trainee | None:
    return db.query(Trainee).filter(Trainee.traineeUid == trainee_uid).first()


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


def list_all(db: Session) -> list[Trainee]:
    return db.query(Trainee).order_by(Trainee.timestamp.desc()).all()


def list_scoped(db: Session, conditions: list) -> list[Trainee]:
    """Same list, restricted by `conditions` - built by the caller (see
    trainee_admin_service.list_trainees_admin) from either the admin's admin_access scope
    (access_scope_conditions) or a trainer's own ownership (trainer_owned_condition)."""
    return db.query(Trainee).filter(*conditions).order_by(Trainee.timestamp.desc()).all()


def trainer_owned_condition(trainer_username: str):
    """A trainee this trainer may see: assigned to them directly (`trainerEmployeeId`), or with
    any attendance row (including the pre-seeded "Pending" roster entry made when a training is
    scheduled) on one of their own conferences - so a trainee who was put on a trainer's roster
    is visible to that trainer even if the trainee's own `trainerEmployeeId` column points
    elsewhere or is blank."""
    on_their_roster = exists().where(
        Attendance.traineeUid == Trainee.traineeUid,
        Attendance.conferenceUid == Conference.conferenceUid,
        Conference.trainerEmployeeId == trainer_username,
    )
    return or_(Trainee.trainerEmployeeId == trainer_username, on_their_roster)


def list_uids_in_state(db: Session, state: str) -> set[str]:
    rows = db.query(Trainee.traineeUid).filter(Trainee.state == state).all()
    return {row.traineeUid for row in rows}


def create(db: Session, trainee: Trainee) -> Trainee:
    db.add(trainee)
    db.commit()
    db.refresh(trainee)
    return trainee


def save(db: Session, trainee: Trainee) -> Trainee:
    db.commit()
    db.refresh(trainee)
    return trainee
