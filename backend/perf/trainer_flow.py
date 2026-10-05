"""Trainer Flow benchmark (Phase 6) - the real HTTP endpoints, end to end, on the local perf MySQL.

    PERF_DB_URL=... python -m perf.trainer_flow enrich --db perf_trainer_100k
    PERF_DB_URL=... python -m perf.trainer_flow bench  --db perf_trainer_100k --label before --runs 40
    PERF_DB_URL=... python -m perf.trainer_flow concurrency --db perf_trainer_100k --label before

`enrich` adds what the attendance dataset (perf.generate_data) doesn't fill but the Trainer Flow
filters on: each trainee's assigned trainer / company / zone / region (from the first training they
attended), state and approval status; the partner-agency trainer accounts; a Live Quiz in ~30% of
training flows; a few trainings on today's date. Deterministic (driven by row ids).

`bench` drives the FastAPI app through its TestClient with real trainer / admin / trainee tokens,
so every number includes authentication, authorization, the service code and serialization. The
tenant database is the perf MySQL; the Common DB (accounts, grants, tenant registry) is a second
perf MySQL database. Per case it records:
  - latency p50 / p95 / p99 (warm-up discarded, nearest-rank),
  - SQL statements and pool checkouts (each checkout is one pre-ping round trip),
  - rows fetched (sum of SELECT row counts) and total database time,
  - an estimate for production: p50 + (statements + checkouts) x RTT_MS (the ~42 ms per round trip
    measured from the dev PC to the managed database, see perf/README.md),
  - EXPLAIN ANALYZE of the slowest statement.
`concurrency` runs a mixed trainer workload from 1 / 4 / 8 threads through the same app.

Everything runs on the local container only (perf._safe refuses any other host / database name).
"""

import argparse
import json
import math
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from unittest.mock import patch

from perf import _safe  # noqa: F401,E402 - must come before any `app` import

from sqlalchemy import event, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.models import *  # noqa: E402,F401,F403 - registers every table

TENANT = "PERF"
RTT_MS = 42
STATES = ["Delhi", "Uttar Pradesh", "Karnataka", "Maharashtra", "West Bengal", "Gujarat"]


def pct(values, q):
    values = sorted(values)
    return round(values[max(0, math.ceil(q * len(values)) - 1)], 1) if values else None


# ------------------------------------------------------------------------------------ enrich
def enrich(db_name: str) -> None:
    engine = _safe.perf_engine(db_name)
    today = date.today().isoformat()
    with engine.begin() as conn:
        # Assigned trainer / placement = the training the trainee attended first.
        conn.execute(text("""
            UPDATE trainee t JOIN (
                SELECT a.traineeUid, MIN(a.id) AS first_id FROM attendance a GROUP BY a.traineeUid
            ) f ON f.traineeUid = t.traineeUid
            JOIN attendance a ON a.id = f.first_id
            JOIN conference c ON c.conferenceUid = a.conferenceUid
            SET t.trainerEmployeeId = c.trainerEmployeeId, t.trainerName = c.trainerName,
                t.company = c.company, t.zone = c.zone, t.region = c.region
        """))
        conn.execute(text(f"""
            UPDATE trainee SET
                state = ELT(1 + (id % 6), {", ".join(f"'{s}'" for s in STATES)}),
                status = IF(id % 10 = 0, 'Pending', 'Approved')
        """))
        conn.execute(text("DELETE FROM agencyteam WHERE username LIKE 'T0%'"))
        conn.execute(text("""
            INSERT INTO agencyteam (agencyTeamUid, username, name, role, company, offerId, password, status)
            SELECT CONCAT('AG', c.trainerEmployeeId), c.trainerEmployeeId, MIN(c.trainerName), 'trainer',
                   (SELECT c2.company FROM conference c2 WHERE c2.trainerEmployeeId = c.trainerEmployeeId
                    GROUP BY c2.company ORDER BY COUNT(*) DESC LIMIT 1),
                   CONCAT('OFF', c.trainerEmployeeId), 'x', 'Active'
            FROM conference c GROUP BY c.trainerEmployeeId
        """))
        conn.execute(text("""
            UPDATE conference SET sessionConfig = JSON_OBJECT('liveQuiz', JSON_OBJECT('assessmentSuiteUid',
                CONCAT('QUIZ', LPAD(id % 5, 3, '0')))) WHERE id % 10 < 3
        """))
        conn.execute(text(f"""
            UPDATE conference SET conferenceDate = '{today}',
                conferenceStatus = IF(id % 2 = 0, 'Scheduled', 'Ongoing'), status = 'Approved'
            WHERE id % 60 = 0
        """))
        for table in ("conference", "trainee", "attendance", "assessment_results", "agencyteam"):
            conn.execute(text(f"ANALYZE TABLE {table}"))
    print("enriched", db_name)


