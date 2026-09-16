from typing import Optional

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
