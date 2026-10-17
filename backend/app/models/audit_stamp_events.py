"""Who / when / how an `attendance` or `conference` row last changed - stamped on every insert and
every real update, whichever path wrote it (QR join, the session screen, check-in, a trainer's mark or
unlock, a proctoring lock, check-out; creating, editing, starting or ending a training):

    updationOn  when (UTC)
    token       a one-way fingerprint of the login token the change was made with - never the token
    logPath     the request that made it, e.g. "POST /attendance/check-in/secure"

The same fingerprint and request line the activity log records (core/request_context) - the other
system fills both tables' `token` this way too (user, 2026-10-12 / 2026-10-17). Outside a request (a
script) `token` and `logPath` are left as they were.

Imported for its side effects by ``app/models/__init__.py``.
"""

from sqlalchemy import event
from sqlalchemy.orm import object_session

from app.models.attendance import Attendance
from app.models.conference import Conference
from app.utils.date_utils import utc_now

STAMPED_MODELS = (Attendance, Conference)


def _stamp(target) -> None:
    # Local import: request_context imports the database layer, which imports these models.
    from app.core.request_context import request_trace

    target.updationOn = utc_now()
    for column, value in request_trace().items():
        setattr(target, column, value)


def _stamp_new_row(mapper, connection, target) -> None:
    _stamp(target)


def _stamp_changed_row(mapper, connection, target) -> None:
    # SQLAlchemy calls this for every "dirty" row, even one with no real column change - only a
    # real change is stamped, so loading or re-saving a row untouched never rewrites it.
    session = object_session(target)
    if session is not None and session.is_modified(target, include_collections=False):
        _stamp(target)


for _model in STAMPED_MODELS:
    event.listen(_model, "before_insert", _stamp_new_row)
    event.listen(_model, "before_update", _stamp_changed_row)
