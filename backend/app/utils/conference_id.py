"""Public training (conference) IDs: ``CONF`` + YY + CC + TT + RRRR, e.g. ``CONF2698735081``.

  YY    the year the training was created (IST)
  CC    an opaque 2-digit company code  - a keyed hash (HMAC-SHA256 with a key derived from the
        server secret) of the company name, reduced to 00-99. Not the company's database id, and
        not reversible: without the secret nobody can compute or list the codes, and many
        companies share each code.
  TT    an opaque 2-digit trainer code - the same, for the assigned trainer's username.
  RRRR  4 random digits from a cryptographically secure source (`secrets`).

Collision strategy: a candidate is only used if no training in this database already has it -
checked inside the inserting transaction; on a clash another RRRR is drawn. With 4 random digits a
trainer has 10,000 IDs per company per year (a 2-digit tail would allow only 100 and start
clashing after about a dozen trainings), so a redraw is rare even for the busiest trainer.

The ID is an identifier, never a credential: knowing it grants nothing. Joining a training needs
the signed join code (app/utils/join_code.py), and every other use of the ID is authorized
separately. It is what other tables store to refer to a training (attendance, results, logs,
media file names), so it never changes once assigned; the table's own integer `id` stays the
internal primary key.
"""

import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.engine import Connection

from app.core.config import settings
from app.models.conference import Conference
from app.utils.date_utils import ist_now

PREFIX = "CONF"
RANDOM_DIGITS = 4
MAX_ATTEMPTS = 25

# Domain-separated key: the server secret is never used directly for this purpose.
_KEY = hmac.new(settings.SECRET_KEY.encode(), b"samsungindia/conference-id/v1", hashlib.sha256).digest()


def opaque_code(kind: str, value: str | None) -> str:
    """A stable, non-reversible 2-digit code for a company or trainer name."""
    normalized = (value or "").strip().lower()
    digest = hmac.new(_KEY, f"{kind}|{normalized}".encode(), hashlib.sha256).digest()
    return f"{int.from_bytes(digest[:8], 'big') % 100:02d}"


def candidate(company: str | None, trainer: str | None) -> str:
    year = f"{ist_now().year % 100:02d}"
    tail = f"{secrets.randbelow(10 ** RANDOM_DIGITS):0{RANDOM_DIGITS}d}"
    return f"{PREFIX}{year}{opaque_code('company', company)}{opaque_code('trainer', trainer)}{tail}"


def new_conference_uid(connection: Connection, company: str | None, trainer: str | None) -> str:
    """A fresh ID no training in this database has - see the module docstring."""
    table = Conference.__table__
    for _ in range(MAX_ATTEMPTS):
        uid = candidate(company, trainer)
        taken = connection.execute(select(table.c.id).where(table.c.conferenceUid == uid).limit(1)).first()
        if taken is None:
            return uid
    raise RuntimeError("Could not allocate a free training ID")
