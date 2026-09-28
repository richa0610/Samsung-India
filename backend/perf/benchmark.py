"""Latency + query-plan benchmark of the Phase A attendance page (local perf MySQL only).

    PERF_DB_URL=... python -m perf.benchmark --db perf_attendance_100k --label baseline --runs 60

Calls the real `training_service.list_attendance_page` (so the numbers are for the actual
Phase A SQL), one sequential client, against the local perf database. For every case it records:
  - request latency p50 / p95 / p99 (warm-up runs discarded),
  - SQL statement count and each statement's median time (page / count / results / tallies),
  - MySQL session counters for one run (temp tables, sorts, rows read),
  - EXPLAIN ANALYZE of every statement, captured from the statements actually sent.
There is no network in these numbers (client and MySQL are on the same machine), so they are the
DATABASE time only. Add (statements x round trip) for a remote deployment.
"""

import argparse
import json
import math
import platform
import time
from collections import defaultdict
from datetime import datetime

from perf import _safe  # noqa: F401,E402 - must come before any `app` import

from sqlalchemy import event, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.dependencies.filters import ConferenceFilters  # noqa: E402
from app.services import training_service  # noqa: E402

COUNTERS = (
    "Created_tmp_tables", "Created_tmp_disk_tables", "Sort_rows", "Sort_merge_passes",
    "Handler_read_key", "Handler_read_next", "Handler_read_rnd_next", "Select_scan", "Select_full_join",
)


def classify(statement: str) -> str:
    s = " ".join(statement.split())
    if s.startswith("EXPLAIN"):
        return "explain"
    if "GROUP BY" in s and "count(*)" in s.lower():
        return "tallies"
    if s.lower().startswith("select count(*)") and "FROM (SELECT" in s:
        return "count"
    if "FROM assessment_results" in s:
        return "results"
    if "LIMIT" in s:
        return "page"
    return "other"


