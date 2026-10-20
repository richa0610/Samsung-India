"""Live Quiz (FFF) real-time broadcast.

The trainer drives a synchronised quiz from the Session Dashboard's Live Studio
card; every joined trainee's phone follows. State is authoritative on the
`conference` row (`liveQuizState` / `liveQuestionId` / `liveTimerEndsAt`, stored the other
system's way and read / written only through conference_format); each
mutation nudges the `/ws/live/{conferenceUid}` room with a thin
`{"type": "live_quiz"}` event so both sides refetch their REST view. Trainee
scores are computed once, when the quiz finishes.
"""

import json
import time
from collections import Counter
from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.constants import (
    LIVE_QUIZ_DEFAULT_TIMER_SECONDS,
    LIVE_QUIZ_STATE_FINISHED,
    LIVE_QUIZ_STATE_IDLE,
    LIVE_QUIZ_STATE_LEADERBOARD,
    LIVE_QUIZ_STATE_QUESTION_LIVE,
    MODULE_NAMES,
    RESULT_COMPLETED,
)
from app.core.exceptions import bad_request, conflict, not_found
from app.core.request_context import caller_device
from app.models.admin import Admin
from app.models.conference import Conference
from app.models.quiz import AssessmentResult, AssessmentSuite, Question
from app.models.trainee import Trainee
from app.repositories import (
    assessment_repository,
    attendance_repository,
    conference_repository,
    trainee_repository,
)
from app.services import answer_numbers, conference_access, trainee_access
from app.routers.ws import manager as ws_manager
from app.utils.date_utils import utc_from_epoch_ms, utc_now
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
from app.services.assessment_service import answers_snapshot, record_start, result_to_complete, score_answers
from app.utils.conference_format import (
    active_module,
    is_running,
    quiz_state,
    set_quiz_state,
    set_timer_ends,
    timer_ends_ms,
)
from app.services.module_flow import live_quiz_suite_uid, mark_checkout_if_last_module
from app.utils import question_format


def _now_ms() -> int:
    return int(time.time() * 1000)


def _question_timer_seconds(question: Question) -> int:
    return question_format.timer_seconds(question) or LIVE_QUIZ_DEFAULT_TIMER_SECONDS


def _question_options(question: Question) -> list[dict]:
    return question_format.options(question)


def _question_explanation(question: Question) -> Optional[str]:
    """Shown on the trainee's result / time's-up card (utils/question_format)."""
    return question_format.explanation(question)


def _quiz_title(suite: Optional[AssessmentSuite]) -> str:
    """The quiz's own title, else the module's name ("Live Quiz")."""
    title = (suite.examTitle or suite.courseName) if suite else None
    return title or MODULE_NAMES["LIVE_QUIZ"]


def _timer_paused(conference: Conference) -> bool:
    """The trainer pressed Stop Timer: the clock is frozen (`liveTimerRemainingMs` holds what was
    left, `liveTimerEndsAt` is stale) and answers are locked until Play. Only while a question is
    live - a value left behind by a quiz ended or restarted mid-pause is not a pause."""
    return quiz_state(conference) == LIVE_QUIZ_STATE_QUESTION_LIVE and conference.liveTimerRemainingMs is not None


def _timer_expired(conference: Conference) -> bool:
    """The live question's time is up. A paused clock has only run out if it was stopped with
    nothing left - its stale `liveTimerEndsAt` passing during the pause doesn't count."""
    if _timer_paused(conference):
        return conference.liveTimerRemainingMs <= 0
    ends_ms = timer_ends_ms(conference)
    return ends_ms is not None and _now_ms() >= ends_ms


def _broadcast_ms(conference: Conference, question: Question) -> Optional[int]:
    """When the current question went live = its deadline minus its duration."""
    ends_ms = timer_ends_ms(conference)
    if ends_ms is None:
        return None
    return ends_ms - _question_timer_seconds(question) * 1000


