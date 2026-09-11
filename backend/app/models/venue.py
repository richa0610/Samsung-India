from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class Venue(Base):
    """Mirrors the `venue` table from mmtbtwob_tops — full hotel/training-venue
    management record including geo-coordinates, banking details, GST info,
    images, and document attachments."""

    __tablename__ = "venue"

    id = Column(Integer, primary_key=True, index=True)
    venueUid = Column(String(100), unique=True)

    # Organisational context
    zone = Column(String(50))
    region = Column(String(50))
    company = Column(String(100))

    # Contact
    name = Column(String(100))
    email = Column(String(100))
    phone = Column(BigInteger)

    # Location
    city = Column(String(100))
    district = Column(String(100))
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    # Set once a trainer corrects this venue's coordinates via the "you're
    # not at the venue, update its location?" prompt at session start (see
    # _resolve_start_geofence). After that the location is treated as
    # confirmed and can't be corrected again through that flow - only a
    # genuinely wrong value edited directly (e.g. by an admin) changes it
    # from here. 0 = never overridden yet.
    geoLocationLocked = Column(Integer, nullable=False, server_default=text("0"))
    state = Column(String(100))
    pincode = Column(String(100))
    map = Column(Text)

    # Contact person
    contactPersonName = Column(String(100))
    contactPersonPhone = Column(BigInteger)

    # Venue details
    venueType = Column(String(100))
    tariff = Column(String(50))
    tax = Column(String(50))
    commission = Column(String(100))

    # Banking
    bankName = Column(String(100))
    ifsc = Column(String(100))
    bankAccountNo = Column(String(100))
    bankHolderName = Column(String(100))
    upi = Column(String(100))
    hotelQR = Column(String(250))

    # GST details
    registeredName = Column(String(100))
    GSTNumber = Column(String(50))
    GSTPhone = Column(BigInteger)
    GSTEmail = Column(String(100))
    GSTAddress = Column(Text)

    # Images (up to 6)
    image1 = Column(String(250))
    image2 = Column(String(250))
    image3 = Column(String(250))
    image4 = Column(String(250))
    image5 = Column(String(250))
    image6 = Column(String(250))

    # Documents
    brochure = Column(String(300))
    gstCertificate = Column(String(300))
    addressProof = Column(String(300))
    MSMECertificate = Column(String(300))
    fssaiCertificate = Column(String(300))
    additionalDocs = Column(String(300))

    # Auth
    username = Column(String(100))
    password = Column(String(100))

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
    contractExpired = Column(Date)
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)
