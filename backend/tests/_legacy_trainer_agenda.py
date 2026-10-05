"""The trainer Home dashboard's counts as they were computed before Phase 3 - by loading the
trainer's trainings (up to three times) and counting in Python (training_service.list_trainer_trainings).

Kept only as the reference the SQL version (dashboard_repository.trainer_summary_counts) is proven
equal to in tests/test_phase3_home_summary.py, the same way _legacy_admin_service.py backs the
admin dashboard's SQL rewrite. Not imported by the app."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.conference import Conference
from app.repositories import assessment_repository, attendance_repository
from app.utils.date_utils import ist_now
from app.utils.status import title_status
from tests import _legacy_queries as legacy_queries


def _trainee_uids(db: Session, conference_uids: list[str]) -> set[str]:
    uids: set[str] = set()
    for _conference, trainee in legacy_queries.list_present_pairs(db, conference_uids):
        uids.add(trainee)
    for _conference, trainee in legacy_queries.list_submitted_pairs(db, conference_uids):
        uids.add(trainee)
    return uids


def _all_for_trainer(db: Session, username: str) -> list[Conference]:
    return db.query(Conference).filter(Conference.trainerEmployeeId == username).all()


def trainer_counts(db: Session, username: str, start: Optional[str], end: Optional[str]) -> dict:
    is_default_view = start is None and end is None
    query = db.query(Conference).filter(Conference.trainerEmployeeId == username)
    if is_default_view:
        conferences = query.filter(Conference.conferenceDate == date.today().isoformat()).all()
    else:
        if start:
            query = query.filter(Conference.conferenceDate >= start)
        if end:
            query = query.filter(Conference.conferenceDate <= end)
        conferences = query.all()

    if is_default_view:
        all_uids = [c.conferenceUid for c in _all_for_trainer(db, username)]
        total_trainees = len(_trainee_uids(db, all_uids))
    else:
        total_trainees = len(_trainee_uids(db, [c.conferenceUid for c in conferences]))

    counted = [c for c in conferences if title_status(c.conferenceStatus) != "Cancelled"]
    total_sessions = len(counted)
    completed = sum(1 for c in counted if title_status(c.conferenceStatus) == "Completed")
    today_ist = ist_now().date().isoformat()

    def not_started_approved(rows):
        return [
            c for c in rows
            if title_status(c.status) == "Approved"
            and title_status(c.conferenceStatus) not in ("Ongoing", "Live", "Completed", "Cancelled")
        ]

    def is_past(c):
        return bool(c.conferenceDate) and c.conferenceDate < today_ist

    scoped = _all_for_trainer(db, username) if is_default_view else counted
    pending = sum(1 for c in not_started_approved(scoped) if not is_past(c))
    missed = sum(1 for c in not_started_approved(counted) if is_past(c))
    ongoing = sum(1 for c in scoped if title_status(c.conferenceStatus) in ("Ongoing", "Live"))
    return {
        "totalTrainees": total_trainees,
        "totalSessions": total_sessions,
        "completed": completed,
        "pending": pending,
        "missed": missed,
        "ongoing": ongoing,
        "executedPercentage": round((completed / total_sessions) * 100) if total_sessions else 0,
        "pendingPercentage": round((pending / total_sessions) * 100) if total_sessions else 0,
    }