# ------------------------------------------------------------------------------------- world
class World:
    """The app wired to the perf databases (never app.main's own startup database work: TESTING=1)."""

    def __init__(self, db_name: str, pool_size: int = 5, max_overflow: int = 10):
        from app.database.connection import CommonBase
        from app.models.admin import Admin
        from app.models.admin_access import AccessBase, AdminAccess
        from app.models.common.tenant_registry import Tenant

        self.tenant_engine = _safe.perf_engine(db_name, pool_size=pool_size, max_overflow=max_overflow, pool_recycle=280)
        common_name = f"perf_common_{db_name.removeprefix('perf_')}"
        _safe.ensure_database(common_name, drop_first=True)
        self.common_engine = _safe.perf_engine(common_name, pool_size=pool_size, max_overflow=max_overflow, pool_recycle=280)
        CommonBase.metadata.create_all(self.common_engine)
        AccessBase.metadata.create_all(self.common_engine)
        self.CommonSession = sessionmaker(bind=self.common_engine)
        with self.CommonSession() as s:
            s.add(Tenant(tenant_uid=TENANT, company_name="Perf Corp", database_host="h", database_port=3306,
                         database_name=db_name, database_username="u", database_password="p", status="active"))
            sup = Admin(adminUid="a-super", username="super", name="Super", password="x", role="admin")
            coadmin = Admin(adminUid="a-coadmin", username="coadmin", name="Co Admin", password="x", role="admin",
                            company="Samsung India")
            s.add_all([sup, coadmin])
            s.flush()
            s.add(AdminAccess(admin_id=sup.id, role="super_admin", active=1, granted_by="perf"))
            s.add(AdminAccess(admin_id=coadmin.id, role="company_admin", tenant_uid=TENANT, company="Samsung India",
                              active=1, granted_by="perf", company_admin_key=f"{TENANT}|samsung india"))
            s.commit()

        self._patches = [
            patch("app.database.common.CommonSessionLocal", self.CommonSession),
            patch("app.services.proctoring_settings_service.CommonSessionLocal", self.CommonSession),
        ]
        for p in self._patches:
            p.start()
        from fastapi.testclient import TestClient

        from app.database.common import get_common_db
        from app.database.tenant import tenant_manager
        from app.main import app

        tenant_manager.register_engine(TENANT, self.tenant_engine)
        tenant_manager.clear_status_cache()

        def common_db():
            session = self.CommonSession()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_common_db] = common_db
        self.app = app
        self.client_factory = lambda: TestClient(app, raise_server_exceptions=True)

        # ---- measurement hooks. One shared collector: the TestClient runs the app on its own thread,
        # so the sequential benchmark resets it per request (the concurrency run ignores it).
        self.local = type("Collector", (), {})()
        self._lock = threading.Lock()
        for engine in (self.tenant_engine, self.common_engine):
            event.listen(engine, "before_cursor_execute", self._before)
            event.listen(engine, "after_cursor_execute", self._after)
            event.listen(engine.pool, "checkout", self._checkout)

    def _stats(self):
        if not hasattr(self.local, "stmts"):
            self.reset()
        return self.local

    def reset(self):
        self.local.stmts, self.local.checkouts = [], 0

    def _before(self, conn, cursor, statement, params, context, many):
        context._t0 = time.perf_counter()

    def _after(self, conn, cursor, statement, params, context, many):
        rows = cursor.rowcount if statement.lstrip().upper().startswith("SELECT") and cursor.rowcount and cursor.rowcount > 0 else 0
        with self._lock:
                self._stats().stmts.append({"sql": statement, "params": params, "ms": (time.perf_counter() - context._t0) * 1000,
                                        "rows": rows, "db": conn.engine.url.database})

    def _checkout(self, dbapi_conn, record, proxy):
        with self._lock:
            self._stats().checkouts += 1

    def tokens(self):
        from app.core.security import create_access_token

        with self.tenant_engine.connect() as conn:
            trainers = [r[0] for r in conn.execute(text(
                "SELECT trainerEmployeeId FROM conference GROUP BY trainerEmployeeId ORDER BY COUNT(*) DESC LIMIT 20")).all()]
            trainee_phone, trainee_uid = conn.execute(text(
                "SELECT t.phone, t.traineeUid FROM attendance a JOIN trainee t ON t.traineeUid = a.traineeUid "
                "WHERE a.status = 'Present' GROUP BY t.phone, t.traineeUid ORDER BY COUNT(*) DESC LIMIT 1")).one()
        tok = lambda subject, role: {"Authorization": f"Bearer {create_access_token(subject=subject, tenant_id=TENANT, role=role)}"}
        return {
            "trainers": [tok(f"agencyteam:{t}", "trainer") for t in trainers],
            "trainer_ids": trainers,
            "trainer": tok(f"agencyteam:{trainers[0]}", "trainer"),
            "coadmin": tok("admin:coadmin", "admin"),
            "trainee": tok(str(trainee_phone), "trainee"),
            "trainee_uid": trainee_uid,
        }

    def close(self):
        self.app.dependency_overrides.clear()
        for p in self._patches:
            p.stop()


