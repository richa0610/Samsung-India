from typing import List, Optional

from pydantic import BaseModel, Field


class SessionModule(BaseModel):
    key: str
    name: str
    time: Optional[str] = None
    endTime: Optional[str] = None
    duration: Optional[str] = None
    # How long the module actually ran (trainer's Start -> End), e.g. "45m 3s".
    ranDuration: Optional[str] = None
    isLive: bool
    isCompleted: bool
    isMissed: bool = False
    # Set while the trainer hasn't admitted this trainee (marked them Present).
    # The module still shows its LIVE badge, but its action is blocked and this
    # reason is shown instead.
    isLocked: bool = False
    lockReason: Optional[str] = None
    completedAt: Optional[str] = None
    score: Optional[str] = None
    assessmentSuiteUid: Optional[str] = None


class CurrentSession(BaseModel):
    conferenceUid: str
    title: str
    sessionType: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    trainerName: Optional[str] = None
    confirmationStatus: str
    started: bool = True
    # True once the trainer marks this trainee Present. While False every
    # module comes back locked (see SessionModule.lockReason).
    admitted: bool = True
    # The trainee's own attendance row status: None / "Joined" / "Present" /
    # "Absent". "Absent" is a hard eject - the app shows a full-screen block.
    attendanceStatus: Optional[str] = None
    # On-device proctoring locked this trainee out of the post-test (3 strikes).
    # Clears when the trainer unlocks them from the Participant Master List.
    proctoringLocked: bool = False
    # Company-level proctoring controls (Tenant.live_proctoring_enabled /
    # proctoring_max_warnings, Common DB) - lets the trainee app disable
    # on-device proctoring entirely, or use a non-default warning count,
    # per company.
    liveProctoringEnabled: bool = True
    proctoringMaxWarnings: int = 3
    # The trainer has closed the session. The app drops back to the "no active
    # session" screen (the module timeline is gone); past results stay in
    # Rank / Dashboard / history.
    sessionClosed: bool = False
    startsAt: Optional[str] = None
    attendanceGeoFencing: bool = False
    modules: List[SessionModule]


class SessionJoinInfo(BaseModel):
    """Summary of the training behind a shared QR code - shown on the
    "You're joining …" preview before/after the scanner sends the trainee
    through login."""

    conferenceUid: str
    title: str
    sessionType: Optional[str] = None
    date: Optional[str] = None
    location: Optional[str] = None
    trainerName: Optional[str] = None
    started: bool
    startsAt: Optional[str] = None


class SessionHistoryItem(BaseModel):
    conferenceUid: str
    title: str
    date: Optional[str] = None
    trainerName: Optional[str] = None
    attendanceStatus: Optional[str] = None
    score: Optional[str] = None
    passed: Optional[bool] = None


class DashboardMetrics(BaseModel):
    totalTrainings: int = 0
    present: int = 0
    absent: int = 0
    scheduled: int = 0


class DashboardPerformance(BaseModel):
    """The donut gauge: aggregate score across every scored assessment the
    trainee has submitted (post-test + live quiz), all sessions."""

    percentage: float = 0.0
    totalScore: float = 0.0
    maxScore: float = 0.0
    # (avg % of results in the last 30 days) - (avg % before that). None when
    # there isn't data on both sides of the window to compare.
    periodGain: Optional[float] = None


class DashboardRanking(BaseModel):
    """Rank of the trainee among all trainees by aggregate score
    (totalScore / maxScore across every scored result). `global` = the whole
    pool, `state` = the pool filtered to the trainee's own state. Percentile
    is rank / total * 100 - lower is better ("Top X%")."""

    globalRank: Optional[int] = None
    globalTotal: int = 0
    globalPercentile: Optional[float] = None
    stateRank: Optional[int] = None
    stateTotal: int = 0
    statePercentile: Optional[float] = None
    stateName: Optional[str] = None


class DashboardTrainingRow(BaseModel):
    conferenceUid: str
    title: str
    date: Optional[str] = None
    # Raw "YYYY-MM-DD" (unlike `date`, which is display-formatted) - lets the
    # trainee's Training History screen filter by date range client-side,
    # the same way the trainer's Sessions screen does.
    rawDate: Optional[str] = None
    day: Optional[str] = None
    status: str  # trainee's outcome: "Completed" | "Ongoing" | "Scheduled" | "Missed" | "Absent"
    postTestScore: Optional[str] = None  # "x/y"
    quizScore: Optional[str] = None
    rank: Optional[str] = None  # this trainee's place in that session's post-test, e.g. "3"
    rankScope: Optional[str] = None  # "Session"