def percentile(sorted_values, q):
    if not sorted_values:
        return None
    return sorted_values[max(0, math.ceil(q * len(sorted_values)) - 1)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--runs", type=int, default=60)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--only", default="", help="comma-separated case-name prefixes, e.g. A1,B1,E4")
    parser.add_argument("--no-explain", action="store_true")
    args = parser.parse_args()

    engine = _safe.perf_engine(args.db, pool_size=5)
    Session = sessionmaker(bind=engine)
    captured: list[dict] = []

    @event.listens_for(engine, "before_cursor_execute")
    def _before(conn, cursor, statement, params, context, executemany):
        context._t0 = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def _after(conn, cursor, statement, params, context, executemany):
        captured.append({"label": classify(statement), "ms": (time.perf_counter() - context._t0) * 1000, "sql": statement, "params": params})

    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        pool_mb = int(conn.execute(text("SELECT @@innodb_buffer_pool_size")).scalar()) // 1048576
        counts = {t: conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in ("conference", "attendance", "trainee", "assessment_results")}
        # a very selective search term: an employee id of a trainee who actually has attendance
        rare = conn.execute(text("SELECT t.uid FROM attendance a JOIN trainee t ON t.traineeUid = a.traineeUid ORDER BY a.id LIMIT 1 OFFSET 777")).scalar()
        newest = conn.execute(text("SELECT MAX(conferenceDate) FROM conference")).scalar()
    print(f"database {args.db} | MySQL {version} | buffer pool {pool_mb} MB | rows {counts}")

    broad = ConferenceFilters(company="Samsung India")
    narrow = ConferenceFilters(company="Samsung India", zones=["north zone"], start="2026-08-15", end="2026-09-15")
    everyone = ConferenceFilters()

    def request(filters=broad, mode="all", q=None, sort="markedAt", desc=True, cursor=None, limit=10, page=None):
        return lambda db: training_service.list_attendance_page(db, filters, mode, q, sort, desc, cursor, limit, page)

    def deep_cursor(pages):
        db = Session()
        cursor = None
        for _ in range(pages):
            cursor = training_service.list_attendance_page(db, broad, "all", None, "markedAt", True, cursor, 10, None).nextCursor
        db.close()
        return cursor

    total_rows = None
    db0 = Session()
    first = training_service.list_attendance_page(db0, broad, "all", None, "markedAt", True, None, 10, None)
    total_rows = first.total
    db0.close()
    last_page = math.ceil(total_rows / 10)

    cases = [
        ("A1 page 1, all, default sort (newest first), broad scope", request()),
        ("A2 page 1, pending", request(mode="pending")),
        ("A3 page 1, confirmed", request(mode="confirmed")),
        ("A4 page 1, no company scope (unrestricted admin)", request(everyone)),
        ("B1 sort participantName asc", request(sort="participantName", desc=False)),
        ("B2 sort conferenceDate desc", request(sort="conferenceDate")),
        ("B3 sort attendanceId asc", request(sort="attendanceId", desc=False)),
        ("B4 sort checkOut desc", request(sort="checkOut")),
        ("C1 narrow scope (one zone, one month)", request(narrow)),
        ("D1 search very selective (an employee id)", request(q=rare)),
        ("D2 search medium ('kumar')", request(q="kumar")),
        ("D3 search broad ('a')", request(q="a")),
        ("D4 search id-like ('att000005')", request(q="att000005")),
        ("E1 page 500 (offset 5,000)", request(page=500)),
        ("E2 page 2000 (offset 20,000)", request(page=2000)),
        (f"E3 last page (page {last_page})", request(page=last_page)),
        ("E4 deep cursor (after 200 pages)", request(cursor=deep_cursor(200))),
        ("F1 limit 50", request(limit=50)),
        ("F2 limit 200", request(limit=200)),
    ]
    if args.only:
        wanted = [w.strip().lower() for w in args.only.split(",") if w.strip()]
        cases = [c for c in cases if any(c[0].lower().startswith(w) for w in wanted)]

    results = []
    print(f"\n{'case':58} {'stmts':>5} {'p50':>8} {'p95':>8} {'p99':>8}   per-statement median ms")
    for name, call in cases:
        for _ in range(args.warmup):
            db = Session(); call(db); db.close()
        latencies, per_label, stmt_counts, rows_returned = [], defaultdict(list), [], 0
        for _ in range(args.runs):
            captured.clear()
            t0 = time.perf_counter()
            db = Session()
            response = call(db)
            db.close()
            latencies.append((time.perf_counter() - t0) * 1000)
            rows_returned = len(response.items)
            stmt_counts.append(len([c for c in captured if c["label"] != "explain"]))
            for c in captured:
                per_label[c["label"]].append(c["ms"])
        latencies.sort()
        medians = {k: round(percentile(sorted(v), 0.5), 1) for k, v in per_label.items() if k != "explain"}

        # one more run: session counters + the statements sent, for EXPLAIN ANALYZE
        captured.clear()
        db = Session()
        conn = db.connection()
        before = {r[0]: int(r[1]) for r in conn.execute(text("SHOW SESSION STATUS")).all() if r[0] in COUNTERS}
        captured.clear()
        call(db)
        sent = [c for c in captured if c["label"] not in ("explain", "other")]
        after = {r[0]: int(r[1]) for r in conn.execute(text("SHOW SESSION STATUS")).all() if r[0] in COUNTERS}
        db.close()
        counters = {k: after[k] - before[k] for k in COUNTERS}
        plans = {}
        if not args.no_explain:
            with engine.connect() as c2:
                for s in sent:
                    plan = "\n".join(r[0] for r in c2.exec_driver_sql("EXPLAIN ANALYZE " + s["sql"], s["params"]).all())
                    plans[s["label"]] = plan

        entry = {
            "case": name, "runs": args.runs, "statements": max(stmt_counts), "rows_returned": rows_returned,
            "p50_ms": round(percentile(latencies, 0.5), 1), "p95_ms": round(percentile(latencies, 0.95), 1),
            "p99_ms": round(percentile(latencies, 0.99), 1), "max_ms": round(latencies[-1], 1),
            "statement_median_ms": medians, "session_counters_one_run": counters, "explain_analyze": plans,
        }
        results.append(entry)
        per = " ".join(f"{k}={v}" for k, v in medians.items())
        print(f"{name[:58]:58} {entry['statements']:>5} {entry['p50_ms']:>8} {entry['p95_ms']:>8} {entry['p99_ms']:>8}   {per}")

    out = {
        "label": args.label, "database": args.db, "when": datetime.now().isoformat(timespec="seconds"),
        "mysql_version": version, "innodb_buffer_pool_mb": pool_mb, "table_rows": counts, "matching_rows_broad_scope": total_rows,
        "client": {"python": platform.python_version(), "machine": platform.machine(), "processor": platform.processor()},
        "method": "single sequential client on the same machine as MySQL (no network); warm-up discarded; nearest-rank percentiles",
        "warmup": args.warmup, "results": results,
    }
    path = f"perf/results/bench_{args.label}_{args.db}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"\nsaved {path}")


if __name__ == "__main__":
    main()