# --------------------------------------------------------------------------------------- bench
def cases(world, t):
    busiest = t["trainer_ids"][0]
    with world.tenant_engine.connect() as conn:
        big_live = conn.execute(text(
            "SELECT c.conferenceUid FROM conference c JOIN attendance a ON a.conferenceUid = c.conferenceUid "
            "WHERE c.trainerEmployeeId = :t AND c.conferenceStatus = 'Ongoing' GROUP BY c.conferenceUid ORDER BY COUNT(*) DESC LIMIT 1"),
            {"t": busiest}).scalar()
        big_done = conn.execute(text(
            "SELECT c.conferenceUid FROM conference c JOIN attendance a ON a.conferenceUid = c.conferenceUid "
            "WHERE c.trainerEmployeeId = :t AND c.conferenceStatus = 'Completed' GROUP BY c.conferenceUid ORDER BY COUNT(*) DESC LIMIT 1"),
            {"t": busiest}).scalar()
    today = date.today().isoformat()
    tr, ad, te = t["trainer"], t["coadmin"], t["trainee"]
    return [
        ("T01 trainer Home (today)", tr, "/admin/trainings/summary"),
        ("T02 trainer Home (month range)", tr, "/admin/trainings/summary?start=2026-09-01&end=2026-09-30"),
        ("T03 Sessions: All, page 1", tr, "/admin/trainings/page?sort=session&limit=20"),
        ("T04 Sessions: All, page 3", tr, "/admin/trainings/page?sort=session&limit=20&page=3"),
        ("T05 Sessions: Today", tr, f"/admin/trainings/page?sort=session&limit=20&on_date={today}"),
        ("T06 Sessions: Completed", tr, "/admin/trainings/page?sort=session&limit=20&status=completed"),
        ("T07 Sessions: search 'CONF00'", tr, "/admin/trainings/page?sort=session&limit=20&q=CONF00"),
        ("T08 Sessions filter options", tr, "/admin/trainings/facets"),
        ("T09 Session dashboard (live, largest)", tr, f"/admin/trainings/{big_live}"),
        ("T10 Session dashboard (completed, largest)", tr, f"/admin/trainings/{big_done}"),
        ("T11 All performers (completed)", tr, f"/admin/trainings/{big_done}/performers"),
        ("T12 Session report (completed)", tr, f"/admin/trainings/{big_done}/report"),
        ("T13 trainer Training List, page 1", tr, "/admin/trainings/page?approval=approved&limit=10"),
        ("T14 trainer Attendance List, page 1", tr, "/admin/attendance/page?mode=all&limit=10"),
        ("T15 trainer Trainee List, page 1", tr, "/admin/trainees/page?mode=all&limit=10"),
        ("T16 Trainer dropdown", tr, "/admin/trainers"),
        ("A01 admin dashboard stats", ad, "/admin/dashboard/stats"),
        ("A02 admin Training List, page 1", ad, "/admin/trainings/page?approval=reviewed&limit=10"),
        ("A03 admin Attendance List, page 1", ad, "/admin/attendance/page?mode=all&limit=10"),
        ("A04 admin Trainee List, page 1", ad, "/admin/trainees/page?mode=all&limit=10"),
        ("R01 trainee Dashboard (Home, 5 rows)", te, "/sessions/dashboard?limit=5"),
        ("R02 trainee Training History (500 rows)", te, "/sessions/dashboard?limit=500"),
        ("R03 trainee current session", te, "/sessions/current"),
        ("R04 trainee Training History, paged (20)", te, "/sessions/trainings?page=1&limit=20"),
        ("R05 trainee Training History, page 3", te, "/sessions/trainings?page=3&limit=20"),
    ]


