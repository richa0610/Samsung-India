"""Live Quiz (FFF) real-time broadcast.

The trainer drives a synchronised quiz from the Session Dashboard's Live Studio
card; every joined trainee's phone follows. State is authoritative on the
`conference` row (`liveQuizState` / `liveQuestionId` / `liveTimerEndsAt`); each
mutation nudges the `/ws/live/{conferenceUid}` room with a thin
`{"type": "live_quiz"}` event so both sides refetch their REST view. Trainee
scores are computed once, when the quiz finishes.
"""

import json
import time
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import (
    LIVE_QUIZ_DEFAULT_TIMER_SECONDS,
    LIVE_QUIZ_STATE_FINISHED,
    LIVE_QUIZ_STATE_IDLE,
    LIVE_QUIZ_STATE_LEADERBOARD,
    LIVE_QUIZ_STATE_QUESTION_LIVE,
)
from app.core.exceptions import bad_request, conflict, not_found
from app.models.admin import Admin
from app.models.conference import Conference
from app.models.quiz import AssessmentResult, Question
from app.models.trainee import Trainee
from app.repositories import (
    assessment_repository,
    attendance_repository,
    conference_repository,
    trainee_repository,
)
from app.routers.ws import manager as ws_manager
from app.schemas.session import (
    LiveAnswerRequest,
    LiveAnswerResult,
    LiveQuestionOut,
    LiveQuizRankRow,
    LiveQuizResultsOut,
    LiveQuizSubmitOut,
    LiveQuizSummaryOut,
    LiveQuizSummaryQuestion,
    LiveQuizView,
    LiveRevealOut,
    QuestionOption,
)
from app.schemas.training import LiveStudioOut, LiveStudioQuestionOut
from app.services.assessment_service import score_answers
from app.services.module_flow import live_quiz_suite_uid

_LOBBY_STATES = (LIVE_QUIZ_STATE_IDLE, "WAITING", "")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _question_timer_seconds(question: Question) -> int:
    try:
        settings = json.loads(question.settings) if question.settings else {}
        return int(settings.get("timerSeconds") or LIVE_QUIZ_DEFAULT_TIMER_SECONDS)
    except (ValueError, TypeError):
        return LIVE_QUIZ_DEFAULT_TIMER_SECONDS


def _question_options(question: Question) -> list[dict]:
    try:
        return json.loads(question.options) if question.options else []
    except ValueError:
        return []


def _question_explanation(question: Question) -> Optional[str]:
    """Shown on the trainee's result / time's-up card. The seed data keeps it
    in `descriptions`; the Answer-Key panel writes `settings.explanation`."""
    try:
        settings = json.loads(question.settings) if question.settings else {}
        if settings.get("explanation"):
            return str(settings["explanation"])
    except (ValueError, TypeError):
        pass
    return (question.descriptions or None) if hasattr(question, "descriptions") else None


def _broadcast_ms(conference: Conference, question: Question) -> Optional[int]:
    """When the current question went live = its deadline minus its duration."""
    if not conference.liveTimerEndsAt:
        return None
    return conference.liveTimerEndsAt - _question_timer_seconds(question) * 1000


def _sum_response_ms(rows) -> int:
    total = 0
    for row in rows:
        try:
            total += max(0, int(row.remarks))
        except (TypeError, ValueError):
            continue
    return total


def _result_response_ms(result: AssessmentResult) -> int:
    try:
        return int(json.loads(result.answersSnapshot or "{}").get("totalResponseMs", 0))
    except (ValueError, TypeError):
        return 0


def live_quiz_ranked_results(db: Session, conference: Conference) -> list[AssessmentResult]:
    """Every trainee's latest Live Quiz result, ranked score DESC then
    total-response-time ASC - live in the sense that it's built from
    whoever has hit Final Submit (or been scored by the trainer's Finish)
    so far, not just once the quiz is over. Shared by the trainee's own
    Rank tab (get_live_quiz_results) and the trainer's Top Performers card
    (training_service.get_session_dashboard) while Live Quiz is running."""
    suite_uid = live_quiz_suite_uid(conference)
    if not suite_uid:
        return []
    results = assessment_repository.list_results_for_conference_suite(db, conference.conferenceUid, suite_uid)
    latest: dict[str, AssessmentResult] = {}
    for r in results:
        latest.setdefault(r.traineeUid, r)
    return sorted(latest.values(), key=lambda r: (-float(r.percentage), _result_response_ms(r)))


