"""Public training (conference) IDs, in the other system's shape (user, 2026-10-17): ``CONF`` + YY + a
5-digit running number, e.g. ``CONF2610001`` - the same counter every other table's ID takes
(app/utils/uid.py ``next_uid``), so two trainings never get the same one. Replaces the earlier
14-character ID (CONF + YY + keyed-hash codes + random digits); IDs already given never change.

A number some training already has is skipped: rows imported from the other system carry its own
CONF + YY + 5-digit IDs, which the counter would otherwise run into.

The ID is an identifier, never a credential: knowing it - or guessing the next one - grants nothing.
Joining a training needs the signed join code (app/utils/join_code.py), and every other use of the ID
is authorized separately. It is what other tables store to refer to a training (attendance, results,
logs, media file names), so it never changes once assigned; the table's own integer `id` stays the
internal primary key.
"""

from sqlalchemy import select
from sqlalchemy.engine import Connection

from app.models.conference import Conference
from app.utils.uid import next_uid

PREFIX = "CONF"
MAX_SKIPS = 1000


def new_conference_uid(connection: Connection) -> str:
    """The next training ID no training in this database has yet."""
    table = Conference.__table__
    for _ in range(MAX_SKIPS):
        uid = next_uid(connection, PREFIX)
        taken = connection.execute(select(table.c.id).where(table.c.conferenceUid == uid).limit(1)).first()
        if taken is None:
            return uid
    raise RuntimeError("Could not allocate a free training ID")
