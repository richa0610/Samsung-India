"""Which sessions a trainee may reach - one place for the rules every trainee endpoint that takes a
`conferenceUid` (or a suite) from the client applies, so none of them trusts that ID on its own:

  rostered     the trainee has an attendance row on the session (joined by QR / link, or put on
               the roster) - required to see anything of it (detail, current session, proctoring)
  present      ...and a trainer / their own check-in marked them Present - required for its
               assessment modules (Standard Test, Live Quiz, Survey), the rule the trainee session
               screen already shows ("You must be marked present")
  module open  ...and that module is the session's active module while the session is still
               running (session_service's `isLive` rule) - required to fetch or submit its questions

A session that doesn't exist, isn't in this tenant, or the trainee isn't on looks the same (404),
so an ID can't be probed."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import conflict, forbidden, not_found
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee
from app.repositories import assessment_repository, attendance_repository, conference_repository

NOT_PRESENT = "You must be marked present by the trainer to take part in this session."

# Assessment modules answered through /assessments (the Live Quiz has its own endpoints).
SUBMITTABLE_MODULES = ("STANDARD_TEST", "SURVEY")


def rostered_conference(db: Session, trainee: Trainee, conference_uid: str, *, lock: bool = False) -> tuple[Conference, Attendance]:
    """The session and the trainee's own attendance row on it, or 404. `lock=True` holds the
    attendance row (SELECT ... FOR UPDATE) for the rest of the transaction, so one trainee's
    concurrent submissions for this session run one after another."""
    conference = conference_repository.get_by_uid(db, conference_uid)
    attendance = (
        attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee.traineeUid, lock=lock)
        if conference
        else None
    )
    if conference is None or attendance is None:
        raise not_found("Training not found")
    return conference, attendance


def present_conference(db: Session, trainee: Trainee, conference_uid: str, *, lock: bool = False) -> tuple[Conference, Attendance]:
    conference, attendance = rostered_conference(db, trainee, conference_uid, lock=lock)
    if attendance.status != "Present":
        raise forbidden(NOT_PRESENT)
    return conference, attendance


def has_taken_part(db: Session, trainee: Trainee, conference_uid: str) -> bool:
    """On the roster, or has a submitted result there - what makes a past session the trainee's own
    (their Training History links to it)."""
    if attendance_repository.get_for_conference_and_trainee(db, conference_uid, trainee.traineeUid):
        return True
    return assessment_repository.has_submitted_result(db, conference_uid, trainee.traineeUid)


def module_of_suite(conference: Conference, suite_uid: str) -> Optional[str]:
    """Which of this session's submittable modules `suite_uid` is, if any."""
    if suite_uid and suite_uid == conference.postAssessmentUid:
        return "STANDARD_TEST"
    if suite_uid and suite_uid == conference.surveyUid:
        return "SURVEY"
    return None


def open_assessment(db: Session, trainee: Trainee, conference_uid: str, suite_uid: str, *, lock: bool = False) -> tuple[Conference, str]:
    """The session and module key for a trainee taking `suite_uid` there right now: Present, the
    suite is that session's Standard Test or Survey, and that module is live in a running session."""
    from app.services.session_service import session_is_running  # local: session_service imports this module

    conference, _ = present_conference(db, trainee, conference_uid, lock=lock)
    module_key = module_of_suite(conference, suite_uid)
    if module_key is None:
        raise not_found("Assessment not found")
    if not session_is_running(conference) or conference.activeModuleId != module_key:
        raise conflict("This module isn't open right now")
    return conference, module_key
