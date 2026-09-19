"""Writes to `logsmaster` - the app's general user activity trail (who did
what, when, from where). See app/models/logs_master.py for the column
repurposing note.

Call `log_activity` after a significant action succeeds. It never raises -
a logging failure must not take down the request that triggered it - so
callers can fire-and-forget it right after their own `db.commit()`.
"""

import logging

from sqlalchemy.orm import Session

from app.models.logs_master import LogsMaster

logger = logging.getLogger("activity_log")


def log_activity(
    db: Session,
    *,
    action: str,
    username: str | None,
    role: str | None = None,
    remarks: str | None = None,
    ip_address: str | None = None,
    status: str = "Success",
) -> None:
    try:
        db.add(
            LogsMaster(
                username=username,
                role=role,
                action=action,
                login_IP=ip_address,
                status=status,
                remarks=remarks,
            )
        )
        db.commit()
    except Exception:
        # Best-effort audit trail - never let a logging failure surface to
        # the user or roll back the action that already succeeded.
        logger.exception("Failed to write activity log for action=%s username=%s", action, username)
        db.rollback()
