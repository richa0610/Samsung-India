"""READ ONLY - how many trainer accounts still carry the shared default password.

The other system's `agencyteam` table gives `password` a fixed default (NOT NULL DEFAULT '<one
bcrypt hash>'), so every trainer row it - or an import - inserts without a password shares that one
password, and this app signs a trainer in with it like any other. Per tenant, this counts the
accounts whose stored hash is still exactly that default: how many hold the trainer role (so can
sign in here) and how many of those have signed in to this app.

It only reads: each tenant's queries run inside a READ ONLY transaction that is rolled back, the
database is opened without the app's pool or schema sync (scripts/_tenant_db.py), and no hash is
ever printed. Usernames (phone numbers) are listed only with --list.

    cd backend
    venv/Scripts/python.exe scripts/report_default_trainer_passwords.py
    venv/Scripts/python.exe scripts/report_default_trainer_passwords.py --list
"""

import argparse
import sys

from sqlalchemy import text

sys.path.insert(0, ".")
from scripts._tenant_db import tenant_engine  # noqa: E402

DEFAULT_PASSWORD = text(
    "SELECT COLUMN_DEFAULT FROM information_schema.COLUMNS "
    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'agencyteam' AND COLUMN_NAME = 'password'"
)
ON_THE_DEFAULT = text(
    "SELECT a.username, a.role, MAX(l.timestamp) AS last_login FROM agencyteam a "
    "LEFT JOIN logsmaster l ON l.username = a.username AND l.action = 'LOGIN' "
    "WHERE a.password = :default GROUP BY a.id, a.username, a.role ORDER BY a.username"
)


def report_tenant(tenant_id: str, list_accounts: bool) -> None:
    try:
        engine = tenant_engine(tenant_id)
    except Exception as exc:  # suspended / unknown tenant, or its registry row unreadable: say so, go on
        print(f"{tenant_id}: not readable ({exc.__class__.__name__})")
        return
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.exec_driver_sql("START TRANSACTION READ ONLY")
            try:
                default = conn.execute(DEFAULT_PASSWORD).scalar()
                # MySQL reports a string default bare, MariaDB in quotes.
                if default and len(default) > 1 and default[0] == default[-1] == "'":
                    default = default[1:-1]
                rows = conn.execute(ON_THE_DEFAULT, {"default": default}).all() if default else []
            finally:
                conn.exec_driver_sql("ROLLBACK")
    finally:
        engine.dispose()

    if not default:
        print(f"{tenant_id}: agencyteam.password has no default - no account shares one")
        return
    trainers = [row for row in rows if (row.role or "").strip().lower() == "trainer"]
    signed_in = [row for row in trainers if row.last_login]
    print(f"{tenant_id}: {len(rows)} account(s) on the default password - {len(trainers)} with the trainer role "
          f"(can sign in here), {len(signed_in)} of those have signed in to this app")
    if list_accounts:
        for row in rows:
            print(f"    {row.username}  role={row.role or '-'}  last login here: {row.last_login or 'never'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read only: trainer accounts still on the shared default password.")
    parser.add_argument("--list", action="store_true", help="also list those accounts' usernames (phone numbers)")
    args = parser.parse_args()

    from app.core.config import settings
    from app.database.common import CommonSessionLocal
    from app.repositories import tenant_repository

    common_db = CommonSessionLocal()
    try:
        tenants = tenant_repository.list_uids(common_db)
    finally:
        common_db.close()
    if settings.DEFAULT_TENANT_ID not in tenants:
        tenants.append(settings.DEFAULT_TENANT_ID)

    for tenant_id in tenants:
        report_tenant(tenant_id, args.list)
    print("read only - nothing was changed.")


if __name__ == "__main__":
    main()
