from sqlalchemy import Column, Integer, String

from app.database.connection import Base


class UidSequence(Base):
    """Per-prefix running counter behind ``app/utils/uid.py``'s ``next_uid()``.
    One row per entity prefix (``CONF``, ``TRN``, ...); ``next_val`` is the
    number the *next* generated UID will use."""

    __tablename__ = "uid_sequence"

    prefix = Column(String(10), primary_key=True)
    next_val = Column(Integer, nullable=False, default=10001)
