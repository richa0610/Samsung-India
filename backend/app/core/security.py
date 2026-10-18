from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    # The cost is settings.BCRYPT_ROUNDS (core/config.py: default 10, allowed 10-14). bcrypt's own
    # default of 12 is fine on normal hardware but takes ~2s on the free/starter-tier CPU this API
    # runs on. The cost is stored in each hash, so only NEW hashes use the configured value;
    # verify_password checks an existing hash with whatever cost it was made with. 10 rounds is
    # still a widely-used, safe default, and login is rate-limited (app/core/rate_limit.py)
    # against brute-forcing the smaller gap it opens.
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    # bcrypt 5 raises - rather than returning False - for a stored value that isn't a bcrypt hash
    # (another system also writes these tables) and for a password over its 72-byte limit; either
    # way the password doesn't match, so a login answers 401 instead of failing with a 500.
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    subject: str,
    tenant_id: str,
    role: Optional[str] = None,
    version: int = 0,
) -> str:
    """A signed session token for `subject` in `tenant_id` - the company the person signed in to;
    there is no default company (user, 2026-10-18)."""
    issued = datetime.now(timezone.utc)
    expire = issued + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": subject,
        # When this login session began - the activity log's loginTime for every action in it.
        "iat": issued,
        "exp": expire,
        "tenant_id": tenant_id,
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