def bench(db_name: str, label: str, runs: int, warmup: int, only: str, explain: bool, baseline: bool = False) -> None:
    patches = baseline_patches() if baseline else []
    for p in patches:
        p.start()
    world = World(db_name)
    t = world.tokens()
    client = world.client_factory()
    results = []
    selected = [c for c in cases(world, t) if not only or any(c[0].startswith(p) for p in only.split(","))]
    print(f"{'case':44} {'stm':>4} {'ck':>3} {'rows':>7} {'db ms':>7} {'p50':>7} {'p95':>7} {'p99':>7} {'est prod':>9}")
    for name, headers, path in selected:
        for _ in range(warmup):
            assert client.get(path, headers=headers).status_code == 200, (name, client.get(path, headers=headers).text[:200])
        lat, stmts, checkouts, rows, db_ms, per_stmt = [], [], [], [], [], defaultdict(list)
        for _ in range(runs):
            world.reset()
            t0 = time.perf_counter()
            response = client.get(path, headers=headers)
            lat.append((time.perf_counter() - t0) * 1000)
            assert response.status_code == 200, (name, response.status_code)
            s = world.local.stmts
            stmts.append(len(s))
            checkouts.append(world.local.checkouts)
            rows.append(sum(x["rows"] for x in s))
            db_ms.append(sum(x["ms"] for x in s))
            for i, x in enumerate(s):
                per_stmt[i].append(x["ms"])
        last = world.local.stmts
        slowest = max(range(len(last)), key=lambda i: pct(per_stmt[i], 0.5)) if last else None
        plan = None
        if explain and slowest is not None and last[slowest]["sql"].lstrip().upper().startswith("SELECT"):
            engine = world.tenant_engine if last[slowest]["db"] == db_name else world.common_engine
            with engine.connect() as conn:
                plan = "\n".join(r[0] for r in conn.exec_driver_sql("EXPLAIN ANALYZE " + last[slowest]["sql"], last[slowest]["params"]).all())
        entry = {
            "case": name, "path": path, "runs": runs,
            "statements": max(stmts), "checkouts": max(checkouts), "rows_fetched": max(rows),
            "db_ms_p50": pct(db_ms, 0.5), "p50_ms": pct(lat, 0.5), "p95_ms": pct(lat, 0.95), "p99_ms": pct(lat, 0.99),
            "est_production_ms": round(pct(lat, 0.5) + (max(stmts) + max(checkouts)) * RTT_MS),
            "statement_median_ms": [pct(per_stmt[i], 0.5) for i in range(len(last))],
            "statements_sql": [" ".join(x["sql"].split())[:400] for x in last],
            "slowest_statement_plan": plan,
        }
        results.append(entry)
        print(f"{name:44} {entry['statements']:>4} {entry['checkouts']:>3} {entry['rows_fetched']:>7} {entry['db_ms_p50']:>7} "
              f"{entry['p50_ms']:>7} {entry['p95_ms']:>7} {entry['p99_ms']:>7} {entry['est_production_ms']:>9}")
    with world.tenant_engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        pool_mb = int(conn.execute(text("SELECT @@innodb_buffer_pool_size")).scalar()) // 1048576
        counts = {x: conn.execute(text(f"SELECT COUNT(*) FROM {x}")).scalar() for x in ("conference", "attendance", "trainee", "assessment_results")}
    out = {"label": label, "database": db_name, "when": datetime.now().isoformat(timespec="seconds"), "mysql": version,
           "buffer_pool_mb": pool_mb, "rows": counts, "rtt_ms_assumed": RTT_MS, "warmup": warmup, "results": results,
           "method": "FastAPI TestClient, one sequential client on the same machine as MySQL; nearest-rank percentiles"}
    path = f"perf/results/trainer_flow_{label}_{db_name}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print("saved", path)
    world.close()
    for p in patches:
        p.stop()


