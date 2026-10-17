"""Signed join codes for a training's QR code / share link: ``<conferenceUid>.<SIGNATURE>``,
e.g. ``CONF2698735081.K3J9XQ2M7PLA4TZB``.

SIGNATURE = the first 80 bits of HMAC-SHA256(key, "v1|<tenant>|<conferenceUid>"), base32 (16 letters
and digits - safe in a URL, a deep link and a QR code). The key is derived from the server secret
and used for nothing else. Binding the tenant means a code only works in the tenant it was issued
for: sending it with another tenant's header (or a token of another tenant) fails the check, so it
can't reach a training elsewhere. Without the server secret a valid code can't be made, so knowing
or guessing a training's ID is not enough to see or join it.

Codes issued before signing existed were the bare ID. `verify` still accepts one until
settings.JOIN_CODE_LEGACY_UNTIL (IST date, inclusive) so QR codes already shared keep working for a
short while; after that - or with the setting empty - only signed codes are accepted.
"""

import base64
import hashlib
import hmac
from typing import Optional

from app.core.config import settings
from app.utils.date_utils import ist_now

_KEY = hmac.new(settings.SECRET_KEY.encode(), b"samsungindia/join-code/v1", hashlib.sha256).digest()
SEPARATOR = "."
MAX_LENGTH = 120


def _signature(tenant_id: str, conference_uid: str) -> str:
    digest = hmac.new(_KEY, f"v1|{tenant_id.strip().lower()}|{conference_uid}".encode(), hashlib.sha256).digest()
    return base64.b32encode(digest[:10]).decode()  # 80 bits -> 16 characters, no padding


def make(tenant_id: str, conference_uid: str) -> str:
    return f"{conference_uid}{SEPARATOR}{_signature(tenant_id, conference_uid)}"


def legacy_codes_accepted() -> bool:
    until = (settings.JOIN_CODE_LEGACY_UNTIL or "").strip()
    return bool(until) and ist_now().date().isoformat() <= until


def verify(tenant_id: str, code: str) -> Optional[str]:
    """The conferenceUid a join code stands for in this tenant, or None when the code isn't valid
    here (wrong signature, another tenant's code, malformed, or an unsigned code after the grace
    period). Constant-time comparison."""
    code = (code or "").strip()
    if not code or len(code) > MAX_LENGTH:
        return None
    conference_uid, separator, signature = code.rpartition(SEPARATOR)
    if not separator:
        return code if legacy_codes_accepted() else None
    if not conference_uid or not hmac.compare_digest(signature.upper(), _signature(tenant_id, conference_uid)):
        return None
    return conference_uid
