from sqlalchemy.orm import Session

from app.models.conference_activity_log import ConferenceActivityLog


def list_for_conference(db: Session, conference_uid: str) -> list[ConferenceActivityLog]:
    return (
        db.query(ConferenceActivityLog)
        .filter(ConferenceActivityLog.conferenceUid == conference_uid)
        # In the order written: rows from before 2026-10-17 hold UTC times and later ones India
        # time, so a session that ran across the change would sort wrongly by time.
        .order_by(ConferenceActivityLog.id)
        .all()
    )


def add(db: Session, entry: ConferenceActivityLog) -> None:
    db.add(entry)
