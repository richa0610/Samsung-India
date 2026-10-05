from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class AttendanceLog(Base):
    """Mirrors the `attendance_logs` table from mmtbtwob_tops — a timestamped
    event log for each attendance mark action, supporting IP/device audit and
    optional geo-fencing location data."""

    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    logUid = Column(String(50))

    conferenceUid = Column(String(50), index=True)
    traineeUid = Column(String(50), index=True)
    moduleId = Column(String(100))

    markedAt = Column(DateTime, server_default=func.now())
    status = Column(String(20), server_default=text("'Present'"))

    # Network & device audit
    ipAddress = Column(String(45))
    deviceInfo = Column(String(255))

    # GeoFencing: "lat,long" string if geo-fencing is enabled
    locationData = Column(Text)
