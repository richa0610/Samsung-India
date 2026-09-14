from sqlalchemy.orm import Session

from app.models.conference_activity_log import ConferenceActivityLog


def list_for_conference(db: Session, conference_uid: str) -> list[ConferenceActivityLog]:
    return (
        db.query(ConferenceActivityLog)
        .filter(ConferenceActivityLog.conferenceUid == conference_uid)
        .order_by(ConferenceActivityLog.timestamp)
        .all()
    )


def add(db: Session, entry: ConferenceActivityLog) -> None:
    db.add(entry)
