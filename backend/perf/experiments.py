"""Stand-alone experiments on the local perf MySQL (raw SQL, EXPERIMENT ONLY - no app code is changed).

    PERF_DB_URL=... python -m perf.experiments count   --db perf_attendance_100k
    PERF_DB_URL=... python -m perf.experiments write   --db perf_attendance_100k
    PERF_DB_URL=... python -m perf.experiments search  --db perf_attendance_100k

count  - the page's total-count statement with and without its LEFT JOIN trainee
write  - insert cost of attendance rows with vs without the candidate timestamp index
search - contains (%term%) vs prefix vs FULLTEXT(ngram) on the trainee table
"""

import argparse
import math
import time

from perf import _safe  # noqa: F401,E402 - must come before any `app` import

from sqlalchemy import text  # noqa: E402


def pct(values, q):
    values = sorted(values)
    return values[max(0, math.ceil(q * len(values)) - 1)]


def timed(conn, sql, runs=50, warmup=3, params=None):
    for _ in range(warmup):
        conn.execute(text(sql), params or {}).all()
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        rows = conn.execute(text(sql), params or {}).all()
        samples.append((time.perf_counter() - t0) * 1000)
    return {"p50": round(pct(samples, 0.5), 1), "p95": round(pct(samples, 0.95), 1), "p99": round(pct(samples, 0.99), 1), "rows": rows[0][0] if rows and len(rows[0]) == 1 else len(rows)}


def explain(conn, sql, params=None, lines=9):
    plan = "\n".join(r[0] for r in conn.execute(text("EXPLAIN ANALYZE " + sql), params or {}).all())
    return "\n".join("     " + ln.rstrip()[:165] for ln in plan.splitlines()[:lines])


SCOPE = "lower(trim(coalesce(c.company,''))) = 'samsung india'"


def run_count(engine):
    variants = {
        "current: attendance JOIN conference LEFT JOIN trainee": f"SELECT count(*) FROM (SELECT a.id FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid LEFT JOIN trainee t ON t.traineeUid = a.traineeUid WHERE {SCOPE}) x",
        "no trainee join (when the search does not use trainee columns)": f"SELECT count(*) FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid WHERE {SCOPE}",
        "no trainee join, mode=pending": f"SELECT count(*) FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid WHERE {SCOPE} AND (a.status IS NULL OR a.status <> 'Present')",
        "no trainee join, mode=confirmed": f"SELECT count(*) FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid WHERE {SCOPE} AND a.status = 'Present'",
        "current, mode=confirmed (with trainee join)": f"SELECT count(*) FROM (SELECT a.id FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid LEFT JOIN trainee t ON t.traineeUid = a.traineeUid WHERE {SCOPE} AND a.status = 'Present') x",
    }
    with engine.connect() as conn:
        print(f"{'variant':66} {'rows':>7} {'p50':>7} {'p95':>7} {'p99':>7}")
        for name, sql in variants.items():
            r = timed(conn, sql)
            print(f"{name:66} {r['rows']:>7} {r['p50']:>7} {r['p95']:>7} {r['p99']:>7}")
        print("\nplan, no trainee join:\n" + explain(conn, variants["no trainee join (when the search does not use trainee columns)"]))