# --- Trainer: Live Studio view (folded into SessionDashboardOut) -------------

def build_live_studio(db: Session, conference: Conference) -> Optional[LiveStudioOut]:
    """Only meaningful while LIVE_QUIZ is the active module - callers gate on
    that. Returns None if no Live Quiz suite is configured."""
    suite_uid = live_quiz_suite_uid(conference)
    if not suite_uid:
        return None

    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    responders = assessment_repository.responders_by_question(db, conference.conferenceUid, suite_uid)
    participants = sum(
        1 for a in attendance_repository.list_for_conference(db, conference.conferenceUid) if a.status == "Present"
    )
    active_qid = int(conference.liveQuestionId) if conference.liveQuestionId else None

    return LiveStudioOut(
        suiteUid=suite_uid,
        suiteTitle=(suite.examTitle or suite.courseName or "Live Quiz") if suite else "Live Quiz",
        state=conference.liveQuizState or LIVE_QUIZ_STATE_IDLE,
        activeQuestionId=active_qid,
        # While paused, liveTimerEndsAt is stale (frozen at whatever it was
        # when Stop Timer was pressed) - the client must use
        # timerRemainingMs as the frozen display value instead of counting
        # down from this.
        timerEndsAt=conference.liveTimerEndsAt or None,
        timerRemainingMs=conference.liveTimerRemainingMs,
        serverNowMs=_now_ms(),
        participants=participants,
        totalResponses=responders.get(conference.liveQuestionId or "", 0),
        questions=[
            LiveStudioQuestionOut(
                id=q.id,
                order=q.sort_order or 0,
                text=q.question or "",
                timerSeconds=_question_timer_seconds(q),
                points=q.points or 0,
                responseCount=responders.get(str(q.id), 0),
                isActive=q.id == active_qid,
            )
            for q in questions
        ],
    )


# --- Trainer: broadcast console actions -------------------------------------

def _owned_live_conference(db: Session, admin: Admin, conference_uid: str) -> Conference:
    conference = conference_repository.get_owned_by_trainer(db, admin.username, conference_uid)
    if not conference:
        raise not_found("Training not found")
    if conference.conferenceStatus != "Ongoing":
        raise conflict("Session is not currently running")
    if conference.activeModuleId != "LIVE_QUIZ":
        raise conflict("Live Quiz isn't the active module")
    return conference


def _nudge(background_tasks: BackgroundTasks, conference_uid: str) -> None:
    background_tasks.add_task(ws_manager.send_to_room, conference_uid, {"type": "live_quiz"})


def _dashboard(db: Session, admin: Admin, conference_uid: str):
    # Lazy import - training_service imports this module at load time.
    from app.services import training_service

    return training_service.get_session_dashboard(db, admin, conference_uid)


def broadcast_question(
    db: Session, admin: Admin, conference_uid: str, question_id: int, background_tasks: BackgroundTasks
):
    conference = _owned_live_conference(db, admin, conference_uid)
    suite_uid = live_quiz_suite_uid(conference)
    question = assessment_repository.get_question(db, question_id)
    if not question or question.assessmentSuiteUid != suite_uid:
        raise bad_request("That question isn't part of this session's Live Quiz")

    conference.liveQuizState = LIVE_QUIZ_STATE_QUESTION_LIVE
    conference.liveQuestionId = str(question_id)
    conference.liveTimerEndsAt = _now_ms() + _question_timer_seconds(question) * 1000
    # A fresh question always starts running, never inheriting a pause left
    # over from whatever question was live before it.
    conference.liveTimerRemainingMs = None
    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid)
    return _dashboard(db, admin, conference_uid)


