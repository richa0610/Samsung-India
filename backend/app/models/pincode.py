from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Deliberately NOT `CommonBase` / `TenantBase` (app/database/connection.py).
#
# `pincode` is the India Post directory the other system already keeps in the shared (Common)
# database - one row per post office. This app only READS it, for the State / District / Venue
# pickers (services/location_service.py). Startup runs `create_all` and the additive column /
# index sync on CommonBase and TenantBase against the live databases; on its own metadata this
# table can never be created, altered or indexed by a restart. tests/test_locations.py pins that.
PincodeBase = declarative_base()


class Pincode(PincodeBase):
    """The columns of the existing `pincode` table the pickers read; the rest stay unmapped."""

    __tablename__ = "pincode"

    id = Column(Integer, primary_key=True)
    pincode = Column(String(100))
    district = Column(String(100))
    stateName = Column(String(100))
