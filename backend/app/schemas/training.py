from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas._common import (
    DateLikeStr,
    IdStr,
    OptDateLikeStr,
    OptDigitStr,
    OptIdStr,
    OptShortStr,
    OptTextStr,
    ShortStr,
)


class ModuleConfig(BaseModel):
    """One block of `conference.sessionConfig` - shared shape for the
    Standard Test, Live Quiz and Survey modules of the session flow."""

    category: OptShortStr = None
    assessmentSuiteUid: OptIdStr = None
    questionCount: Optional[Annotated[int, Field(ge=0, le=10_000)]] = None
    startTime: OptDateLikeStr = None
    endTime: OptDateLikeStr = None
    checkIn: bool = False
    unlockCondition: OptShortStr = None


class AssessmentSuiteOut(BaseModel):
    """One row of `assessmentsuite`, as offered to the trainer's Category /
    Select Question Set pickers when building a session flow."""

    assessmentSuiteUid: str
    category: str
    name: str
    noOfQuestion: int


class QuestionOptionIn(BaseModel):
    id: IdStr
    text: Annotated[str, Field(max_length=1000)]


class QuestionCreate(BaseModel):
    question: Annotated[str, Field(min_length=1, max_length=2000)]
    questionType: ShortStr = "multiple_choice"
    options: Annotated[list[QuestionOptionIn], Field(max_length=20)] = []
    correctAnswer: OptIdStr = None
    points: Annotated[int, Field(ge=0, le=1000)] = 1
    timerSeconds: Optional[Annotated[int, Field(ge=0, le=86_400)]] = None
    explanation: OptTextStr = None


class QuestionOut(BaseModel):
    id: int
    question: str
    questionType: str
    options: list[QuestionOptionIn]
    correctAnswer: Optional[str] = None
    points: int
    timerSeconds: Optional[int] = None
    explanation: Optional[str] = None
    sortOrder: int


class AssessmentSuiteCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: OptTextStr = None
    category: Annotated[str, Field(min_length=1, max_length=120)]
    testTime: OptDigitStr = None
    type: ShortStr = "Quiz"


class AssessmentSuiteDetail(BaseModel):
    assessmentSuiteUid: str
    title: str
    description: Optional[str] = None
    category: str
    testTime: Optional[str] = None
    type: str
    noOfQuestion: int
    questions: list[QuestionOut] = []


class PendingSessionItem(BaseModel):
    conferenceUid: str
    title: str
    trainerName: Optional[str] = None
    conferenceDate: Optional[str] = None
    conferenceTime: Optional[str] = None
    status: str


class AttendanceConfig(BaseModel):
    checkInOpens: Optional[str] = None
    checkOutCloses: Optional[str] = None
    geoFencing: bool = False
    # Metres a trainee may be from the venue and still check in. Only used when
    # geoFencing is on and the venue has coordinates. Defaults to 100 (the
    # `conference.geoRadius` column default) when not given.
    geoRadius: Optional[int] = Field(default=None, ge=10, le=5000)


class SessionFlowConfig(BaseModel):
    attendance: Optional[AttendanceConfig] = None
    standardTest: Optional[ModuleConfig] = None
    liveQuiz: Optional[ModuleConfig] = None
    survey: Optional[ModuleConfig] = None


class TrainingCreate(BaseModel):
    zone: OptShortStr = None
    region: OptShortStr = None
    company: OptShortStr = None
    requestedBy: OptShortStr = None

    trainerEmployeeId: OptIdStr = None
    trainerName: OptShortStr = None

    state: OptShortStr = None
    district: OptShortStr = None
    venue: OptIdStr = None

    isResidential: bool = False
    conferenceDate: DateLikeStr
    conferenceTime: DateLikeStr
    # Only meaningful when isResidential is set - the program's last day.
    # No dedicated conference column for this yet, so it's folded into
    # sessionConfig (see create_training) rather than conferenceEndsOn,
    # which already means something else (the session's actual end
    # timestamp, set by /trainings/{uid}/end).
    trainingEndDate: OptDateLikeStr = None
    trainingHub: OptShortStr = None
    audience: OptShortStr = None
    sessionType: OptShortStr = None
    trainingType: OptShortStr = None
    batchSize: OptDigitStr = None

    sessionFlow: Optional[SessionFlowConfig] = None
    checklist: Optional[Annotated[list[ShortStr], Field(max_length=100)]] = None


class TrainingOut(BaseModel):
    conferenceUid: str
    conferenceStatus: str
    status: str


class AttendanceMarkRequest(BaseModel):
    status: Literal["Present", "Absent", "Joined", "Pending"]
    # The trainer must give a reason for a manual Present/Absent mark - it's
    # appended (with who + when) to `attendance.remarks` as an audit trail.
    reason: str = Field(min_length=1, max_length=500)


