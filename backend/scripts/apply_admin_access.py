"""APPLY the reviewed admin_access table and the seed grants (Phase C, step 2 - approved).

    python -m scripts.apply_admin_access --plan scripts/admin_access_plan.samsung.json --confirm-super-admin 1 --yes-apply

Writes to the SHARED database only: runs docs/admin_access_table.sql (one new table) and inserts
the planned grants in a single transaction. Refuses to run if the table already exists, if the plan
has blockers, or without --yes-apply. Enforcement is NOT enabled by this: nothing reads the table yet.
"""

import argparse
import re
import sys
from pathlib import Path

from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database.connection import build_connect_args
from app.models.common.tenant_registry import Tenant
from scripts.seed_admin_access import _engine as _read_only_engine
from app.services.access_seeding import build_plan, load_assignments, render_report

DDL = Path(__file__).resolve().parents[2] / "docs" / "admin_access_table.sql"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--confirm-super-admin", type=int, action="append", default=[])
    p.add_argument("--yes-apply", action="store_true")
    args = p.parse_args()
    if not args.yes_apply:
        print("refusing: pass --yes-apply to write", file=sys.stderr)
        return 2

    tenant_uid, assignments = load_assignments(args.plan)
    cfg = (settings.common_db_host, settings.common_db_port, settings.common_db_user, settings.common_db_password, settings.common_db_name)
    ro_common = sessionmaker(bind=_read_only_engine(*cfg))()
    rec = ro_common.query(Tenant).filter(Tenant.tenant_uid == tenant_uid).first()
    ro_tenant = sessionmaker(bind=_read_only_engine(rec.database_host, rec.database_port, rec.database_username, rec.database_password, rec.database_name))()
    plan = build_plan(ro_common, ro_tenant, tenant_uid, assignments, frozenset(args.confirm_super_admin))
    print(render_report(plan))
    if plan.blockers or any(g.status != "planned" for g in plan.grants):
        print("refusing: plan has blockers or held grants", file=sys.stderr)
        return 1

    engine = create_engine(URL.create("mysql+pymysql", username=cfg[2], password=cfg[3], host=cfg[0], port=cfg[1], database=cfg[4]), connect_args=build_connect_args())
    if "admin_access" in inspect(engine).get_table_names():
        print("refusing: admin_access already exists", file=sys.stderr)
        return 1

    ddl = "\n".join(line for line in DDL.read_text(encoding="utf-8").splitlines() if not line.strip().startswith("--"))
    statements = [s.strip() for s in ddl.split(";") if s.strip()]
    assert len(statements) == 2 and statements[0].startswith("CREATE TABLE admin_access"), "unexpected DDL"
    with engine.connect() as conn:
        for s in statements:
            conn.execute(text(s))
        conn.commit()
        for g in plan.grants:
            conn.execute(
                text("INSERT INTO admin_access (admin_id, role, tenant_uid, company, zone, region, active, granted_by, company_admin_key) "
                     "VALUES (:a, :r, :t, :c, :z, :g, 1, 'phase-c-seed', :k)"),
                {"a": g.admin_id, "r": g.role, "t": g.tenant_uid, "c": g.company, "z": g.zone, "g": g.region, "k": g.key},
            )
        conn.commit()
        rows = conn.execute(text("SELECT admin_id, role, tenant_uid, company, zone, region, active, company_admin_key FROM admin_access ORDER BY id")).all()
    print("\nAPPLIED. admin_access now holds %d rows:" % len(rows))
    for r in rows:
        print("  ", tuple(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
