from sqlalchemy import BigInteger, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base

# Deliberately NOT `CommonBase` / `TenantBase` (app/database/connection.py).
#
# `agency` is the other system's table of registered companies, in the shared (Common) database:
# every client company is registered there first (user, 2026-10-14). Startup runs `create_all`
# and the additive column sync on CommonBase / TenantBase against the live databases; on its own
# metadata this table can never be created or altered by a restart.
AgencyBase = declarative_base()


class Agency(AgencyBase):
    """The columns of the existing `agency` table that registering a company fills; the rest keep
    the table's own defaults."""

    __tablename__ = "agency"

    id = Column(Integer, primary_key=True)
    agencyUid = Column(String(100))
    companyName = Column(String(200))
    name = Column(String(100))  # the contact person
    email = Column(String(100))
    phone = Column(BigInteger)
    website = Column(String(200))
    localCity = Column(String(100))
    localDistrict = Column(String(100))
    localState = Column(String(100))
    localPinCode = Column(String(100))
    aboutAgency = Column(Text)
    updatedBy = Column(String(50))
    status = Column(String(100), nullable=False, default="Pending")
    remarks = Column(Text)