def _present_live_quiz(db: Session, trainee: Trainee, conference_uid: str) -> tuple[Conference, str]:
    """The session (its trainee must be marked Present) and its Live Quiz question set - refused
    when the session has no Live Quiz."""
    conference, _attendance = trainee_access.present_conference(db, trainee, conference_uid)
    suite_uid = live_quiz_suite_uid(conference)
    if not suite_uid:
        raise bad_request("This session has no Live Quiz")
    return conference, suite_uid


def _row_response_ms(row) -> Optional[int]:
    """How long one answer took (stored in `remarks`), or None when it holds no usable number."""
    try:
        return max(0, int(row.remarks))
    except (TypeError, ValueError):
        return None


def _sum_response_ms(rows) -> int:
    return sum(ms for ms in map(_row_response_ms, rows) if ms is not None)


def _result_response_ms(result: AssessmentResult) -> int:
    """The trainee's total answering time, the leaderboard's tie-break: the snapshot's per-question
    "responseMs" added up (assessment_service.answers_snapshot) - or, on a result scored before the
    snapshot took the other system's shape, its "totalResponseMs"."""
    try:
        snapshot = json.loads(result.answersSnapshot or "{}")
        if "totalResponseMs" in snapshot:
            return int(snapshot["totalResponseMs"])
        return sum(int(entry.get("responseMs") or 0) for entry in snapshot.values() if isinstance(entry, dict))
    except (ValueError, TypeError, AttributeError):
        return 0


def live_quiz_ranked_results(db: Session, conference: Conference) -> list[AssessmentResult]:
    """Every trainee's latest Live Quiz result, ranked score DESC then
    total-response-time ASC - live in the sense that it's built from
    whoever has hit Final Submit (or been scored by the trainer's Finish)
    so far, not just once the quiz is over. Shared by the trainee's own
    Rank tab (get_live_quiz_results) and the trainer's Top Performers card
    (training.session_dashboard.get_session_dashboard) while Live Quiz is running."""
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
        suiteTitle=_quiz_title(suite),
        state=quiz_state(conference),
        activeQuestionId=active_qid,
        # While paused, liveTimerEndsAt is stale (frozen at whatever it was
        # when Stop Timer was pressed) - the client must use
        # timerRemainingMs as the frozen display value instead of counting
        # down from this.
        timerEndsAt=timer_ends_ms(conference),
        timerRemainingMs=conference.liveTimerRemainingMs if _timer_paused(conference) else None,
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

def _owned_live_conference(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> Conference:
    """Same access rule as training.common.owned_conference: the assigned trainer, or
    (per the Phase C access grants) an admin-table account whose scope covers this conference."""
    conference = conference_access.get_authorized_conference(db, admin, conference_uid, common_db, tenant_id)
    if not is_running(conference):
        raise conflict("Session is not currently running")
    if active_module(conference) != "LIVE_QUIZ":
        raise conflict("Live Quiz isn't the active module")
    return conference


def _nudge(background_tasks: BackgroundTasks, conference_uid: str, tenant_id: str = None) -> None:
    background_tasks.add_task(ws_manager.send_to_room, tenant_id, conference_uid, {"type": "live_quiz"})


def _dashboard(db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None):
    # Lazy import - training.session_dashboard imports this module at load time.
    from app.services.training import session_dashboard

    return session_dashboard.get_session_dashboard(db, admin, conference_uid, common_db, tenant_id)


def broadcast_question(
    db: Session,
    admin: Admin,
    conference_uid: str,
    question_id: int,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
):
    conference = _owned_live_conference(db, admin, conference_uid, common_db, tenant_id)
    suite_uid = live_quiz_suite_uid(conference)
    question = assessment_repository.get_question(db, question_id)
    if not question or question.assessmentSuiteUid != suite_uid:
        raise bad_request("That question isn't part of this session's Live Quiz")

    set_quiz_state(conference, LIVE_QUIZ_STATE_QUESTION_LIVE)
    conference.liveQuestionId = str(question_id)
    set_timer_ends(conference, _now_ms() + _question_timer_seconds(question) * 1000)
    # A fresh question always starts running, never inheriting a pause left
    # over from whatever question was live before it.
    conference.liveTimerRemainingMs = None
    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid, tenant_id)
    return _dashboard(db, admin, conference_uid, common_db, tenant_id)