def stop_timer(db: Session, admin: Admin, conference_uid: str, background_tasks: BackgroundTasks):
    """Toggles the current question's clock between running and paused -
    this is the trainer's Stop Timer / Play Timer button. Pausing freezes
    the countdown at whatever time is left (never dropping it to 0);
    pressing it again resumes from exactly that point rather than
    restarting the question."""
    conference = _owned_live_conference(db, admin, conference_uid)
    if conference.liveQuizState != LIVE_QUIZ_STATE_QUESTION_LIVE:
        raise conflict("No question is currently live")

    if conference.liveTimerRemainingMs is not None:
        # Paused -> resume: pick the clock back up with whatever was left.
        conference.liveTimerEndsAt = _now_ms() + conference.liveTimerRemainingMs
        conference.liveTimerRemainingMs = None
    else:
        # Running -> pause: freeze at whatever's left, clamped to 0 so a
        # press after the deadline already passed can't store a negative.
        conference.liveTimerRemainingMs = max(0, (conference.liveTimerEndsAt or _now_ms()) - _now_ms())

    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid)
    return _dashboard(db, admin, conference_uid)


def show_leaderboard(db: Session, admin: Admin, conference_uid: str, background_tasks: BackgroundTasks):
    conference = _owned_live_conference(db, admin, conference_uid)
    conference.liveQuizState = LIVE_QUIZ_STATE_LEADERBOARD
    conference.liveQuestionId = None
    conference.liveTimerRemainingMs = None
    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid)
    return _dashboard(db, admin, conference_uid)


def show_lobby(db: Session, admin: Admin, conference_uid: str, background_tasks: BackgroundTasks):
    conference = _owned_live_conference(db, admin, conference_uid)
    conference.liveQuizState = LIVE_QUIZ_STATE_IDLE
    conference.liveQuestionId = None
    conference.liveTimerRemainingMs = None
    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid)
    return _dashboard(db, admin, conference_uid)


def finish(db: Session, admin: Admin, conference_uid: str, background_tasks: BackgroundTasks):
    conference = conference_repository.get_owned_by_trainer(db, admin.username, conference_uid)
    if not conference:
        raise not_found("Training not found")
    finish_quiz(db, conference)
    _nudge(background_tasks, conference_uid)
    return _dashboard(db, admin, conference_uid)


# --- Scoring -------------------------------------------------------------------

def _write_trainee_result(db: Session, conference_uid: str, suite_uid: str, trainee_uid: str, questions, answer_rows) -> None:
    """Write one `AssessmentResult` for a trainee from their Live Quiz answer
    rows. Idempotent - no-op if they already have a Submitted result here (so
    a trainee's own Final Submit and the trainer's Finish never double-score).
    Total response time (ms) goes in `answersSnapshot` for the leaderboard
    tie-break; `durationSeconds` gets its whole-seconds form."""
    if assessment_repository.get_latest_result(db, conference_uid, trainee_uid, suite_uid):
        return
    picks = {}
    for row in answer_rows:
        try:
            picks[int(row.questionId)] = row.selectedOption
        except (TypeError, ValueError):
            continue
    total, max_score, percentage, _ = score_answers(questions, picks)
    response_ms = _sum_response_ms(answer_rows)
    now = datetime.now()
    assessment_repository.add_result(
        db,
        AssessmentResult(
            conferenceUid=conference_uid,
            traineeUid=trainee_uid,
            assessmentSuiteUid=suite_uid,
            attemptNumber=assessment_repository.next_attempt_number(db, trainee_uid, suite_uid),
            totalScore=total,
            maxScore=max_score,
            percentage=percentage,
            startedAt=now,
            submittedAt=now,
            durationSeconds=response_ms // 1000,
            answersSnapshot=json.dumps({"totalResponseMs": response_ms}),
            status="Submitted",
        ),
    )


