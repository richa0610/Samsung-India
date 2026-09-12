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
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "tenant_id": tenant_id or settings.DEFAULT_TENANT_ID,
    }
    if role:
        payload["role"] = role
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