class ProctoringUnlockRequest(BaseModel):
    # The trainer must give a reason to clear a proctoring lockout - appended
    # (with who + when) to `attendance.theftRemarks` + `remarks`.
    reason: str = Field(min_length=1, max_length=500)


class AttendanceListItemOut(BaseModel):
    """Powers the trainer's Attendance List / Pending Attendance / Confirmed
    Attendance screens - one row per attendance record across every
    conference this trainer owns. `marked`/`Present` vs not is how the
    Pending/Confirmed screens split the same list client-side."""

    attendanceId: str
    region: Optional[str] = None
    product: Optional[str] = None
    session: Optional[str] = None
    audienceType: Optional[str] = None
    conferenceDate: Optional[str] = None
    trainerName: Optional[str] = None
    trainerHoId: Optional[str] = None
    participantHoId: Optional[str] = None
    participantName: str
    phone: Optional[str] = None
    state: Optional[str] = None
    location: Optional[str] = None
    reportingManagerOfPromoter: Optional[str] = None
    attendanceStatus: str
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    postTestScore: Optional[str] = None
    postTestScoreSummary: Optional[str] = None
    sessionTypeMethod: Optional[str] = None
    conferenceId: Optional[str] = None
    lastUpdates: Optional[str] = None
    marked: bool
    # How many of this trainer's trainings the participant is on, across all
    # of them - same value repeats on each of that participant's rows.
    trainerTrainingsTotal: int = 0
    trainerTrainingsPresent: int = 0
    trainerTrainingsPending: int = 0


class TrainingAgendaItem(BaseModel):
    conferenceUid: str
    title: str
    trainerName: Optional[str] = None
    hoid: Optional[str] = None
    conferenceDate: Optional[str] = None
    conferenceTime: Optional[str] = None
    conferenceStatus: str
    approvalStatus: str
    location: Optional[str] = None
    batchSize: Optional[str] = None
    trainingType: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    trainingHub: Optional[str] = None
    venueName: Optional[str] = None
    updatedBy: Optional[str] = None
    updationOn: Optional[str] = None
    timestamp: Optional[str] = None
    traineeCount: int = 0


class TrainerAgendaResponse(BaseModel):
    """GET /admin/trainings - the session list plus the dashboard's summary
    stats, all computed server-side so the frontend just displays them
    rather than re-deriving them from the raw list itself. `totalTrainees`
    is a de-duplicated headcount (see the router for how it's built from
    `attendance`/`assessment_results`); `totalSessions`/`completed`/`pending`
    are counted straight off the filtered `conference` rows. `recentCompleted`
    is always the trainer's most recently completed sessions all-time,
    regardless of `start`/`end` - the Recent Sessions card ignores whatever
    date scope the rest of this response uses."""

    trainings: list[TrainingAgendaItem]
    totalTrainees: int
    totalSessions: int
    completed: int
    pending: int
    executedPercentage: int
    pendingPercentage: int
    recentCompleted: list[TrainingAgendaItem] = []


class AudienceBreakdown(BaseModel):
    total: int
    present: int
    absent: int = 0
    # Joined via QR / on the list but the trainer hasn't marked them Present
    # or Absent yet.
    notMarked: int = 0
    # On this trainer's roster vs. walked-in / joined by QR.
    assigned: int = 0
    unassigned: int = 0
    # Participants with no earlier Present attendance in any other session -
    # being trained for the first time.
    fresh: int = 0


class AssessmentSummary(BaseModel):
    pass_: int = Field(0, alias="pass")
    fail: int
    totalAttempts: int

    model_config = {"populate_by_name": True}


class TopPerformer(BaseModel):
    traineeUid: str
    name: str
    score: float = 0
    maxScore: float = 0
    percentage: float


class SessionHeroStat(BaseModel):
    """Per-module summary for the Session Heroes cards (Live Quiz / Test)."""

    moduleKey: str  # "LIVE_QUIZ" | "STANDARD_TEST"
    label: str
    participants: int
    averagePercent: float
    bestPercent: float
    topName: Optional[str] = None


class TraineeRow(BaseModel):
    traineeUid: str
    name: str
    employeeId: Optional[str] = None
    phone: Optional[int] = None
    # "ASSIGNED" if on this trainer's roster, else "NOT ALLOCATED" (walked
    # in / joined by QR).
    audienceType: str = "NOT ALLOCATED"
    # "Present" | "Pending" (joined, not checked in) | "Absent" | "Attempted"
    status: str
    markedOn: Optional[str] = None
    checkOutTime: Optional[str] = None
    score: Optional[str] = None
    profilePhoto: Optional[str] = None
    # On-device proctoring lockout (post-test). `isLocked` drives the red
    # "LOCKED" pill + the trainer's unlock control; `proctoringLogs` are the
    # already-formatted strike/unlock lines from `attendance.theftRemarks`.
    isLocked: bool = False
    proctoringStrikes: int = 0
    proctoringMaxStrikes: int = 3
    proctoringLogs: list[str] = []


