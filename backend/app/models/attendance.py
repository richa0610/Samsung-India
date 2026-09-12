from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func

from app.database.connection import Base


class Attendance(Base):
    """Mirrors the real `attendance` table (mmtbtwob_tops)."""

    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)

    attendanceUid = Column(String(100), unique=True)
    conferenceUid = Column(String(100), nullable=False, index=True)
    trainerUid = Column(String(100))
    traineeUid = Column(String(100), nullable=False, index=True)
    phone = Column(BigInteger)

    markedOn = Column(String(50))
    filePath = Column(String(100))
    logPath = Column(String(100))
    excelUploadedOn = Column(String(100))
    updatedBy = Column(String(100))
    updationOn = Column(DateTime)
    isRead = Column(String(50))
    token = Column(String(50))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(100), nullable=False, server_default=text("'Pending'"))

    # Geofence & Check-In/Out
    checkInPhoto = Column(String(300))
    checkOutPhoto = Column(String(300))
    checkOutTime = Column(DateTime)
    checkInDistance = Column(String(50))
    geofenceBypass = Column(SmallInteger, server_default=text("'0'"))
    bypassRemark = Column(Text)
    attemptCount = Column(Integer, server_default=text("'1'"))

    # Security & Metadata
    isTheftLocked = Column(SmallInteger, server_default=text("'0'"))
    remarks = Column(Text)
    securityDetails = Column(Text)
    sessionMeta = Column(Text)
    masterRemarks = Column(Text)
    theftAttemptsLeft = Column(Integer, server_default=text("'3'"))
    theftRemarks = Column(Text)

