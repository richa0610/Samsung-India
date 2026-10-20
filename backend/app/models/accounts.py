from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class Accounts(Base):
    """Mirrors the `accounts` table from mmtbtwob_tops — venue/account payment
    records for training events. Links a training session (via trainingUid) to
    a venue and records full payment + attendance sheet data."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    accountsUid = Column(String(100), unique=True)

    # Venue details
    venueName = Column(String(100))
    venueEmail = Column(String(100))
    venuePhone = Column(BigInteger)
    venueAddress = Column(Text)

    # Contact person
    contactPersonName = Column(String(100))
    contactPersonPhone = Column(BigInteger)

    # Zone head
    zoneHeadName = Column(String(100))
    zoneHeadEmail = Column(String(100))
    zoneHeadPhone = Column(BigInteger)

    # Trainer
    trainerEmployeeId = Column(String(100))
    trainerName = Column(String(100))
    trainerEmail = Column(String(100))
    trainerPhone = Column(BigInteger)

    # Training link
    trainingUid = Column(String(100))
    trainingDate = Column(String(100))
    state = Column(String(100))
    city = Column(String(100))
    trainingHub = Column(String(100))
    batchSize = Column(String(50))
    confirmedPax = Column(String(50))

    # Payment
    tariff = Column(String(50))
    tax = Column(String(50))
    total = Column(String(50))
    totalPaid = Column(String(50))
    dueAmount = Column(String(50))
    referenceNumber = Column(String(100))
    dateOfPayment = Column(String(100))
    dateOfAttendence = Column(String(100))

    # Attachments
    attendenceSheet = Column(String(250))
    venueBill = Column(String(250))
    hotelRemarks = Column(Text)

    # Upload tracking
    filePath = Column(String(100))
    logPath = Column(String(100))
    excelUploadedOn = Column(String(100))

    # Audit / meta
    updatedBy = Column(String(100))
    updationOn = Column(DateTime, onupdate=func.now())
    isRead = Column(String(50), nullable=False, default="No")
    token = Column(String(50))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(50), nullable=False, default="Pending")
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)
