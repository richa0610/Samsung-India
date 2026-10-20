"""Create (or configure) a single Admin row directly in the Common DB (the
database admin_service.login actually queries). Unlike seed_admin.py, this
does NOT go through SessionLocal (the default *tenant* engine) - Admin is a
CommonBase model, and the tenant DB has no `admin` table at all.

adminUid is set explicitly rather than left to the before_insert UID hook:
that hook calls next_uid(), which writes to `uid_sequence` - a tenant-only
table that doesn't exist in the Common DB, so it would fail there.

Also seeds this admin's identity scope (see app/services/data_scope_service.py):
`company` lives directly on the Admin row (Common DB), but zone assignment
is read from `data_scopes`, which is a per-tenant table - so that part is
written via SessionLocal (the default tenant) instead, matching where
admin_service's scoping helper actually looks for it.

No credentials are hardcoded here - everything is passed on the command
line, so nothing sensitive ever sits committed in this file. Run from
backend/ with:

  venv/Scripts/python.exe scripts/create_single_admin.py \\
      --username admin --password <password> --company Samsung --zone East

--company and --zone are optional; omit either to leave that scope alone
(an admin with no company/zone assigned is unrestricted - see
data_scope_service.apply_identity_scope).
"""

import argparse
import getpass
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database.common import CommonSessionLocal
from app.database.connection import SessionLocal
from app.models.admin import Admin
from app.models.data_scope import DataScope

# Plain, unambiguous words (no look-alikes across the set) for
# --generate-password - easier to read off a screen and type on a phone
# keyboard than a random token, while still unrelated to the account itself.
_WORDS = [
    "amber", "arrow", "birch", "cedar", "coral", "delta", "eagle", "ember",
    "falcon", "forest", "garnet", "harbor", "hazel", "ivory", "jasper", "lotus",
    "maple", "marble", "meadow", "nectar", "olive", "onyx", "opal", "orbit",
    "pearl", "pepper", "quartz", "raven", "river", "saffron", "summit", "tiger",
    "topaz", "valley", "willow", "zephyr",
]


def generate_readable_password() -> str:
    word1, word2 = secrets.SystemRandom().sample(_WORDS, 2)
    number = secrets.randbelow(90) + 10
    return f"{word1.capitalize()}{word2.capitalize()}{number}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--username", required=True, help="Login username (Company ID / phone).")
    parser.add_argument(
        "--password",
        default=None,
        help="Login password to set. Omit to be prompted (hidden input) instead of passing it on the "
        "command line, where it would land in shell history. Only used when creating a new admin, or "
        "rotating an existing one's password with --rotate-password.",
    )
    parser.add_argument(
        "--generate-password",
        action="store_true",
        help="Generate a readable Word+Word+number password (e.g. TigerHarbor42) instead of supplying "
        "--password or being prompted for one - printed once so it can be handed off; not stored anywhere else.",
    )
    parser.add_argument(
        "--rotate-password",
        action="store_true",
        help="If the admin already exists, replace its password (from --password/--generate-password/prompt) "
        "instead of leaving existing credentials untouched.",
    )
    parser.add_argument("--name", default=None, help="Display name (defaults to the username).")
    parser.add_argument("--company", default=None, help="Company to scope this admin to.")
    parser.add_argument("--zone", default=None, help="Zone to scope this admin to.")
    return parser.parse_args()


def resolve_password(args: argparse.Namespace, *, purpose: str) -> str:
    if args.generate_password:
        password = generate_readable_password()
        print(f"Generated password for {purpose}: {password}")
        return password
    if args.password:
        return args.password
    password = getpass.getpass(f"Password for {purpose}: ")
    if not password:
        print("A password is required.", file=sys.stderr)
        sys.exit(1)
    return password


def main() -> None:
    args = parse_args()

    common_db = CommonSessionLocal()
    try:
        admin = common_db.query(Admin).filter(Admin.username == args.username).first()
        if admin:
            if args.rotate_password:
                password = resolve_password(args, purpose=f"admin {args.username!r}")
                admin.password = hash_password(password)
                common_db.commit()
                print(f"Rotated password for {args.username!r}.")
            else:
                print(f"Admin {args.username!r} already exists (role={admin.role!r}) - not touching credentials.")
        else:
            password = resolve_password(args, purpose=f"new admin {args.username!r}")
            admin_uid = f"ADM26{secrets.randbelow(90000) + 10000}"
            admin = Admin(
                adminUid=admin_uid,
                username=args.username,
                password=hash_password(password),
                name=args.name or args.username,
                role="admin",
                status="Approved",
            )
            common_db.add(admin)
            common_db.commit()
            common_db.refresh(admin)
            print(f"Created admin {args.username!r} (adminUid={admin_uid})")

        if args.company and admin.company != args.company:
            admin.company = args.company
            common_db.commit()
            print(f"Set {args.username!r}.company = {args.company!r}")
    finally:
        admin_id = admin.id
        common_db.close()

    if args.zone:
        tenant_db = SessionLocal()
        try:
            existing_scope = (
                tenant_db.query(DataScope)
                .filter(
                    DataScope.table_type == "admin",
                    DataScope.user_id == admin_id,
                    DataScope.scope_type == "zone",
                )
                .first()
            )
            if existing_scope:
                if existing_scope.scope_value == args.zone:
                    print(f"Zone scope for {args.username!r} already set to {args.zone!r} - no change.")
                else:
                    old_value = existing_scope.scope_value
                    existing_scope.scope_value = args.zone
                    tenant_db.commit()
                    print(f"Updated {args.username!r}'s zone: {old_value!r} -> {args.zone!r}")
            else:
                tenant_db.add(DataScope(table_type="admin", user_id=admin_id, scope_type="zone", scope_value=args.zone))
                tenant_db.commit()
                print(f"Scoped {args.username!r} to zone={args.zone!r}")
        finally:
            tenant_db.close()


if __name__ == "__main__":
    main()
