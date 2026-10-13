"""Writes to `logsmaster` - the app's general user activity trail (who did
what, when, from where). See app/models/logs_master.py for the column
repurposing note.

Call `log_activity` after a significant action succeeds. It never raises -
a logging failure must not take down the request that triggered it - so
callers can fire-and-forget it right after their own `db.commit()`.

Every column is filled from the action and the request behind it (core/request_context.py):
  login_IP        the caller's IP           updatedBy / updatedOn  who acted, and when (UTC)
  loginTime       when the acting login session began (its token's `iat`; the action itself
                  for one that signs in)     logoutTime  when it ended, on a logout
  token           a one-way fingerprint of that session's token - never the token itself, which
                  would let anyone reading the log act as that user
  filePath        the stored file an upload action wrote
  logPath         the request ("POST /admin/trainings/CONF.../end")
  securityDetails the client's user agent, the token version and the session's expiry
  masterRemarks   the reason the user typed (approve/reject, attendance mark/reset, unlock)
Never written: `password` / `securedPassword` (no password belongs in a log) and
`excelUploadedOn` (the app has no Excel upload).
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.request_context import current_request, token_fingerprint
from app.models.logs_master import LogsMaster
from app.utils.date_utils import utc_now

logger = logging.getLogger("activity_log")

_STAMP = "%Y-%m-%d %H:%M:%S"


def log_activity(
    db: Session,
    *,
    action: str,
    username: str | None,
    role: str | None = None,
    remarks: str | None = None,
    ip_address: str | None = None,
    status: str = "Success",
    reason: str | None = None,
    file_path: str | None = None,
    issued_token: str | None = None,
    ends_session: bool = False,
) -> None:
    """`issued_token`: the token an action that signs someone in (login, self-registration) just
    issued - otherwise the session is the one whose token the request carried. `ends_session`: a
    logout, which stamps logoutTime."""
    try:
        request = current_request()
        token = issued_token or (request.token if request else None)
        claims = _token_claims(token)
        now = utc_now()
        db.add(
            LogsMaster(
                username=username,
                role=role,
                action=action,
                login_IP=ip_address or (request.client_ip if request else None),
                status=status,
                remarks=remarks,
                updatedBy=username,
                updatedOn=now.strftime(_STAMP),
                loginTime=_session_start(claims),
                logoutTime=now.strftime(_STAMP) if ends_session else None,
                token=token_fingerprint(token),
                filePath=_fit(file_path),
                logPath=_fit(request.line) if request else None,
                securityDetails=_security_details(request.user_agent if request else None, claims),
                masterRemarks=reason or None,
            )
        )
        db.commit()
    except Exception:
        # Best-effort audit trail - never let a logging failure surface to
        # the user or roll back the action that already succeeded.
        logger.exception("Failed to write activity log for action=%s username=%s", action, username)
        db.rollback()


def _token_claims(token: str | None) -> dict:
    """The token's own claims (signature checked - the auth dependency has already accepted it).
    Expiry isn't re-checked: a logout's token is logged as it's being revoked."""
    if not token:
        return {}
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
    except JWTError:
        return {}


def _utc(epoch_seconds) -> datetime:
    return datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc).replace(tzinfo=None)


def _session_start(claims: dict) -> str | None:
    """When the session's login happened: the token's `iat`, or - for a token issued before that
    claim existed - its expiry minus the token lifetime."""
    if "iat" in claims:
        return _utc(claims["iat"]).strftime(_STAMP)
    if "exp" in claims:
        return (_utc(claims["exp"]) - timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).strftime(_STAMP)
    return None


def _security_details(user_agent: str | None, claims: dict) -> str | None:
    details = {
        "userAgent": user_agent,
        "tokenVersion": claims.get("ver"),
        "sessionExpires": _utc(claims["exp"]).strftime(_STAMP) if "exp" in claims else None,
    }
    details = {key: value for key, value in details.items() if value is not None}
    return json.dumps(details) if details else None


def _fit(value: str | None, limit: int = 100) -> str | None:
    """These legacy columns are VARCHAR(100): trimmed rather than failing the insert."""
    return value[:limit] if value else None