class ExecutionFlowItem(BaseModel):
    moduleKey: str
    label: str
    status: str  # "Pending" | "Running" | "Completed"
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    elapsedSeconds: Optional[int] = None
    # Planned duration of this module in minutes, from the start/end times the
    # trainer set on it when building the session flow. None when it has no
    # usable pair. Feeds the "Assigned" budget + "Total Time Used" gauge.
    assignedMinutes: Optional[int] = None
    # True when the trainer may start this module now: the session is
    # running, nothing else is live, this module hasn't run yet, and every
    # module before it in the flow has finished. Drives the per-row Start
    # button on the Session Dashboard's Execution Flow.
    canStart: bool = False
    # True when the trainer may re-run this finished module now: the session
    # is running and nothing else is currently live. Drives the per-row
    # Restart button.
    canRestart: bool = False


class AuditLogEntry(BaseModel):
    """One STARTED/STOPPED pair for a module - a module can run more than
    once (e.g. if `advance-module` cycles back around), so unlike
    `ExecutionFlowItem` this is per-run, not per-module."""

    moduleKey: str
    label: str
    runNumber: int
    startedAt: Optional[str] = None
    endedAt: Optional[str] = None
    elapsedSeconds: Optional[int] = None
    isRunning: bool = False
    startedBy: Optional[str] = None
    # Free-text detail for a non-module event (e.g. the reason a trainer gave
    # when overriding a late session start). None for ordinary module runs.
    note: Optional[str] = None


class LiveBroadcastRequest(BaseModel):
    questionId: int


class LiveStudioQuestionOut(BaseModel):
    """One question of the configured Live Quiz suite, as shown in the
    trainer's Live Studio card while LIVE_QUIZ is the active module."""

    id: int
    order: int
    text: str
    timerSeconds: int
    points: int
    responseCount: int
    isActive: bool


class LiveStudioOut(BaseModel):
    """Only populated on SessionDashboardOut when `activeModuleId == "LIVE_QUIZ"`
    - drives the Live Studio broadcast console. `state` mirrors
    `conference.liveQuizState`; `timerEndsAt` is epoch milliseconds."""

    suiteUid: str
    suiteTitle: str
    state: str
    activeQuestionId: Optional[int] = None
    timerEndsAt: Optional[int] = None
    # Server clock at response time (epoch ms). The client subtracts its own
    # Date.now() to get the clock offset, so the countdown is right even when
    # the device clock disagrees with the server's.
    serverNowMs: Optional[int] = None
    participants: int
    totalResponses: int
    questions: list[LiveStudioQuestionOut] = []


class SessionDashboardOut(BaseModel):
    conferenceUid: str
    title: str
    trainingType: Optional[str] = None
    conferenceDate: Optional[str] = None
    conferenceTime: Optional[str] = None
    trainerName: Optional[str] = None
    location: Optional[str] = None
    conferenceStatus: str
    approvalStatus: str
    activeModuleId: Optional[str] = None
    # Question count of the active module's suite - only for STANDARD_TEST /
    # LIVE_QUIZ; None for ATTENDANCE / SURVEY / no active module.
    activeModuleQuestionCount: Optional[int] = None

    actualStartedAt: Optional[str] = None
    actualEndedAt: Optional[str] = None
    runtimeSeconds: Optional[int] = None

    audience: AudienceBreakdown
    assessment: AssessmentSummary
    topPerformers: list[TopPerformer]
    trainees: list[TraineeRow]
    executionFlow: list[ExecutionFlowItem] = []
    auditLog: list[AuditLogEntry] = []
    sessionHeroes: list[SessionHeroStat] = []
    # Only present while LIVE_QUIZ is the active module - see _live_studio in
    # services/training_service.py.
    liveStudio: Optional[LiveStudioOut] = None


class SessionReportParticipant(BaseModel):
    userId: str
    name: str
    role: str = "Participant"
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    score: Optional[str] = None


class SessionReportSummary(BaseModel):
    conferenceId: str
    sessionName: str
    date: Optional[str] = None
    state: Optional[str] = None
    schedule: Optional[str] = None
    duration: Optional[str] = None
    venueLink: Optional[str] = None


class SessionReportOut(BaseModel):
    """Session Report screen. `standardTest` / `liveQuiz` list only the
    trainees who actually completed that module for this conference (a
    Submitted assessment result for the module's suite)."""

    summary: SessionReportSummary
    standardTest: list[SessionReportParticipant] = []
    liveQuiz: list[SessionReportParticipant] = []
