from sqlalchemy import Column, Integer, String

from app.database.connection import CommonBase


class CommonUidSequence(CommonBase):
    """The shared Common Database's ``uid_sequence``: the counters behind IDs that must never repeat
    across companies - a trainee's (user, 2026-10-19; services/user_registry_service). The same table
    and columns as each company's own ``uid_sequence`` (models/uid_sequence.py), so the same
    ``app/utils/uid.py`` functions run against either; a deployment whose company database is the
    Common Database simply shares the one table."""

    __tablename__ = "uid_sequence"

    prefix = Column(String(10), primary_key=True)
    next_val = Column(Integer, nullable=False, default=10001)
