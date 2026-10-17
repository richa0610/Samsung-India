from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class Booking(Base):
    """Mirrors the `booking` table from mmtbtwob_tops — hotel/venue booking
    records for training events, including payment tracking fields."""

    __tablename__ = "booking"

    id = Column(Integer, primary_key=True, index=True)
    bookingUid = Column(String(100), unique=True)

    # Organisational context
    zone = Column(String(50))
    region = Column(String(50))

    # Stay dates
    checkIn = Column(String(50))
    checkOut = Column(String(50))

    # Requester
    name = Column(String(100))
    email = Column(String(100))
    phone = Column(BigInteger)

    # Venue details
    venueName = Column(String(150))
    venueAddress = Column(Text)
    city = Column(String(100))
    state = Column(String(100))

    # Payment
    tariff = Column(String(100))
    tax = Column(String(100))
    total = Column(String(50))
    totalPaid = Column(String(100))
    dueAmount = Column(String(100))
    referenceNumber = Column(String(100))
    dateOfPayment = Column(String(100))
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
