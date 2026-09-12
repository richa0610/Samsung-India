from sqlalchemy import BigInteger, Column, Integer, String

from app.database.connection import Base


class AgencyTeam(Base):
    """Mirrors the real `agencyteam` table (mmtbtwob_tops). This is the
    org-authoritative table for real trainers (as opposed to `admin`,
    which is only meant for the internal admin panel) - trainer login
    checks `admin` first, then falls back here.

    Unlike `admin`, this table has no Aadhar/documents/social-media/
    salary/etc. columns - the Trainer Profile screen (GET/PATCH
    /admin/profile) only reads/writes the subset that actually exists
    here for an AgencyTeam-backed login."""

    __tablename__ = "agencyteam"

    id = Column(Integer, primary_key=True, index=True)

    agencyTeamUid = Column(String(100), unique=True, nullable=True)
    companyUid = Column(String(100))
    company = Column(String(150))

    name = Column(String(100))
    email = Column(String(100))
    phone = Column(BigInteger)
    altPhone = Column(BigInteger)
    officialEmail = Column(String(100))
    dob = Column(String(50))
    gender = Column(String(50))

    # The trainer's employee ID - the login screen's "Company ID / Phone No"
    # field should accept this as well as `username` (the phone number).
    offerId = Column(String(100), nullable=True, index=True)

    designation = Column(String(100))
    jobCity = Column(String(100))
    jobState = Column(String(100))
    jobPincode = Column(String(50))
    profilePhoto = Column(String(250))

    username = Column(String(100), unique=True, nullable=True, index=True)
    password = Column(String(100), nullable=False)
    role = Column(String(100))
    status = Column(String(50), nullable=False, default="Pending")
