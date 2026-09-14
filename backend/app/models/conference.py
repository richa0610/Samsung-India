from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class Conference(Base):
    """Mirrors the real `conference` table (mmtbtwob_tops), trimmed to
    the columns the trainee-facing session flow and the trainer's
    "Add New Training" registration form currently use."""

    __tablename__ = "conference"

    id = Column(Integer, primary_key=True, index=True)
    conferenceUid = Column(String(100), unique=True)

    zone = Column(String(120))
    region = Column(String(150))
    company = Column(String(100))
    requestedBy = Column(String(100))

    trainerEmployeeId = Column(String(100))
    trainerName = Column(String(100))

    conferenceType = Column(String(100), nullable=False, server_default=text("'Non Residential Conference'"))
    conferenceDate = Column(String(100))
    conferenceEndsOn = Column(String(100))
    conferenceTime = Column(String(100))
    conferenceStatus = Column(String(100), nullable=False, server_default=text("'Scheduled'"))
    activeModuleId = Column(String(50))
    # Real-time Live Quiz state: IDLE, WAITING, QUESTION_LIVE, LEADERBOARD,
    # FINISHED. Not driven by any code yet - see module_flow.py, which still
    # only detects Live Quiz via sessionConfig.
    liveQuizState = Column(String(50), nullable=False, server_default=text("'IDLE'"))
    liveQuestionId = Column(String(100))
    liveTimerEndsAt = Column(BigInteger, server_default=text("0"))
    # Milliseconds left on the current question's clock at the moment the
    # trainer paused it via Stop Timer - NULL whenever the timer is running
    # (or no question is live). While this is set, liveTimerEndsAt is stale
    # and ignored; resuming recomputes it as now + this value. See
    # live_quiz_service.stop_timer.
    liveTimerRemainingMs = Column(BigInteger, nullable=True)
    actualStartedAt = Column(DateTime)
    actualEndedAt = Column(DateTime)
    enableCheckIn = Column(Integer, server_default=text("0"))
    # Reason the trainer gave for starting this session earlier or later than
    # its scheduled conferenceDate/conferenceTime (see start_training's
    # SCHEDULE_OVERRIDE gate) - required before an off-schedule start is
    # allowed to proceed at all. None for a session started on schedule.
    scheduleOverrideReason = Column(Text)

    trainingHub = Column(String(100))
    audience = Column(String(150))
    sessionType = Column(String(150))
    trainingType = Column(String(100))
    batchSize = Column(String(150))
    confirmedPax = Column(String(150), server_default=text("'0'"))
    attendanceSheetPax = Column(String(100), nullable=False, server_default=text("'0'"))
    suiteTitle = Column(Text)

    state = Column(String(150))
    district = Column(String(150))
    venueUid = Column(String(150))
    geoLatitude = Column(Numeric(10, 8))
    geoLongitude = Column(Numeric(11, 8))
    geoRadius = Column(Integer, server_default=text("100"))
    # Set once a trainer corrects THIS conference's geoLatitude/geoLongitude
    # via the "you're not at the venue, update its location?" prompt at
    # session start (see _resolve_start_geofence). Scoped to this conference
    # only - the shared venue row is never touched, so a correction here
    # doesn't silently change where the geofence is for every OTHER training
    # at the same venue. After this is set, that flow can't correct it again
    # for this conference. 0 = never overridden yet.
    venueLocationOverridden = Column(Integer, nullable=False, server_default=text("0"))

    assessmentFor = Column(String(100))
    preAssessmentUid = Column(String(100))
    postAssessmentUid = Column(String(100))
    surveyUid = Column(String(100))
    noOfQuestion = Column(String(100), nullable=False, server_default=text("'1'"))

    sessionConfig = Column(Text)
    checklistUid = Column(String(255))

    # Photo captured from the trainer when they hit "Start Session" - maps
    # onto the real table's already-existing (previously unused) column, so
    # no migration/ALTER TABLE is needed for this.
    startConferenceImage = Column(String(300))
    # Security Check-Out at "End Session": the trainer's face photo
    # (`conferenceImage`) and the uploaded signed attendance sheet
    # (`attendanceSheet`). Both are pre-existing real columns - no ALTER.
    conferenceImage = Column(String(300))
    attendanceSheet = Column(String(300))

    updatedBy = Column(String(100))
    updationOn = Column(DateTime)
    status = Column(String(100), nullable=False, server_default=text("'Pending'"))
    auditStatus = Column(String(50), server_default=text("'Pending'"))
    remarks = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