# --------------------------------------------------------------------------------- concurrency
class _Everything:
    def __contains__(self, item):
        return True


def baseline_patches():
    """The pre-Phase-6 query shapes, for an equal-conditions comparison: the trainer Trainee List's
    OR + EXISTS condition, and the Attendance List without the deferred trainee join."""
    from app.repositories import attendance_repository, dashboard_repository

    original = dashboard_repository.trainee_authorization_conditions
    return [
        patch.object(dashboard_repository, "trainee_authorization_conditions",
                     lambda scope, listing=False: original(scope, listing=False)),
        patch.object(attendance_repository, "_TRAINEE_SORTS", _Everything()),
    ]


def concurrency(db_name: str, label: str, per_thread: int, baseline: bool = False) -> None:
    patches = baseline_patches() if baseline else []
    for p in patches:
        p.start()
    world = World(db_name)
    t = world.tokens()
    today = date.today().isoformat()
    workload = [
        "/admin/trainings/summary", "/admin/trainings/page?sort=session&limit=20",
        f"/admin/trainings/page?sort=session&limit=20&on_date={today}", "/admin/attendance/page?mode=all&limit=10",
        "/admin/trainees/page?mode=all&limit=10", "/admin/trainings/facets",
        "/admin/attendance/page?mode=confirmed&limit=10",
    ]
    out = {"label": label, "database": db_name, "per_thread": per_thread, "levels": []}
    print(f"{'threads':>7} {'requests':>8} {'req/s':>7} {'p50':>7} {'p95':>7} {'p99':>7} {'errors':>6}")
    for threads in (1, 4, 8):
        lat, errors = [], 0
        lock = threading.Lock()

        def worker(n):
            nonlocal errors
            client = world.client_factory()
            headers = t["trainers"][n % len(t["trainers"])]
            for i in range(per_thread):
                path = workload[(n + i) % len(workload)]
                t0 = time.perf_counter()
                status = client.get(path, headers=headers).status_code
                with lock:
                    lat.append((time.perf_counter() - t0) * 1000)
                    errors += status != 200

        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=threads) as pool:
            list(pool.map(worker, range(threads)))
        wall = time.perf_counter() - started
        level = {"threads": threads, "requests": len(lat), "req_per_s": round(len(lat) / wall, 1),
                 "p50_ms": pct(lat, 0.5), "p95_ms": pct(lat, 0.95), "p99_ms": pct(lat, 0.99), "errors": errors}
        out["levels"].append(level)
        print(f"{threads:>7} {level['requests']:>8} {level['req_per_s']:>7} {level['p50_ms']:>7} {level['p95_ms']:>7} {level['p99_ms']:>7} {errors:>6}")
    path = f"perf/results/trainer_flow_concurrency_{label}_{db_name}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("saved", path)
    world.close()
    for p in patches:
        p.stop()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["enrich", "bench", "concurrency"])
    parser.add_argument("--db", required=True)
    parser.add_argument("--label", default="run")
    parser.add_argument("--runs", type=int, default=40)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--only", default="")
    parser.add_argument("--no-explain", action="store_true")
    parser.add_argument("--per-thread", type=int, default=30)
    parser.add_argument("--baseline", action="store_true", help="use the pre-Phase-6 query shapes (bench and concurrency)")
    args = parser.parse_args()
    if args.command == "enrich":
        enrich(args.db)
    elif args.command == "bench":
        bench(args.db, args.label, args.runs, args.warmup, args.only, not args.no_explain, args.baseline)
    else:
        concurrency(args.db, args.label, args.per_thread, args.baseline)


if __name__ == "__main__":
    main()
