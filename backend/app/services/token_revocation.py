"""Server-side sign-out: revoking every token issued for one account.

Each account row carries `tokenVersion`, and each token carries the value it was issued with
(`ver`, core/security.py). Bumping the row's value makes every earlier token fail the
`is_token_current` check the auth dependencies already make on each request - no extra query,
no denylist to store or expire. It signs the account out on every device at once; other
accounts are untouched."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.services import device_sessions
from app.services.activity_log_service import log_activity


def revoke_all_tokens(
    account_db: Session, account: Admin | AgencyTeam | Trainee, log_db: Session, ip_address: Optional[str] = None
) -> None:
    """`account_db` is the database the account row lives in (Common DB for an admin-table
    account, the tenant DB otherwise); `log_db` is the tenant DB the activity log lives in."""
    account.tokenVersion = int(account.tokenVersion or 0) + 1
    account_db.commit()
    _log_logout(log_db, account, ip_address)


def sign_out(
    account_db: Session,
    account: Admin | AgencyTeam | Trainee,
    log_db: Session,
    common_db: Session,
    session_id: Optional[str],
    ip_address: Optional[str] = None,
) -> None:
    """Logout. A token naming its device's session (services/device_sessions) signs out that device
    only (user, 2026-10-19); one from before devices were tracked - or an admin-table account's, which
    has none - revokes every token of the account, as before."""
    if session_id:
        device_sessions.end(common_db, session_id)
        _log_logout(log_db, account, ip_address)
    else:
        revoke_all_tokens(account_db, account, log_db, ip_address)


def _log_logout(log_db: Session, account: Admin | AgencyTeam | Trainee, ip_address: Optional[str]) -> None:
    username = str(account.phone) if isinstance(account, Trainee) else account.username
    role = "trainee" if isinstance(account, Trainee) else account.role
    log_activity(log_db, action="LOGOUT", username=username, role=role, ip_address=ip_address, ends_session=True)