def stop_timer(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
    paused: Optional[bool] = None,
):
    """The trainer's Stop Timer / Play Timer button, for the trainer and every
    trainee at once. `paused` is the button pressed: True freezes the current
    question's countdown at whatever time is left (never dropping it to 0);
    False resumes from exactly that point rather than restarting the question.
    Asking for the state it's already in changes nothing, so a press made from
    a stale screen - or by a second trainer/admin on the same session - can't
    flip it the other way. None (an older app that sends no body) toggles."""
    conference = _owned_live_conference(db, admin, conference_uid, common_db, tenant_id)
    if quiz_state(conference) != LIVE_QUIZ_STATE_QUESTION_LIVE:
        raise conflict("No question is currently live")

    is_paused = _timer_paused(conference)
    pause = (not is_paused) if paused is None else paused
    if pause == is_paused:
        return _dashboard(db, admin, conference_uid, common_db, tenant_id)

    now = _now_ms()
    if pause:
        # Freeze at whatever's left, clamped to 0 so a press after the
        # deadline already passed can't store a negative.
        ends_ms = timer_ends_ms(conference)
        conference.liveTimerRemainingMs = max(0, (ends_ms if ends_ms is not None else now) - now)
    else:
        # Pick the clock back up with whatever was left.
        set_timer_ends(conference, now + conference.liveTimerRemainingMs)
        conference.liveTimerRemainingMs = None

    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid, tenant_id)
    return _dashboard(db, admin, conference_uid, common_db, tenant_id)


def show_leaderboard(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
):
    conference = _owned_live_conference(db, admin, conference_uid, common_db, tenant_id)
    set_quiz_state(conference, LIVE_QUIZ_STATE_LEADERBOARD)
    conference.liveQuestionId = None
    conference.liveTimerRemainingMs = None
    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid, tenant_id)
    return _dashboard(db, admin, conference_uid, common_db, tenant_id)


def show_lobby(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
):
    conference = _owned_live_conference(db, admin, conference_uid, common_db, tenant_id)
    set_quiz_state(conference, LIVE_QUIZ_STATE_IDLE)
    conference.liveQuestionId = None
    conference.liveTimerRemainingMs = None
    conference_repository.save(db, conference)
    _nudge(background_tasks, conference_uid, tenant_id)
    return _dashboard(db, admin, conference_uid, common_db, tenant_id)


def finish(
    db: Session,
    admin: Admin,
    conference_uid: str,
    background_tasks: BackgroundTasks,
    common_db: Session = None,
    tenant_id: str = None,
):
    conference = conference_access.get_authorized_conference(db, admin, conference_uid, common_db, tenant_id)
    finish_quiz(db, conference)
    _nudge(background_tasks, conference_uid, tenant_id)
    return _dashboard(db, admin, conference_uid, common_db, tenant_id)


# --- Scoring -------------------------------------------------------------------