class TraineeDashboardOut(BaseModel):
    conferenceUid: Optional[str] = None
    hasActiveSession: bool = False
    metrics: DashboardMetrics
    performance: DashboardPerformance
    ranking: DashboardRanking
    trainings: List[DashboardTrainingRow] = []


class ProctoringLockRequest(BaseModel):
    """Sent by the trainee's post-test screen when on-device proctoring
    strikes out (3rd violation). Persists the lock onto the trainee's
    attendance row so the trainer's Participant Master List can show it."""

    conferenceUid: str
    violationType: str = Field(min_length=1, max_length=100)
    strikeNumber: int = Field(ge=1, le=10)


class ProctoringLockOut(BaseModel):
    locked: bool


class QuestionOption(BaseModel):
    id: str
    text: str


class LiveQuestionOut(BaseModel):
    """The active Live Quiz question as seen by a trainee - deliberately has
    no correct-answer field."""

    id: int
    text: str
    options: List[QuestionOption]
    # 1-based position + total, for the "Question X of Y" progress badge.
    order: int = 0
    total: int = 0
    # Countdown length for this question (backend-authoritative).
    timerSeconds: int = 30


class LiveQuizView(BaseModel):
    """Trainee's authoritative view of the Live Quiz, polled by the Live Quiz
    screen and refreshed on each `/ws/live/{conferenceUid}` nudge. `state`
    mirrors `conference.liveQuizState`; `timerEndsAt` is epoch milliseconds."""

    state: str
    conferenceUid: str
    suiteUid: Optional[str] = None
    question: Optional[LiveQuestionOut] = None
    timerEndsAt: Optional[int] = None
    # Server clock at response time (epoch ms) - lets the client correct for a
    # device clock that disagrees with the server's, so the countdown is right.
    serverNowMs: Optional[int] = None
    alreadyAnswered: bool = False


class LiveAnswerRequest(BaseModel):
    conferenceUid: str
    questionId: int
    selectedOption: Optional[str] = None


class LiveAnswerResult(BaseModel):
    accepted: bool
    # Instant feedback (only meaningful when accepted). `correctOptionId` /
    # `explanation` let the trainee screen show the result card right away.
    correct: bool = False
    correctOptionId: Optional[str] = None
    explanation: Optional[str] = None


class LiveRevealOut(BaseModel):
    """Correct answer + explanation for a Live Quiz question - served once the
    trainee has answered it, its timer has expired, or the trainer has moved
    on (so it can never leak the answer while the question is still live)."""

    questionId: int
    correctOptionId: Optional[str] = None
    explanation: Optional[str] = None
    yourOptionId: Optional[str] = None


class LiveQuizSubmitOut(BaseModel):
    """Result of a trainee ending their own Live Quiz early (Final Submit)."""

    submitted: bool
    totalScore: float
    maxScore: float
    percentage: float
    correctCount: int
    totalQuestions: int


class LiveQuizSummaryQuestion(BaseModel):
    """One question of the Live Quiz suite, tagged with this trainee's own
    outcome - for the read-only Assessment Map shown before Final Submit."""

    id: int
    order: int
    text: str
    options: List[QuestionOption]
    # "attempted" (answered) | "timed_out" (seen, ran out) | "skipped" (never reached)
    status: str
    yourOptionId: Optional[str] = None
    correctOptionId: Optional[str] = None
    explanation: Optional[str] = None
    responseMs: Optional[int] = None


class LiveQuizSummaryOut(BaseModel):
    """The calling trainee's per-question map for a Live Quiz. Read-only - the
    correct answer / explanation are already revealed per question during play,
    so this leaks nothing new."""

    suiteUid: Optional[str] = None
    suiteTitle: str
    totalQuestions: int
    attemptedCount: int = 0
    skippedCount: int = 0
    timedOutCount: int = 0
    questions: List[LiveQuizSummaryQuestion] = []


class LiveTimeoutRequest(BaseModel):
    conferenceUid: str
    questionId: int


class LiveQuizRankRow(BaseModel):
    rank: int
    traineeUid: str
    name: str
    score: float
    maxScore: float
    percentage: float
    totalResponseMs: int
    isYou: bool = False


class LiveQuizResultsOut(BaseModel):
    """Trainee's Live Quiz results / leaderboard.

    `state`:
      - "in_progress" - quiz still running, this trainee hasn't submitted
      - "submitted"   - this trainee is done, waiting for the trainer to end it
      - "ranked"      - trainer ended the quiz; `leaderboard` + `you.rank` set
    """

    state: str
    finished: bool = False
    you: Optional[LiveQuizRankRow] = None
    correctCount: int = 0
    totalQuestions: int = 0
    durationSeconds: int = 0
    leaderboard: List[LiveQuizRankRow] = []
