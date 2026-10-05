"""Sequential, human-readable entity identifiers: ``<PREFIX><YY><5-digit seq>``
(e.g. ``TRN2610001``, YY = the current year in IST). Replaces the old ``uuid4().hex`` UIDs.
Trainings don't use this: their public ID is non-sequential (app/utils/conference_id.py).

The running counter per prefix lives in the ``uid_sequence`` table so every
insert path shares one source of truth - the ORM ``before_insert`` hooks in
``app/models/uid_events.py``, seed scripts, and the one-off
``scripts/migrate_uids.py``.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.utils.date_utils import ist_now

START = 10001


def next_uid(connection: Connection, prefix: str) -> str:
    """Atomically claim the next UID for ``prefix``. Must run inside a
    transaction: the upsert takes the row lock that serialises concurrent
    inserts. ``connection`` is the Core connection SQLAlchemy passes to
    ``before_insert`` events (in scripts, ``engine.begin()``)."""
    connection.execute(
        text(
            "INSERT INTO uid_sequence (prefix, next_val) VALUES (:p, :first) "
            "ON DUPLICATE KEY UPDATE next_val = next_val + 1"
        ),
        {"p": prefix, "first": START + 1},
    )
    seq = connection.execute(
        text("SELECT next_val - 1 FROM uid_sequence WHERE prefix = :p"),
        {"p": prefix},
    ).scalar()
    return f"{prefix}{ist_now().year % 100:02d}{seq:05d}"