def _write_trainee_result(
    db: Session, conference_uid: str, suite_uid: str, trainee_uid: str, questions, answer_rows,
    device: Optional[dict[str, Optional[str]]] = None,
) -> None:
    """Complete a trainee's Live Quiz result from their answer rows - the
    "Started" row their first answer wrote (_record_quiz_start), so startedAt
    is when the quiz began for them. Idempotent - no-op if they already have a
    finished result here (so a trainee's own Final Submit and the trainer's
    Finish never double-score). `answersSnapshot` lists every question with its
    answer time for the leaderboard tie-break (assessment_service.answers_snapshot);
    `durationSeconds` is the total in whole seconds. `device` is the trainee's own IP / user agent
    (request_context.caller_device) when they submitted it themselves; a result
    the trainer's Finish scored keeps the device of the trainee's first answer -
    never the trainer's."""
    if assessment_repository.get_latest_result(db, conference_uid, trainee_uid, suite_uid):
        return
    picks: dict[int, Optional[str]] = {}
    response_ms_by_qid: dict[int, int] = {}
    for row in answer_rows:
        try:
            question_id = int(row.questionId)
        except (TypeError, ValueError):
            continue
        picks[question_id] = row.selectedOption
        response_ms = _row_response_ms(row)
        if response_ms is not None:
            response_ms_by_qid[question_id] = response_ms
    total, max_score, percentage, _ = score_answers(questions, picks)
    result = result_to_complete(db, conference_uid, trainee_uid, suite_uid)
    result.totalScore, result.maxScore, result.percentage = total, max_score, percentage
    result.submittedAt = utc_now()
    result.durationSeconds = _sum_response_ms(answer_rows) // 1000
    result.answersSnapshot = answers_snapshot(questions, picks, scored=True, response_ms_by_qid=response_ms_by_qid)
    result.status = RESULT_COMPLETED
    for column, value in (device or {}).items():
        setattr(result, column, value)


def _record_quiz_start(db: Session, conference_uid: str, trainee_uid: str, suite_uid: str, went_live_ms: int) -> None:
    """The trainee's first answer (or timeout) in the quiz: the quiz began for them when that
    question went live (assessment_service.record_start keeps only the first)."""
    record_start(db, conference_uid, trainee_uid, suite_uid, utc_from_epoch_ms(went_live_ms))


def _went_live_ms(conference: Conference, question: Question) -> int:
    """When `question` went live: from the running clock while it is still the live one, else - its
    timer has just run out on the trainee's phone - one full timer ago."""
    if conference.liveQuestionId == str(question.id):
        broadcast_ms = _broadcast_ms(conference, question)
        if broadcast_ms is not None:
            return broadcast_ms
    return _now_ms() - _question_timer_seconds(question) * 1000


def finish_quiz(db: Session, conference: Conference) -> None:
    """Score every participant who isn't already scored, then mark the quiz
    FINISHED. Idempotent - safe to call from the trainer's Finish action,
    `advance_module` past LIVE_QUIZ, and `end_training`."""
    if quiz_state(conference) == LIVE_QUIZ_STATE_FINISHED:
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

    set_quiz_state(conference, LIVE_QUIZ_STATE_FINISHED)
    db.commit()


# --- Trainee: live view + per-question answer ------------------------------

def get_live_quiz_view(db: Session, trainee: Trainee, conference_uid: str) -> LiveQuizView:
    conference, _attendance = trainee_access.present_conference(db, trainee, conference_uid)

    state = quiz_state(conference)
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
    timer_remaining_ms = None
    if state == LIVE_QUIZ_STATE_QUESTION_LIVE:
        if _timer_paused(conference):
            timer_remaining_ms = conference.liveTimerRemainingMs
        else:
            timer_ends_at = timer_ends_ms(conference)

    return LiveQuizView(
        state=state,
        conferenceUid=conference_uid,
        suiteUid=suite_uid,
        question=question_out,
        timerEndsAt=timer_ends_at,
        timerRemainingMs=timer_remaining_ms,
        serverNowMs=_now_ms(),
        alreadyAnswered=already_answered,
    )


def _answer_result(question: Optional[Question], saved_option: Optional[str]) -> LiveAnswerResult:
    """The instant result card for an accepted answer, recorded as `saved_option`."""
    return LiveAnswerResult(
        accepted=True,
        correct=answer_numbers.is_correct(question, saved_option) if question else False,
        correctOptionId=answer_numbers.correct_option_id(question) if question else None,
        explanation=_question_explanation(question) if question else None,
    )


