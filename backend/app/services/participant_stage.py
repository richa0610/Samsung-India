"""The Session Dashboard's Stage column: each participant's attendance stage, and done / not done
for every activity of the training after Attendance.

The pin line reads "Attendance" once the participant is Present through their OWN check-in in the
Attendance activity, else "Not Started" - a trainee only the trainer marked Present (by hand, from
the list) hasn't attended the activity themselves. An activity after it is done the same way the
trainee's own Training Detail screen counts it: a Submitted result for its question set here.
"""

from collections.abc import Iterable, Mapping
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.repositories import assessment_repository
from app.schemas.training import ParticipantModuleProgress
from app.services.module_flow import configured_modules, module_suite_uid

NOT_STARTED = "Not Started"
ATTENDED = "Attendance"
# The column is narrow - its chips use the shortest names.
CHIP_LABELS = {"STANDARD_TEST": "Test", "LIVE_QUIZ": "Quiz", "SURVEY": "Survey"}


def _checked_in_themselves(attendance: Attendance | None) -> bool:
    """Present through their own check-in on the phone, not only a trainer's mark. The secure
    check-in - the app's normal one - leaves the check-in photo, also when the trainer had marked
    them Present first; the plain check-in (a phone that captured no location) leaves no photo, but
    then no trainer has touched the row (`updatedBy`, set by a trainer's mark, unset)."""
    if attendance is None or attendance.status != "Present":
        return False
    return bool(attendance.checkInPhoto) or not attendance.updatedBy


class ParticipantStage(NamedTuple):
    stage: str
    modules: list[ParticipantModuleProgress]


def participant_stages(
    db: Session,
    conference: Conference,
    attendance_by_trainee: Mapping[str, Attendance],
    trainee_uids: Iterable[str],
) -> dict[str, ParticipantStage]:
    """{traineeUid: their stage and per-activity progress} for this training's participants - one
    query for every activity's submissions, however many participants."""
    suite_by_module = {key: module_suite_uid(conference, key) for key in configured_modules(conference) if key in CHIP_LABELS}
    submitted = assessment_repository.submitted_trainees_by_suite(
        db, conference.conferenceUid, sorted({suite for suite in suite_by_module.values() if suite})
    )

    stages: dict[str, ParticipantStage] = {}
    for uid in trainee_uids:
        stages[uid] = ParticipantStage(
            stage=ATTENDED if _checked_in_themselves(attendance_by_trainee.get(uid)) else NOT_STARTED,
            modules=[
                ParticipantModuleProgress(
                    key=key, label=CHIP_LABELS[key], done=uid in submitted.get(suite or "", set())
                )
                for key, suite in suite_by_module.items()
            ],
        )
    return stages
