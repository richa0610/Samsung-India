"""The whole-table / all-pairs queries the pre-optimization code used - kept ONLY for the reference
implementations the SQL versions are proven equal to (tests/_legacy_*.py, test_phase5_aggregates).
The app no longer has, or needs, any of them (Phase 7 removed them from app/repositories)."""

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult


def conference_list_all(db: Session) -> list[Conference]:
    return db.query(Conference).all()


def conference_list_all_for_trainer(db: Session, trainer_username: str) -> list[Conference]:
    return db.query(Conference).filter(Conference.trainerEmployeeId == trainer_username).all()


def attendance_list_for_conferences(db: Session, conference_uids: list[str]) -> list[Attendance]:
    if not conference_uids:
        return []
    return (
        db.query(Attendance)
        .filter(Attendance.conferenceUid.in_(conference_uids))
        .order_by(Attendance.timestamp.desc())
        .all()
    )


def list_present_pairs(db: Session, conference_uids: list[str]) -> list[tuple[str, str]]:
    if not conference_uids:
        return []
    rows = (
        db.query(Attendance.conferenceUid, Attendance.traineeUid)
        .filter(Attendance.conferenceUid.in_(conference_uids), Attendance.status == "Present")
        .all()
    )
    return [(row.conferenceUid, row.traineeUid) for row in rows]


def list_submitted_pairs(db: Session, conference_uids: list[str]) -> list[tuple[str, str]]:
    if not conference_uids:
        return []
    rows = (
        db.query(AssessmentResult.conferenceUid, AssessmentResult.traineeUid)
        .filter(AssessmentResult.conferenceUid.in_(conference_uids), AssessmentResult.status == "Submitted")
        .all()
    )
    return [(row.conferenceUid, row.traineeUid) for row in rows]


def list_all_submitted_results(db: Session) -> list[AssessmentResult]:
    return db.query(AssessmentResult).filter(AssessmentResult.status == "Submitted").all()


def list_attended_trainee_uids(db: Session) -> set[str]:
    rows = db.query(Attendance.traineeUid).filter(Attendance.status == "Present").distinct().all()
    return {row.traineeUid for row in rows}