def finish_quiz(db: Session, conference: Conference) -> None:
    """Score every participant who isn't already scored, then mark the quiz
    FINISHED. Idempotent - safe to call from the trainer's Finish action,
    `advance_module` past LIVE_QUIZ, and `end_training`."""
    if conference.liveQuizState == LIVE_QUIZ_STATE_FINISHED:
        return

    suite_uid = live_quiz_suite_uid(conference)
    if suite_uid:
        questions = assessment_repository.list_questions_for_suite(db, suite_uid)
        rows = assessment_repository.list_answers_for_conference_suite(db, conference.conferenceUid, suite_uid)
        rows_by_trainee: dict[str, list] = {}
        for row in rows:
            rows_by_trainee.setdefault(row.traineeUid, []).append(row)
        for trainee_uid, answer_rows in rows_by_trainee.items():
            _write_trainee_result(db, conference.conferenceUid, suite_uid, trainee_uid, questions, answer_rows)

    conference.liveQuizState = LIVE_QUIZ_STATE_FINISHED
    db.commit()


# --- Trainee: live view + per-question answer ------------------------------

def get_live_quiz_view(db: Session, trainee: Trainee, conference_uid: str) -> LiveQuizView:
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")

    state = conference.liveQuizState or LIVE_QUIZ_STATE_IDLE
    suite_uid = live_quiz_suite_uid(conference)

    question_out: Optional[LiveQuestionOut] = None
    already_answered = False
    if state == LIVE_QUIZ_STATE_QUESTION_LIVE and conference.liveQuestionId:
        question = assessment_repository.get_question(db, int(conference.liveQuestionId))
        if question:
            suite_questions = (
                assessment_repository.list_questions_for_suite(db, suite_uid) if suite_uid else []
            )
            order = next((i + 1 for i, q in enumerate(suite_questions) if q.id == question.id), 0)
            question_out = LiveQuestionOut(
                id=question.id,
                text=question.question or "",
                options=[QuestionOption(id=o.get("id", ""), text=o.get("text", "")) for o in _question_options(question)],
                order=order,
                total=len(suite_questions),
                timerSeconds=_question_timer_seconds(question),
            )
            already_answered = (
                assessment_repository.get_answer(db, conference_uid, trainee.traineeUid, question.id) is not None
            )

    timer_ends_at = None
    if state == LIVE_QUIZ_STATE_QUESTION_LIVE:
        timer_ends_at = conference.liveTimerEndsAt or None

    return LiveQuizView(
        state=state,
        conferenceUid=conference_uid,
        suiteUid=suite_uid,
        question=question_out,
        timerEndsAt=timer_ends_at,
        serverNowMs=_now_ms(),
        alreadyAnswered=already_answered,
    )


def submit_live_answer(
    db: Session, trainee: Trainee, payload: LiveAnswerRequest, background_tasks: BackgroundTasks
) -> LiveAnswerResult:
    conference = conference_repository.get_by_uid(db, payload.conferenceUid)
    if not conference:
        raise not_found("Training not found")

    live = (
        conference.liveQuizState == LIVE_QUIZ_STATE_QUESTION_LIVE
        and conference.liveQuestionId == str(payload.questionId)
        and conference.liveTimerEndsAt
        and _now_ms() < conference.liveTimerEndsAt
    )
    if not live:
        return LiveAnswerResult(accepted=False)

    question = assessment_repository.get_question(db, payload.questionId)
    broadcast_ms = _broadcast_ms(conference, question) if question else None
    response_ms = max(0, _now_ms() - broadcast_ms) if broadcast_ms is not None else None

    assessment_repository.upsert_answer(
        db,
        conference_uid=payload.conferenceUid,
        trainee_uid=trainee.traineeUid,
        suite_uid=live_quiz_suite_uid(conference) or "",
        question_id=payload.questionId,
        selected_option=payload.selectedOption,
        response_ms=response_ms,
    )
    _nudge(background_tasks, payload.conferenceUid)

    correct_option = (question.correct_answer or None) if question else None
    return LiveAnswerResult(
        accepted=True,
        correct=bool(payload.selectedOption) and payload.selectedOption == correct_option,
        correctOptionId=correct_option,
        explanation=_question_explanation(question) if question else None,
    )