def submit_live_answer(
    db: Session, trainee: Trainee, payload: LiveAnswerRequest, background_tasks: BackgroundTasks, tenant_id: str = None
) -> LiveAnswerResult:
    # Locked: one trainee's answers run one after another, so two at once can't both record a start.
    conference, _attendance = trainee_access.present_conference(db, trainee, payload.conferenceUid, lock=True)

    live_question = (
        quiz_state(conference) == LIVE_QUIZ_STATE_QUESTION_LIVE
        and conference.liveQuestionId == str(payload.questionId)
        and timer_ends_ms(conference) is not None
    )
    if not live_question or _timer_expired(conference):
        return LiveAnswerResult(accepted=False)
    if _timer_paused(conference):
        # Still open, just stopped by the trainer: `paused` tells the app this isn't a timeout, so
        # it keeps the question up (locked) instead of revealing the answer.
        return LiveAnswerResult(accepted=False, paused=True)

    question = assessment_repository.get_question(db, payload.questionId)
    # One answer per question: whatever is recorded stands - an earlier answer, or the blank row a
    # reported timeout leaves (which unlocks the reveal). An accepted answer's response names the
    # correct option, so a later answer replacing the record would let a trainee answer, read the
    # right option and answer again. The app never repeats one (it locks the options after the first
    # tap) but a restarted app could: a repeat changes nothing and gets the recorded answer's result.
    # Checking before writing is safe - the lock above runs this trainee's quiz writes one at a time.
    recorded = assessment_repository.get_answer(db, payload.conferenceUid, trainee.traineeUid, payload.questionId)
    if recorded is not None:
        if recorded.selectedOption is None:
            return LiveAnswerResult(accepted=False)  # timed out - the app shows it as such
        return _answer_result(question, recorded.selectedOption)

    # Saved as the option's number (answer_numbers); the app is answered with option ids.
    saved_option = answer_numbers.number_for(question, payload.selectedOption) if question else None
    now_ms = _now_ms()
    broadcast_ms = _broadcast_ms(conference, question) if question else None
    response_ms = max(0, now_ms - broadcast_ms) if broadcast_ms is not None else None
    suite_uid = live_quiz_suite_uid(conference) or ""
    if suite_uid:
        _record_quiz_start(
            db, payload.conferenceUid, trainee.traineeUid, suite_uid, broadcast_ms if broadcast_ms is not None else now_ms
        )

    # Commits the answer and the start together, releasing the lock.
    assessment_repository.upsert_answer(
        db,
        conference_uid=payload.conferenceUid,
        trainee_uid=trainee.traineeUid,
        suite_uid=suite_uid,
        question_id=payload.questionId,
        selected_option=saved_option,
        response_ms=response_ms,
    )
    _nudge(background_tasks, payload.conferenceUid, tenant_id)

    return _answer_result(question, saved_option)


def report_live_timeout(
    db: Session, trainee: Trainee, conference_uid: str, question_id: int
) -> LiveAnswerResult:
    """A trainee's per-question timer ran out without a submitted answer. Record
    a blank answer row so the Assessment Map can tell 'timed out' (the question
    reached them, they didn't answer in time) from 'skipped' (never broadcast to
    them). Idempotent - a no-op once any answer row exists for this question."""
    # Locked like an answer (submit_live_answer): one trainee's quiz writes run one after another.
    conference, _attendance = trainee_access.present_conference(db, trainee, conference_uid, lock=True)

    suite_uid = live_quiz_suite_uid(conference)
    question = assessment_repository.get_question(db, question_id)
    if not suite_uid or not question or question.assessmentSuiteUid != suite_uid:
        raise bad_request("That question isn't part of this session's Live Quiz")

    if assessment_repository.get_answer(db, conference_uid, trainee.traineeUid, question_id) is None:
        _record_quiz_start(db, conference_uid, trainee.traineeUid, suite_uid, _went_live_ms(conference, question))
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
    _conference, suite_uid = _present_live_quiz(db, trainee, conference_uid)

    suite = assessment_repository.get_suite_by_uid(db, suite_uid)
    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    my_answers = _answers_by_question(db, conference_uid, suite_uid, trainee.traineeUid)
    out = [
        _summary_question(order, question, my_answers.get(question.id))
        for order, question in enumerate(questions, start=1)
    ]
    counts = Counter(question.status for question in out)
    return LiveQuizSummaryOut(
        suiteUid=suite_uid,
        suiteTitle=_quiz_title(suite),
        totalQuestions=len(questions),
        attemptedCount=counts["attempted"],
        skippedCount=counts["skipped"],
        timedOutCount=counts["timed_out"],
        questions=out,
    )


