from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class AssessmentSuite(Base):
    """Mirrors the `assessmentsuite` table from mmtbtwob_tops — a quiz/test/survey
    container. Now includes courseUid linkage and theme JSON blob."""

    __tablename__ = "assessmentsuite"

    id = Column(Integer, primary_key=True, index=True)
    assessmentSuiteUid = Column(String(100), unique=True)
    courseUid = Column(String(100))
    courseName = Column(String(100))
    examTitle = Column(Text)
    description = Column(Text)
    assessment_type = Column(String(50), server_default=text("'Quiz'"))
    # JSON blob: Global Quiz Settings (Shuffle, Progress Bar, etc.)
    settings = Column(Text)
    # JSON blob: Theme Colors, Fonts, Backgrounds
    theme = Column(Text)
    noOfQuestion = Column(Integer, server_default=text("0"))
    testTime = Column(String(50))
    status = Column(String(50), nullable=False, server_default=text("'Pending'"))

    # Upload tracking
    filePath = Column(String(100))
    logPath = Column(String(100))
    excelUploadedOn = Column(String(100))

    # Audit
    updatedBy = Column(String(100))
    updationOn = Column(DateTime, onupdate=func.now())
    isRead = Column(String(100))
    token = Column(String(100))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)


class Question(Base):
    """Mirrors the `questions` table — the question bank, linked to a suite
    via `assessmentSuiteUid`."""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessmentSuiteUid = Column(String(100), index=True)
    question = Column(Text)
    question_type = Column(String(50), nullable=False, server_default=text("'multiple_choice'"))
    sort_order = Column(Integer, server_default=text("0"))
    options = Column(Text)
    correct_answer = Column(Text)
    points = Column(Integer, server_default=text("0"))
    descriptions = Column(Text)
    # JSON blob, e.g. {"timerSeconds": 30, "explanation": "..."} - the
    # Answer Key panel's Timer/Explanation fields, which have no dedicated
    # columns of their own.
    settings = Column(Text)
    status = Column(String(50), nullable=False, server_default=text("'Approved'"))

    # Upload tracking
    filePath = Column(String(100))
    logPath = Column(String(100))
    excelUploadedOn = Column(String(100))

    # Audit
    updatedBy = Column(String(100))
    updationOn = Column(DateTime, onupdate=func.now())
    token = Column(String(100))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    remarks = Column(Text)
    masterRemarks = Column(Text)


class Assessment(Base):
    """Mirrors the `assessment` table — a trainee's single answer submission
    for one question."""

    __tablename__ = "assessment"

    id = Column(Integer, primary_key=True, index=True)
    assessmentUid = Column(String(100))
    assessmentSuiteUid = Column(String(100), index=True)
    conferenceUid = Column(String(100), index=True)
    traineeUid = Column(String(100), index=True)
    questionId = Column(String(100))
    selectedOption = Column(Text)
    status = Column(String(50), nullable=False, server_default=text("'Approved'"))

    # Upload tracking
    filePath = Column(String(100))
    logPath = Column(String(100))
    excelUploadedOn = Column(String(100))

    # Audit
    updatedBy = Column(String(100))
    updationOn = Column(DateTime, onupdate=func.now())
    isRead = Column(String(100))
    token = Column(String(100))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)


class AssessmentResult(Base):
    """Mirrors the `assessment_results` table — per-attempt scoring summary,
    the source table for leaderboards. Now includes answersSnapshot JSON
    and device/IP audit columns."""

    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    resultUid = Column(String(50))
    conferenceUid = Column(String(50), index=True)
    traineeUid = Column(String(50), index=True)
    assessmentSuiteUid = Column(String(50), index=True)
    attemptNumber = Column(Integer, server_default=text("1"))
    totalScore = Column(Numeric(10, 2), server_default=text("0.00"))
    maxScore = Column(Numeric(10, 2), server_default=text("0.00"))
    percentage = Column(Numeric(5, 2), server_default=text("0.00"))
    startedAt = Column(DateTime)
    submittedAt = Column(DateTime)
    durationSeconds = Column(Integer, server_default=text("0"))
    status = Column(String(20), server_default=text("'Started'"))
    # JSON dump of all answers for quick viewing / replay
    answersSnapshot = Column(Text)
    # Network & device audit
    ipAddress = Column(String(45))
    deviceInfo = Column(String(255))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
