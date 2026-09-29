"""Encrypts the tenant registry's database passwords at rest (see app/core/secret_box.py).

    cd backend
    venv/Scripts/python.exe scripts/encrypt_tenant_db_passwords.py            # dry run (default)
    venv/Scripts/python.exe scripts/encrypt_tenant_db_passwords.py --apply    # write

Needs TENANT_SECRETS_KEYS set (the same value the running API will use - set it on Render
FIRST, or the API can't decrypt what this writes). Plaintext rows are encrypted with the first
key; already-encrypted rows are re-encrypted with it (key rotation). Every row is verified to
decrypt back to the same value before anything is written, and the whole run is one
transaction. Prints tenant ids and row states only - never a password.
"""

import argparse
import sys

from sqlalchemy.orm import Session

sys.path.insert(0, ".")
from app.core.secret_box import decrypt_secret, encryption_enabled, is_encrypted, reencrypt_secret  # noqa: E402
from app.models.common.tenant_registry import Tenant  # noqa: E402


def plan(common_db: Session) -> list[tuple[Tenant, str]]:
    """(tenant row, "encrypt" | "re-encrypt") for every registry row."""
    return [(row, "re-encrypt" if is_encrypted(row.database_password) else "encrypt") for row in common_db.query(Tenant)]


def apply(common_db: Session, rows: list[tuple[Tenant, str]]) -> None:
    for tenant, _ in rows:
        original = decrypt_secret(tenant.database_password)
        updated = reencrypt_secret(tenant.database_password)
        if decrypt_secret(updated) != original:  # never write something that won't read back
            raise RuntimeError(f"Verification failed for tenant '{tenant.tenant_uid}' - nothing was written")
        tenant.database_password = updated
    common_db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Encrypt tenant database passwords at rest.")
    parser.add_argument("--apply", action="store_true", help="write the changes (default: dry run)")
    args = parser.parse_args()
    if not encryption_enabled():
        sys.exit("TENANT_SECRETS_KEYS is not set - nothing to encrypt with.")

    from app.database.common import CommonSessionLocal

    common_db = CommonSessionLocal()
    try:
        rows = plan(common_db)
        for tenant, action in rows:
            print(f"{tenant.tenant_uid:30} {action}")
        if args.apply:
            apply(common_db, rows)
            print(f"{len(rows)} row(s) written.")
        else:
            print("dry run only - nothing was written. Re-run with --apply.")
    except Exception:
        common_db.rollback()
        raise
    finally:
        common_db.close()


if __name__ == "__main__":
    main()
