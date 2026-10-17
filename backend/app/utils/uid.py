"""Sequential, human-readable entity identifiers: ``<PREFIX><YY><5-digit seq>``
(e.g. ``TRN2610001``, YY = the current year in IST). Replaces the old ``uuid4().hex`` UIDs.
Trainings take it too (``CONF2610001``), skipping numbers already taken (app/utils/conference_id.py).

Assessment answers and results follow the other system's style instead (user, 2026-10-16):
``<KIND><YYMMDD><4-digit count>`` - ``next_daily_uid``.

The running counter per prefix lives in the ``uid_sequence`` table so every
insert path shares one source of truth - the ORM ``before_insert`` hooks in
``app/models/uid_events.py``, seed scripts, and the one-off
``scripts/migrate_uids.py``.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.utils.date_utils import ist_now

START = 10001

# MySQL in every real database; SQLite in the test suite's in-memory ones.
_UPSERT_MYSQL = (
    "INSERT INTO uid_sequence (prefix, next_val) VALUES (:p, :after) ON DUPLICATE KEY UPDATE next_val = next_val + 1"
)
_UPSERT_SQLITE = (
    "INSERT INTO uid_sequence (prefix, next_val) VALUES (:p, :after) ON CONFLICT (prefix) DO UPDATE SET next_val = next_val + 1"
)


def _claim(connection: Connection, key: str, first: int) -> int:
    """Atomically takes the next number of the counter ``key`` (``first`` for a new counter). Must run
    inside a transaction: the upsert takes the row lock that serialises concurrent inserts.
    ``connection`` is the Core connection SQLAlchemy passes to ``before_insert`` events (in scripts,
    ``engine.begin()``)."""
    upsert = _UPSERT_SQLITE if connection.dialect.name == "sqlite" else _UPSERT_MYSQL
    connection.execute(text(upsert), {"p": key, "after": first + 1})
    return connection.execute(text("SELECT next_val - 1 FROM uid_sequence WHERE prefix = :p"), {"p": key}).scalar()


def next_uid(connection: Connection, prefix: str) -> str:
    """Atomically claim the next UID for ``prefix``."""
    return f"{prefix}{ist_now().year % 100:02d}{_claim(connection, prefix, START):05d}"


def next_daily_uid(connection: Connection, kind: str) -> str:
    """The next ``<KIND><YYMMDD><count>`` ID, e.g. ``SUB2610160007`` - the other system's style for
    assessment answers and results (SUB = a test or survey, LIVE = the Live Quiz). The count starts
    at 0001 each IST day, from its own counter (``<KIND><YYMMDD>``, at most 10 characters), so no two
    rows share an ID; it only grows past four digits after 9,999 in one day."""
    day = f"{kind}{ist_now():%y%m%d}"
    return f"{day}{_claim(connection, day, 1):04d}"