def report_live_timeout(
    db: Session, trainee: Trainee, conference_uid: str, question_id: int
) -> LiveAnswerResult:
    """A trainee's per-question timer ran out without a submitted answer. Record
    a blank answer row so the Assessment Map can tell 'timed out' (the question
    reached them, they didn't answer in time) from 'skipped' (never broadcast to
    them). Idempotent - a no-op once any answer row exists for this question."""
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")

    suite_uid = live_quiz_suite_uid(conference)
    question = assessment_repository.get_question(db, question_id)
    if not suite_uid or not question or question.assessmentSuiteUid != suite_uid:
        raise bad_request("That question isn't part of this session's Live Quiz")

    if assessment_repository.get_answer(db, conference_uid, trainee.traineeUid, question_id) is None:
        assessment_repository.upsert_answer(
            db,
            conference_uid=conference_uid,
            trainee_uid=trainee.traineeUid,
            suite_uid=suite_uid,
            question_id=question_id,
            selected_option=None,
        )
    return LiveAnswerResult(accepted=True)


def get_live_quiz_summary(
    db: Session, trainee: Trainee, conference_uid: str
) -> LiveQuizSummaryOut:
    """The calling trainee's per-question outcome map, shown after they answer
    the last question and before Final Submit."""
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")
    suite_uid = live_quiz_suite_uid(conference)
    if not suite_uid:
        raise bad_request("This session has no Live Quiz")

    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    my_rows = [
        row
        for row in assessment_repository.list_answers_for_conference_suite(db, conference_uid, suite_uid)
        if row.traineeUid == trainee.traineeUid
    ]
    row_by_qid: dict[int, object] = {}
    for row in my_rows:
        try:
            row_by_qid[int(row.questionId)] = row
        except (TypeError, ValueError):
            continue

    out: list[LiveQuizSummaryQuestion] = []
    attempted = timed_out = skipped = 0
    for order, question in enumerate(questions, start=1):
        row = row_by_qid.get(question.id)
        if row is None:
            status = "skipped"
            skipped += 1
        elif row.selectedOption:
            status = "attempted"
            attempted += 1
        else:
            status = "timed_out"
            timed_out += 1

        response_ms = None
        if row is not None:
            try:
                response_ms = max(0, int(row.remarks))
            except (TypeError, ValueError):
                response_ms = None

        out.append(
            LiveQuizSummaryQuestion(
                id=question.id,
                order=order,
                text=question.question or "",
                options=[
                    QuestionOption(id=o.get("id", ""), text=o.get("text", ""))
                    for o in _question_options(question)
                ],
                status=status,
                yourOptionId=row.selectedOption if (row is not None and row.selectedOption) else None,
                correctOptionId=question.correct_answer or None,
                explanation=_question_explanation(question),
                responseMs=response_ms,
            )
        )

    return LiveQuizSummaryOut(
        suiteUid=suite_uid,
        suiteTitle=(suite.examTitle or suite.courseName or "Live Quiz") if suite else "Live Quiz",
        totalQuestions=len(questions),
        attemptedCount=attempted,
        skippedCount=skipped,
        timedOutCount=timed_out,
        questions=out,
    )


def reveal_live_question(db: Session, trainee: Trainee, conference_uid: str, question_id: int) -> LiveRevealOut:
    """Correct answer + explanation for one question. Refused while that
    question is still the live one and its timer hasn't run out and the
    trainee hasn't answered - so it can't be used to peek."""
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")

    answer = assessment_repository.get_answer(db, conference_uid, trainee.traineeUid, question_id)
    still_the_live_question = conference.liveQuestionId == str(question_id)
    timer_expired = bool(conference.liveTimerEndsAt) and _now_ms() >= conference.liveTimerEndsAt
    if still_the_live_question and not timer_expired and answer is None:
        raise conflict("This question is still live")

    question = assessment_repository.get_question(db, question_id)
    if not question:
        raise not_found("Question not found")
    return LiveRevealOut(
        questionId=question_id,
        correctOptionId=question.correct_answer or None,
        explanation=_question_explanation(question),
        yourOptionId=answer.selectedOption if answer else None,
    )