def _answers_by_question(db: Session, conference_uid: str, suite_uid: str, trainee_uid: str) -> dict[int, object]:
    """This trainee's answer rows in the quiz, by question ID (a row with an unreadable ID is skipped)."""
    answers: dict[int, object] = {}
    for row in assessment_repository.list_answers_for_conference_suite(db, conference_uid, suite_uid):
        if row.traineeUid != trainee_uid:
            continue
        try:
            answers[int(row.questionId)] = row
        except (TypeError, ValueError):
            continue
    return answers


def _answer_status(row) -> str:
    """skipped (no answer row), attempted (an option chosen) or timed_out (the clock ran out)."""
    if row is None:
        return "skipped"
    return "attempted" if row.selectedOption else "timed_out"


def _summary_question(order: int, question: Question, row) -> LiveQuizSummaryQuestion:
    return LiveQuizSummaryQuestion(
        id=question.id,
        order=order,
        text=question.question or "",
        options=[
            QuestionOption(id=o.get("id", ""), text=o.get("text", ""))
            for o in _question_options(question)
        ],
        status=_answer_status(row),
        yourOptionId=answer_numbers.option_id(question, row.selectedOption) if row is not None else None,
        correctOptionId=answer_numbers.correct_option_id(question),
        explanation=_question_explanation(question),
        responseMs=_row_response_ms(row) if row is not None else None,
    )


def reveal_live_question(db: Session, trainee: Trainee, conference_uid: str, question_id: int) -> LiveRevealOut:
    """Correct answer + explanation for one question. Refused while that
    question is still the live one and its timer hasn't run out and the
    trainee hasn't answered - so it can't be used to peek."""
    conference, _attendance = trainee_access.present_conference(db, trainee, conference_uid)

    answer = assessment_repository.get_answer(db, conference_uid, trainee.traineeUid, question_id)
    still_the_live_question = conference.liveQuestionId == str(question_id)
    if still_the_live_question and not _timer_expired(conference) and answer is None:
        raise conflict("This question is still live")

    question = assessment_repository.get_question(db, question_id)
    if not question:
        raise not_found("Question not found")
    return LiveRevealOut(
        questionId=question_id,
        correctOptionId=answer_numbers.correct_option_id(question),
        explanation=_question_explanation(question),
        yourOptionId=answer_numbers.option_id(question, answer.selectedOption) if answer else None,
    )


def submit_live_quiz(db: Session, trainee: Trainee, conference_uid: str) -> LiveQuizSubmitOut:
    """Trainee ends their own Live Quiz early ("Final Submit"). Scores just
    this trainee from their answers so far and marks their result Submitted;
    does not touch the trainer-controlled quiz state."""
    conference, suite_uid = _present_live_quiz(db, trainee, conference_uid)

    questions = assessment_repository.list_questions_for_suite(db, suite_uid)
    all_rows = assessment_repository.list_answers_for_conference_suite(db, conference_uid, suite_uid)
    my_rows = [r for r in all_rows if r.traineeUid == trainee.traineeUid]

    _write_trainee_result(db, conference_uid, suite_uid, trainee.traineeUid, questions, my_rows, caller_device())
    mark_checkout_if_last_module(db, conference, trainee.traineeUid, "LIVE_QUIZ")
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
    conference, suite_uid = _present_live_quiz(db, trainee, conference_uid)

    finished = quiz_state(conference) == LIVE_QUIZ_STATE_FINISHED
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
