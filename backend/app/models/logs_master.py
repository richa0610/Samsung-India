from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class LogsMaster(Base):
    """Mirrors the `logsmaster` table from mmtbtwob_tops - originally a
    login/logout audit log (username/role/login_IP/loginTime/logoutTime),
    unused by any code until now. Repurposed as the app's general user
    activity trail: one row per significant action a user takes (login,
    registration, starting/ending a session, marking attendance, submitting
    an assessment, etc.), written via app/services/activity_log_service.py.

    `action` is the one new column added on top of the legacy schema (via
    the startup schema-sync, no manual migration needed) - everything else
    reuses the original columns for their closest generic equivalent:
    `login_IP` as the request IP for any action (not just login), `remarks`
    as a human-readable description, `status` as Success/Failed. Never
    write `password`/`securedPassword` here even though the legacy columns
    exist - those were for the old login-log design and have no place in an
    activity trail."""

    __tablename__ = "logsmaster"

    id = Column(Integer, primary_key=True, index=True)
    logsUid = Column(String(100), unique=True)
    username = Column(String(100), index=True)
    role = Column(String(100))
    # What happened - a short code like "LOGIN", "START_SESSION",
    # "SUBMIT_ASSESSMENT". The one column this repurposing actually adds.
    action = Column(String(100), index=True)
    login_IP = Column(String(200))
    updatedBy = Column(String(100))
    updatedOn = Column(String(100))
    loginTime = Column(String(100))
    logoutTime = Column(String(100))
    token = Column(String(100))
    filePath = Column(String(100))
    logPath = Column(String(100))
    excelUploadedOn = Column(String(100))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(100))
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)