def submit_live_quiz(db: Session, trainee: Trainee, conference_uid: str) -> LiveQuizSubmitOut:
    """Trainee ends their own Live Quiz early ("Final Submit"). Scores just
    this trainee from their answers so far and marks their result Submitted;
    does not touch the trainer-controlled quiz state."""
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")
    suite_uid = live_quiz_suite_uid(conference)
    if not suite_uid:
        raise bad_request("This session has no Live Quiz")

    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    all_rows = assessment_repository.list_answers_for_conference_suite(db, conference_uid, suite_uid)
    my_rows = [r for r in all_rows if r.traineeUid == trainee.traineeUid]

    _write_trainee_result(db, conference_uid, suite_uid, trainee.traineeUid, questions, my_rows)
    db.commit()

    result = assessment_repository.get_latest_result(db, conference_uid, trainee.traineeUid, suite_uid)
    total = float(result.totalScore) if result else 0.0
    max_score = float(result.maxScore) if result else 0.0
    picks = {}
    for r in my_rows:
        try:
            picks[int(r.questionId)] = r.selectedOption
        except (TypeError, ValueError):
            continue
    _, _, _, correct_count = score_answers(questions, picks)
    return LiveQuizSubmitOut(
        submitted=True,
        totalScore=total,
        maxScore=max_score,
        percentage=float(result.percentage) if result else 0.0,
        correctCount=correct_count,
        totalQuestions=len(questions),
    )


def get_live_quiz_results(db: Session, trainee: Trainee, conference_uid: str) -> LiveQuizResultsOut:
    """Trainee's Live Quiz results + this-session leaderboard.

    The board is LIVE: once the trainee has hit Final Submit it ranks everyone
    who has submitted so far (score DESC, then total response time ASC) and the
    trainee's Rank screen re-polls it every few seconds while the quiz runs.
    `finished` flips true once the trainer ends the quiz - the ranking is final
    then, and the trainee's Rank tab keeps showing it after the session ends."""
    conference = conference_repository.get_by_uid(db, conference_uid)
    if not conference:
        raise not_found("Training not found")
    suite_uid = live_quiz_suite_uid(conference)
    if not suite_uid:
        raise bad_request("This session has no Live Quiz")

    finished = conference.liveQuizState == LIVE_QUIZ_STATE_FINISHED
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    ranked = live_quiz_ranked_results(db, conference)
    mine = next((r for r in ranked if r.traineeUid == trainee.traineeUid), None)

    my_answers = [
        r
        for r in assessment_repository.list_answers_for_conference_suite(db, conference_uid, suite_uid)
        if r.traineeUid == trainee.traineeUid
    ]
    my_picks = {}
    for r in my_answers:
        try:
            my_picks[int(r.questionId)] = r.selectedOption
        except (TypeError, ValueError):
            continue
    _, _, _, my_correct = score_answers(questions, my_picks)

    names = {t.traineeUid: t.name for t in trainee_repository.get_by_uids(db, {r.traineeUid for r in ranked})}
    rows = [
        LiveQuizRankRow(
            rank=i + 1,
            traineeUid=r.traineeUid,
            name=names.get(r.traineeUid) or "Trainee",
            score=float(r.totalScore),
            maxScore=float(r.maxScore),
            percentage=float(r.percentage),
            totalResponseMs=_result_response_ms(r),
            isYou=r.traineeUid == trainee.traineeUid,
        )
        for i, r in enumerate(ranked)
    ]
    you = next((row for row in rows if row.isYou), None)

    # No board until this trainee has submitted (their Rank tab mid-quiz just
    # shows "in progress"). Once they have: "live" while the quiz runs (the
    # ranking is provisional and re-polled), "ranked" once the trainer ends it.
    if you is None and mine is None:
        return LiveQuizResultsOut(
            state="in_progress",
            finished=finished,
            you=None,
            correctCount=my_correct,
            totalQuestions=len(questions),
            durationSeconds=0,
        )

    return LiveQuizResultsOut(
        state="ranked" if finished else "live",
        finished=finished,
        you=you,
        correctCount=my_correct,
        totalQuestions=len(questions),
        durationSeconds=(mine.durationSeconds or 0) if mine else 0,
        leaderboard=rows,
    )
