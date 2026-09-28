"""DRY RUN of the first admin_access grants (Phase C, step 2).

    python -m scripts.seed_admin_access --plan scripts/admin_access_plan.samsung.json
    python -m scripts.seed_admin_access --plan ... --confirm-super-admin 1     # only shows the plan as if 1 were confirmed

Reads both databases (shared + the tenant) through READ-ONLY connections and prints the plan.
There is no option that writes: applying the plan is a separate step that needs its own approval.
"""

import argparse
import sys

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.connection import build_connect_args
from app.models.common.tenant_registry import Tenant
from app.services.access_seeding import build_plan, load_assignments, make_read_only, render_report


def _engine(host, port, user, password, database):
    url = URL.create("mysql+pymysql", username=user, password=password, host=host, port=port, database=database)
    return make_read_only(create_engine(url, connect_args=build_connect_args(), pool_pre_ping=True))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--plan", required=True, help="path to the assignments JSON")
    parser.add_argument("--confirm-super-admin", type=int, action="append", default=[], metavar="ADMIN_ID",
                        help="treat this account's Super Admin as confirmed (only affects the printed plan)")
    args = parser.parse_args()

    tenant_uid, assignments = load_assignments(args.plan)
    common_engine = _engine(settings.common_db_host, settings.common_db_port, settings.common_db_user, settings.common_db_password, settings.common_db_name)
    common = sessionmaker(bind=common_engine)()
    record = common.query(Tenant).filter(Tenant.tenant_uid == tenant_uid).first()
    if record is not None:
        tenant_engine = _engine(record.database_host, record.database_port, record.database_username, record.database_password, record.database_name)
    elif tenant_uid == settings.DEFAULT_TENANT_ID:
        tenant_engine = _engine(settings.DB_HOST, settings.DB_PORT, settings.DB_USER, settings.DB_PASSWORD, settings.DB_NAME)
    else:
        print(f"tenant {tenant_uid!r} is not in the registry and is not the default tenant", file=sys.stderr)
        return 2
    tenant = sessionmaker(bind=tenant_engine)()

    plan = build_plan(common, tenant, tenant_uid, assignments, frozenset(args.confirm_super_admin))
    print(render_report(plan))
    return 1 if plan.blockers else 0


if __name__ == "__main__":
    sys.exit(main())