def run_write(engine):
    """Insert cost with vs without ix_attendance_timestamp, on two full-size copies of attendance."""
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        for t in ("attendance_wtest_base", "attendance_wtest_idx"):
            conn.execute(text(f"DROP TABLE IF EXISTS {t}"))
            conn.execute(text(f"CREATE TABLE {t} LIKE attendance"))
            conn.execute(text(f"INSERT INTO {t} SELECT * FROM attendance"))
        conn.execute(text("ALTER TABLE attendance_wtest_base DROP INDEX ix_attendance_timestamp"))  # base = without the candidate
        for t in ("attendance_wtest_base", "attendance_wtest_idx"):
            conn.execute(text(f"ANALYZE TABLE {t}"))
        sizes = {t: conn.execute(text("SELECT ROUND(data_length/1048576,2), ROUND(index_length/1048576,2) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = :t"), {"t": t}).one() for t in ("attendance_wtest_base", "attendance_wtest_idx")}
        print("table size (data MB, index MB):", {k: tuple(map(float, v)) for k, v in sizes.items()})

        def single_inserts(table, n, tag):
            samples = []
            for i in range(n):
                t0 = time.perf_counter()
                conn.execute(text(f"INSERT INTO {table} (attendanceUid, conferenceUid, traineeUid, status, `timestamp`) VALUES (:u, 'CONF0000001', :t, 'Present', NOW())"), {"u": f"W{tag}{i}", "t": f"WTR{tag}{i}"})
                samples.append((time.perf_counter() - t0) * 1000)
            return samples

        print(f"\n{'single-row INSERT (one commit each), 1,000 rows':52} {'p50 ms':>8} {'p95 ms':>8} {'p99 ms':>8} {'total s':>8}")
        for round_no in (1, 2, 3):
            for table in (("attendance_wtest_base", "attendance_wtest_idx") if round_no % 2 else ("attendance_wtest_idx", "attendance_wtest_base")):
                s = single_inserts(table, 1000, f"{table[-4:]}{round_no}")
                print(f"  round {round_no} {table:44} {pct(s,0.5):>8.2f} {pct(s,0.95):>8.2f} {pct(s,0.99):>8.2f} {sum(s)/1000:>8.2f}")

        print("\nbulk insert of 20,000 rows (INSERT ... SELECT):")
        for table in ("attendance_wtest_base", "attendance_wtest_idx"):
            t0 = time.perf_counter()
            conn.execute(text(f"INSERT INTO {table} (attendanceUid, conferenceUid, traineeUid, status, `timestamp`) SELECT CONCAT('B', attendanceUid), conferenceUid, CONCAT('X', traineeUid), status, `timestamp` FROM attendance LIMIT 20000"))
            print(f"  {table:28} {time.perf_counter() - t0:6.2f} s")
        for t in ("attendance_wtest_base", "attendance_wtest_idx"):
            conn.execute(text(f"DROP TABLE {t}"))
        print("scratch tables dropped")


def run_search(engine):
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text("DROP TABLE IF EXISTS trainee_ft"))
        conn.execute(text("CREATE TABLE trainee_ft LIKE trainee"))
        conn.execute(text("INSERT INTO trainee_ft SELECT * FROM trainee"))
        conn.execute(text("ALTER TABLE trainee_ft ADD FULLTEXT INDEX ft_name (name) WITH PARSER ngram"))
        conn.execute(text("ALTER TABLE trainee_ft ADD FULLTEXT INDEX ft_uid (uid) WITH PARSER ngram"))
        conn.execute(text("ANALYZE TABLE trainee_ft"))
        rare = conn.execute(text("SELECT uid FROM trainee ORDER BY id LIMIT 1 OFFSET 4242")).scalar()
        rows = conn.execute(text("SELECT COUNT(*) FROM trainee")).scalar()
        print(f"trainee rows: {rows} | rare employee id: {rare[:9]}...\n")
        cases = [
            ("name contains 'kumar'   (current style: lower(x) LIKE %t%)", "SELECT count(*) FROM trainee WHERE lower(coalesce(name,'')) LIKE :like", {"like": "%kumar%"}),
            ("name PREFIX 'asha k%'   (column LIKE 't%')", "SELECT count(*) FROM trainee WHERE name LIKE :like", {"like": "asha k%"}),
            ("employee id contains    (current style)", "SELECT count(*) FROM trainee WHERE lower(coalesce(uid,'')) LIKE :like", {"like": f"%{rare.lower()}%"}),
            ("employee id PREFIX      (uses the (uid,email) index)", "SELECT count(*) FROM trainee WHERE uid LIKE :like", {"like": f"{rare.lower()}%"}),
            ("name FULLTEXT ngram 'kumar'", "SELECT count(*) FROM trainee_ft WHERE MATCH(name) AGAINST(:t IN BOOLEAN MODE)", {"t": '"kumar"'}),
            ("employee id FULLTEXT ngram", "SELECT count(*) FROM trainee_ft WHERE MATCH(uid) AGAINST(:t IN BOOLEAN MODE)", {"t": f'"{rare}"'}),
        ]
        print(f"{'25,000-row trainee table, one column':62} {'matches':>8} {'p50 ms':>8} {'p95 ms':>8}")
        for name, sql, params in cases:
            r = timed(conn, sql, runs=50, params=params)
            print(f"{name:62} {r['rows']:>8} {r['p50']:>8} {r['p95']:>8}")
        print("\nplan, name PREFIX:\n" + explain(conn, cases[1][1], cases[1][2], 5))
        print("plan, name contains:\n" + explain(conn, cases[0][1], cases[0][2], 5))
        conn.execute(text("DROP TABLE trainee_ft"))
        print("scratch table dropped")


