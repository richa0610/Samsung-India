"""VERBATIM copy of `training_service.list_attendance` as it was when the paged
endpoint was written - the reference ("oracle") the new `list_attendance_page` is
compared against. It deliberately loads every row and builds every item in
Python. Do not edit it to match the new code: if the two disagree, the new code
is the one that is wrong.

The only change from the original is the function name."""

from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
from app.repositories import assessment_repository, attendance_repository, conference_repository, trainee_repository
from app.schemas.training import AttendanceListItemOut


def legacy_list_attendance(
    db: Session, admin: Admin, org: bool = False, filters: Optional[ConferenceFilters] = None
) -> list[AttendanceListItemOut]:
    """Powers the trainer's Attendance List / Pending Attendance / Confirmed
    Attendance screens (all three fetch this same list and split it
    client-side by `marked`). Scoped to this trainer's own conferences,
    same as list_trainer_trainings - this lives in the trainer's own More
    menu, not a cross-trainer admin view."""
    if org:
        conferences = [c for c in conference_repository.list_all(db) if filters is None or filters.matches(c)]
    else:
        conferences = conference_repository.list_all_for_trainer(db, admin.username)
    conference_by_uid = {c.conferenceUid: c for c in conferences}
    conference_uids = list(conference_by_uid.keys())
    if not conference_uids:
        return []

    attendance_rows = attendance_repository.list_for_conferences(db, conference_uids)

    trainee_uids = {a.traineeUid for a in attendance_rows}
    trainees_by_uid = {t.traineeUid: t for t in trainee_repository.get_by_uids(db, trainee_uids)}

    # Per-participant tallies across every training this trainer owns - the
    # roster is seeded (status "Pending") when a training is scheduled, so a
    # trainee on an upcoming session counts here before it's held.
    trainings_total: Counter[str] = Counter(a.traineeUid for a in attendance_rows)
    trainings_present: Counter[str] = Counter(
        a.traineeUid for a in attendance_rows if a.status == "Present"
    )
    trainings_pending: Counter[str] = Counter(
        a.traineeUid for a in attendance_rows if a.status in ("Pending", "Joined")
    )

    result_rows = assessment_repository.list_results_for_conferences(db, conference_uids)
    # Keep only the latest attempt per (conference, trainee), matching a
    # conference's own post-test suite - the same "latest attempt wins"
    # rule _build_dashboard uses for the single-session dashboard.
    latest_result: dict[tuple[str, str], object] = {}
    for r in result_rows:
        conference = conference_by_uid.get(r.conferenceUid)
        if not conference or r.assessmentSuiteUid != conference.postAssessmentUid:
            continue
        key = (r.conferenceUid, r.traineeUid)
        latest_result.setdefault(key, r)

    items: list[AttendanceListItemOut] = []
    for a in attendance_rows:
        conference = conference_by_uid.get(a.conferenceUid)
        trainee = trainees_by_uid.get(a.traineeUid)
        result = latest_result.get((a.conferenceUid, a.traineeUid))

        post_test_score = None
        post_test_summary = None
        if result:
            total = float(result.maxScore)
            correct = float(result.totalScore)
            post_test_score = f"{correct:g} / {total:g} ({float(result.percentage):g}%)"
            post_test_summary = f"Total: {total:g}, Correct: {correct:g}, Wrong: {total - correct:g}"

        items.append(
            AttendanceListItemOut(
                attendanceId=a.attendanceUid or str(a.id),
                region=conference.region if conference else None,
                product=conference.trainingType if conference else None,
                session=conference.sessionType if conference else None,
                audienceType=conference.audience if conference else None,
                conferenceDate=conference.conferenceDate if conference else None,
                trainerName=conference.trainerName if conference else None,
                trainerHoId=conference.trainerEmployeeId if conference else None,
                participantHoId=trainee.employee_id if trainee else None,
                participantName=trainee.name if trainee else "Unknown Trainee",
                phone=str(a.phone) if a.phone else (str(trainee.phone) if trainee else None),
                state=conference.state if conference else None,
                location=", ".join(filter(None, [conference.district, conference.state])) if conference else None,
                district=conference.district if conference else None,
                reportingManagerOfPromoter=trainee.supervisorName if trainee else None,
                attendanceStatus=a.status,
                markedAt=a.timestamp.strftime("%Y-%m-%d %H:%M:%S") if a.timestamp else None,
                checkIn=a.markedOn,
                checkOut=a.checkOutTime.strftime("%Y-%m-%d %H:%M:%S") if a.checkOutTime else None,
                postTestScore=post_test_score,
                postTestScoreSummary=post_test_summary,
                sessionTypeMethod=conference.sessionType if conference else None,
                conferenceId=a.conferenceUid,
                lastUpdates=a.timestamp.strftime("%Y-%m-%d %H:%M:%S") if a.timestamp else None,
                updatedBy=a.updatedBy,
                updationOn=a.updationOn.strftime("%Y-%m-%d %H:%M:%S") if a.updationOn else None,
                marked=a.status == "Present",
                trainerTrainingsTotal=trainings_total[a.traineeUid],
                trainerTrainingsPresent=trainings_present[a.traineeUid],
                trainerTrainingsPending=trainings_pending[a.traineeUid],
            )
        )

    return items
