from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    # bcrypt's default cost (12 rounds) is fine on normal hardware but takes
    # ~2s on the free/starter-tier CPU this API currently runs on - the
    # rounds are stored in the hash itself, so only NEW hashes made from
    # here on get the faster cost; verify_password on an existing hash keeps
    # using whatever it was created with. 10 rounds is still a widely-used,
    # safe default and this endpoint is already rate-limited (see
    # app/core/rate_limit.py) against brute-forcing the smaller gap it opens.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(
    subject: str,
    tenant_id: Optional[str] = None,
    role: Optional[str] = None,
    version: int = 0,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "tenant_id": tenant_id or settings.DEFAULT_TENANT_ID,
        # The account's tokenVersion when issued - see is_token_current.
        "ver": int(version or 0),
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def is_token_current(payload: dict, account) -> bool:
    """False once the account's tokens were revoked (its tokenVersion bumped past the token's
    `ver`). A token issued before versions existed carries no `ver` and counts as 0, so it stays
    valid until that account's first revocation - nobody is signed out by the rollout itself."""
    try:
        issued = int(payload.get("ver") or 0)
    except (TypeError, ValueError):
        return False
    return issued == int(getattr(account, "tokenVersion", 0) or 0)