def run_search_rewrite(engine):
    """Same "contains" semantics, evaluated on the SMALL tables first: which conferences and which
    trainees match, then attendance rows whose conference/trainee is in those sets (or whose own
    columns match). Compared with the current shape: 15 expressions evaluated on every joined row."""
    def lk(col, p):  # lower(coalesce(cast(col as char),'')) LIKE p
        return f"lower(coalesce(cast({col} as char),'')) LIKE {p}"

    def current(term):
        p = "concat('%', :t, '%')"
        cols = ["t.name", "t.uid", "coalesce(case when a.phone is not null and a.phone <> 0 then cast(a.phone as char) else cast(t.phone as char) end,'')",
                "c.trainerName", "c.trainerEmployeeId", "c.region", "c.trainingType", "c.sessionType", "c.audience", "c.state", "c.district",
                "a.conferenceUid", "coalesce(a.attendanceUid, concat('', a.id))", "a.status", "c.conferenceDate"]
        cond = " OR ".join(lk(col, p) for col in cols)
        return f"SELECT count(*) FROM attendance a JOIN conference c ON c.conferenceUid=a.conferenceUid LEFT JOIN trainee t ON t.traineeUid=a.traineeUid WHERE {SCOPE} AND ({cond})"

    def rewritten(term):
        p = "concat('%', :t, '%')"
        conf_cols = ["c2.trainerName", "c2.trainerEmployeeId", "c2.region", "c2.trainingType", "c2.sessionType", "c2.audience", "c2.state", "c2.district", "c2.conferenceDate"]
        conf = " OR ".join(lk(col, p) for col in conf_cols)
        trainee = " OR ".join(lk(col, p) for col in ("t2.name", "t2.uid"))
        trainee_phone = lk("t2.phone", p)
        own = " OR ".join(lk(col, p) for col in ("a.conferenceUid", "coalesce(a.attendanceUid, concat('', a.id))", "a.status"))
        own_phone = f"(a.phone is not null and a.phone <> 0 and {lk('a.phone', p)})"
        return (f"SELECT count(*) FROM attendance a JOIN conference c ON c.conferenceUid=a.conferenceUid WHERE {SCOPE} AND ("
                f"a.conferenceUid IN (SELECT c2.conferenceUid FROM conference c2 WHERE {conf}) "
                f"OR a.traineeUid IN (SELECT t2.traineeUid FROM trainee t2 WHERE {trainee}) "
                f"OR ((a.phone is null or a.phone = 0) AND a.traineeUid IN (SELECT t2.traineeUid FROM trainee t2 WHERE {trainee_phone})) "
                f"OR {own} OR {own_phone})")

    with engine.connect() as conn:
        print(f"{'term':16} {'shape':10} {'matches':>8} {'p50 ms':>8} {'p95 ms':>8}")
        for label, term in (("selective (id)", "ho0004242"), ("medium 'kumar'", "kumar"), ("broad 'a'", "a")):
            counts = {}
            for shape, build in (("current", current), ("rewritten", rewritten)):
                r = timed(conn, build(term), runs=20, warmup=2, params={"t": term})
                counts[shape] = r["rows"]
                print(f"{label:16} {shape:10} {r['rows']:>8} {r['p50']:>8} {r['p95']:>8}")
            print(f"{'':16} identical match counts: {counts['current'] == counts['rewritten']}")
        print("\nrewritten plan (selective term):\n" + explain(conn, rewritten("ho0004242"), {"t": "ho0004242"}, 14))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment", choices=("count", "write", "search", "search-rewrite"))
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    engine = _safe.perf_engine(args.db)
    {"count": run_count, "write": run_write, "search": run_search, "search-rewrite": run_search_rewrite}[args.experiment](engine)


if __name__ == "__main__":
    main()
