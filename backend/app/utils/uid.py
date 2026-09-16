"""Sequential, human-readable entity identifiers: ``<PREFIX>26<5-digit seq>``
(e.g. ``CONF2610001``). Replaces the old ``uuid4().hex`` UIDs.

The running counter per prefix lives in the ``uid_sequence`` table so every
insert path shares one source of truth - the ORM ``before_insert`` hooks in
``app/models/uid_events.py``, seed scripts, and the one-off
``scripts/migrate_uids.py``.
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection

YEAR = "26"
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
    return f"{prefix}{YEAR}{seq:05d}"
