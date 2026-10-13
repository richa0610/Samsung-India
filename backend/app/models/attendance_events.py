"""Who / when / how an attendance row last changed - stamped on every insert and every real update,
whichever path wrote it (QR join, the session screen, check-in, a trainer's mark or unlock, a
proctoring lock, check-out):

    updationOn  when (UTC)
    token       a one-way fingerprint of the login token the change was made with - never the token
    logPath     the request that made it, e.g. "POST /attendance/check-in/secure"

The same fingerprint and request line the activity log records (core/request_context). Outside a
request (a script) `token` and `logPath` are left as they were.

Imported for its side effects by ``app/models/__init__.py``.
"""

from sqlalchemy import event
from sqlalchemy.orm import object_session

from app.models.attendance import Attendance
from app.utils.date_utils import utc_now


def _stamp(target: Attendance) -> None:
    # Local import: request_context imports the database layer, which imports these models.
    from app.core.request_context import request_trace

    target.updationOn = utc_now()
    for column, value in request_trace().items():
        setattr(target, column, value)


@event.listens_for(Attendance, "before_insert")
def _stamp_new_row(mapper, connection, target: Attendance) -> None:
    _stamp(target)


@event.listens_for(Attendance, "before_update")
def _stamp_changed_row(mapper, connection, target: Attendance) -> None:
    # SQLAlchemy calls this for every "dirty" row, even one with no real column change - only a
    # real change is stamped, so loading or re-saving a row untouched never rewrites it.
    session = object_session(target)
    if session is not None and session.is_modified(target, include_collections=False):
        _stamp(target)
