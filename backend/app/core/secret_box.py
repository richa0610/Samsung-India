"""Encryption at rest for secrets stored in the database - today the tenant registry's
`database_password` (Common DB `tenants` table), so reading the Common DB (a backup, a leaked
dump, a SQL injection) no longer yields every tenant database's credentials.

Keys come from settings.TENANT_SECRETS_KEYS - comma-separated Fernet keys, never stored in the
database. The FIRST key encrypts; every listed key can decrypt, so a key is rotated by putting
the new one first and keeping the old one until scripts/encrypt_tenant_db_passwords.py has
re-encrypted every row. Generate a key with:

    venv/Scripts/python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Stored values are tagged "enc:v1:..."; an untagged value is a not-yet-migrated plaintext row and
is used as-is, so turning this on never breaks an existing tenant. Nothing here ever logs a
secret or includes one in an exception message."""

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.core.config import settings

ENCRYPTED_PREFIX = "enc:v1:"


class SecretUnavailable(Exception):
    """An encrypted value can't be decrypted (no key configured, or none of the keys match)."""


def _keys() -> list[str]:
    return [key.strip() for key in (settings.TENANT_SECRETS_KEYS or "").split(",") if key.strip()]


def encryption_enabled() -> bool:
    return bool(_keys())


def _box() -> MultiFernet:
    keys = _keys()
    if not keys:
        raise SecretUnavailable("No TENANT_SECRETS_KEYS configured")
    try:
        return MultiFernet([Fernet(key.encode()) for key in keys])
    except (ValueError, TypeError):
        raise SecretUnavailable("TENANT_SECRETS_KEYS contains a malformed key") from None


def is_encrypted(value: str | None) -> bool:
    return bool(value) and value.startswith(ENCRYPTED_PREFIX)


def encrypt_secret(plaintext: str) -> str:
    return ENCRYPTED_PREFIX + _box().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(stored: str) -> str:
    """The usable secret for a stored value: decrypted if tagged, as-is if plaintext (legacy)."""
    if not is_encrypted(stored):
        return stored
    try:
        return _box().decrypt(stored[len(ENCRYPTED_PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        raise SecretUnavailable("Stored secret does not match any configured key") from None


def protect_secret(plaintext: str) -> str:
    """What to store for a new secret: encrypted when a key is configured, else plaintext (the
    behaviour before encryption existed - run the migration script once a key is set)."""
    return encrypt_secret(plaintext) if encryption_enabled() else plaintext


def reencrypt_secret(stored: str) -> str:
    """The stored value under the current first key (plaintext rows get encrypted)."""
    return encrypt_secret(decrypt_secret(stored))
