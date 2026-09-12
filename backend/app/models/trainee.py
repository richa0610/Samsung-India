from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, Text, text
from sqlalchemy.sql import func

from app.database.connection import Base


class Trainee(Base):
    """Mirrors the real `trainee` table (mmtbtwob_tops). Columns are added
    here as the app grows into using them - the real table has more (see
    database_dump.sql / mmtbtwob_tops.sql for the full shape)."""

    __tablename__ = "trainee"

    id = Column(Integer, primary_key=True, index=True)

    traineeUid = Column(String(100), unique=True, nullable=False)

    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(BigInteger, unique=True, nullable=False)

    gender = Column(String(50))
    designation = Column(String(150))
    supervisorName = Column(String(100))

    district = Column(String(100))
    state = Column(String(100))
    profilePhoto = Column(String(255))

    # The real table's employee-ID column is confusingly just named `uid`
    # (not to be confused with `traineeUid`, our app-generated identifier).
    # Mapped here under the more descriptive `employee_id` attribute name.
    employee_id = Column("uid", String(100))

    status = Column(String(100), nullable=False, server_default=text("'Pending'"))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    # ─── Columns used by the admin-side trainee registration/list flow ─────
    zone = Column(String(100))
    region = Column(String(100))
    company = Column(String(100))
    requestedBy = Column(String(100))
    trainerEmployeeId = Column(String(100))
    trainerName = Column(String(100))
    supervisorUid = Column(String(100))
    supervisorDesignation = Column(String(150))
    agencyId = Column(String(150))
    dob = Column(Date)
    address = Column(Text)
    altPhone = Column(String(20))
    altEmail = Column(String(100))
    joinedOn = Column(Date)
    jobStatus = Column(String(50), server_default=text("'Active'"))
    jobCity = Column(String(100))
    jobPincode = Column(String(10))
    resignedOn = Column(Date)
    username = Column(String(100), unique=True)
    password = Column(String(255))
    updatedBy = Column(String(100))
    updationOn = Column(DateTime)
