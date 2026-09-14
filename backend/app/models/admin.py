from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import CommonBase


class Admin(CommonBase):
    """Mirrors the real `admin` table (mmtbtwob_tops). Shared by admin and
    trainer accounts, distinguished by `role` - only `role="trainer"`
    accounts can sign into the trainer dashboard today; `role="admin"`
    rows are stored for a future admin panel."""

    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)

    adminUid = Column(String(100), unique=True, nullable=False)

    name = Column(String(100))
    email = Column(String(255))
    phone = Column(BigInteger)
    altPhone = Column(BigInteger)
    gender = Column(String(50))
    dob = Column(String(50))
    fatherName = Column(String(180))
    motherName = Column(String(180))

    # ─── Trainer Profile screen (src/components/trainer/profile) ──────────
    localCity = Column(String(180))
    localDistrict = Column(String(180))
    localState = Column(String(180))
    localPinCode = Column(String(180))
    localLandmark = Column(String(180))
    permanentCity = Column(String(180))
    permanentDistrict = Column(String(180))
    permanentState = Column(String(180))
    permanentPinCode = Column(String(180))
    permanentLandmark = Column(String(180))

    aadharNo = Column(String(100))
    aadharImage = Column(String(300))
    profilePhoto = Column(String(100))
    about = Column(Text)
    resume = Column(String(300))
    otherDocument = Column(String(300))

    facebook = Column(String(300), server_default=text("'https://facebook.com/'"))
    twitter = Column(String(300), server_default=text("'https://twitter.com/'"))
    instagram = Column(String(300), server_default=text("'https://instagram.com/'"))
    linkedin = Column(String(300), server_default=text("'https://www.linkedin.com/company/'"))
    youtube = Column(String(300), server_default=text("'https://www.youtube.com/'"))
    github = Column(String(100))

    jobStatus = Column(String(100), nullable=False, server_default=text("'Pending'"))
    joinedOn = Column(String(100))
    company = Column(String(100))
    band = Column(String(50))
    reportingManager = Column(String(100))
    postedIn = Column(String(100))
    designation = Column(String(100))
    salary = Column(String(100))
    companyEmail = Column(String(100))
    visitingCard = Column(String(100), nullable=False, server_default=text("'No'"))
    idCard = Column(String(100), nullable=False, server_default=text("'No'"))
    offerLetter = Column(String(100), nullable=False, server_default=text("'No'"))
    letterHead = Column(String(100), nullable=False, server_default=text("'No'"))
    promoCode = Column(String(100), nullable=False, server_default=text("'No'"))

    username = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    access = Column(Text)

    updatedBy = Column(String(100))
    updationOn = Column(DateTime)
    status = Column(String(100), nullable=False, server_default=text("'Pending'"))
    remarks = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
