"""The `admin` table's own audit columns, written when an admin-table account changes its profile
(Trainer Profile screen: details, photo, Aadhaar) - in the wording the other system that shares this
table already uses (user, 2026-10-16), so the website shows old and new rows the same way:

    securityDetails  "Your browser: Google Chrome 124.0.0.0 -->-- on windows reports -->-- <user agent>
                     -->-- REMOTE_ADDR <caller IP> -->-- 16-10-2026 03:24:21 PM"   (IST)
    masterRemarks    "Admin updated by <name>(<username>), With token <fingerprint> where Keys details
                     are, Now name is: ..., email is: ..., ..., github is: ..."   - the row as saved
    updatedBy / updationOn   the account's username, and when (UTC)

Kept out on purpose: the password hash (only "changed" / "not changed"), the login token (its one-way
fingerprint, as the activity log stores it), and what this server can't truly know - the device's own
LAN address, an IP-to-location lookup (an outside service) and the server's network setup. `remarks`
is never written: it is the note of whoever approved the account.
"""

from typing import Optional

from app.core.request_context import RequestInfo, current_request, token_fingerprint
from app.models.admin import Admin
from app.utils import user_agent
from app.utils.date_utils import ist_now, utc_now

_SEPARATOR = " -->-- "
_STAMP = "%d-%m-%Y %I:%M:%S %p"

# The row's fields the change line lists, in the other system's order and under its column names
# (the password and remarks come between these two groups - see _change_line).
_PROFILE_COLUMNS = (
    "name", "email", "phone", "altPhone", "gender", "dob", "fatherName", "motherName",
    "localCity", "localDistrict", "localState", "localPinCode", "localLandmark",
    "permanentCity", "permanentDistrict", "permanentState", "permanentPinCode", "permanentLandmark",
    "aadharNo", "about", "profilePhoto", "aadharImage", "resume", "otherDocument",
)
_SOCIAL_COLUMNS = ("facebook", "twitter", "instagram", "linkedin", "youtube", "github")


def record_profile_change(account: Admin, *, password_changed: bool = False) -> None:
    """Stamps `account` as just changed by itself through the current request. Not committed - the
    caller saves the row with its change."""
    request = current_request()
    account.securityDetails = _security_details(request)
    account.masterRemarks = _change_line(account, request, password_changed)
    account.updatedBy = account.username
    account.updationOn = utc_now()


def _security_details(request: Optional[RequestInfo]) -> str:
    agent = request.user_agent if request else None
    browser, system = user_agent.describe(agent)
    caller_ip = request.client_ip if request else None
    return _SEPARATOR.join((
        f"Your browser: {browser}",
        f"on {system} reports",
        agent or "",
        f"REMOTE_ADDR {caller_ip or ''}",
        ist_now().strftime(_STAMP),
    ))


def _change_line(account: Admin, request: Optional[RequestInfo], password_changed: bool) -> str:
    token = token_fingerprint(request.token) if request else None
    fields = [(column, getattr(account, column)) for column in _PROFILE_COLUMNS]
    fields += [("password", "changed" if password_changed else "not changed"), ("remarks", account.remarks)]
    fields += [(column, getattr(account, column)) for column in _SOCIAL_COLUMNS]
    details = ", ".join(f"{column} is: {'' if value is None else value}" for column, value in fields)
    actor = f"{account.name or account.username}({account.username})"
    return f"Admin updated by {actor}, With token {token or ''} where Keys details are, Now {details}"
