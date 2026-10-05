"""Phase 6 query experiments on the local perf MySQL (raw SQL; EXPERIMENT ONLY - changes no app code).

    PERF_DB_URL=... python -m perf.phase6_experiments owned   --db perf_trainer_100k
    PERF_DB_URL=... python -m perf.phase6_experiments ranking --db perf_trainer_100k
    PERF_DB_URL=... python -m perf.phase6_experiments indexes --db perf_trainer_100k

owned   - the trainer's "assigned OR on my roster" trainee condition: OR + EXISTS vs IN (UNION)
ranking - the trainee ranking statement's parts, and candidate rewrites
indexes - candidate composite indexes, added in the perf database only, measured, then dropped
"""

import argparse
import math
import time

from perf import _safe  # noqa: F401,E402 - must come before any `app` import

from sqlalchemy import text  # noqa: E402


def pct(values, q):
    values = sorted(values)
    return round(values[max(0, math.ceil(q * len(values)) - 1)], 1)


def timed(conn, sql, params, runs=15, warmup=2):
    for _ in range(warmup):
        conn.execute(text(sql), params).all()
    samples, rows = [], None
    for _ in range(runs):
        t0 = time.perf_counter()
        rows = conn.execute(text(sql), params).all()
        samples.append((time.perf_counter() - t0) * 1000)
    first = rows[0][0] if rows and len(rows[0]) == 1 else len(rows)
    return pct(samples, 0.5), pct(samples, 0.95), first


def plan(conn, sql, params, lines=14):
    out = "\n".join(r[0] for r in conn.execute(text("EXPLAIN ANALYZE " + sql), params).all())
    return "\n".join("    " + ln[:170] for ln in out.splitlines()[:lines])


def busiest(conn):
    return conn.execute(text("SELECT trainerEmployeeId FROM conference GROUP BY trainerEmployeeId ORDER BY COUNT(*) DESC LIMIT 1")).scalar()


def run_owned(engine):
    with engine.connect() as conn:
        p = {"t": busiest(conn)}
        roster = ("SELECT a.traineeUid FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid "
                  "WHERE c.trainerEmployeeId = :t")
        conditions = {
            "current: assigned OR EXISTS(roster)":
                "(t.trainerEmployeeId = :t OR EXISTS (SELECT 1 FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid "
                "WHERE a.traineeUid = t.traineeUid AND c.trainerEmployeeId = :t))",
            "IN (assigned UNION roster)":
                f"t.traineeUid IN (SELECT traineeUid FROM trainee WHERE trainerEmployeeId = :t UNION {roster})",
            "IN (derived: assigned UNION roster)":
                f"t.traineeUid IN (SELECT o.traineeUid FROM (SELECT traineeUid FROM trainee WHERE trainerEmployeeId = :t UNION {roster}) o)",
        }
        print(f"{'variant':44} {'count p50':>10} {'p95':>7} {'page p50':>9} {'p95':>7} {'rows':>6}")
        for name, cond in conditions.items():
            count_sql = f"SELECT count(*) FROM trainee t WHERE {cond}"
            page_sql = f"SELECT t.id, t.traineeUid, t.name FROM trainee t WHERE {cond} ORDER BY t.timestamp DESC, t.id DESC LIMIT 11"
            c50, c95, n = timed(conn, count_sql, p)
            p50, p95, _ = timed(conn, page_sql, p)
            print(f"{name:44} {c50:>10} {c95:>7} {p50:>9} {p95:>7} {n:>6}")
        print("\nplan, IN (derived):\n" + plan(conn, f"SELECT count(*) FROM trainee t WHERE {conditions['IN (derived: assigned UNION roster)']}", p))


def app_sql(query):
    """The app's own SQLAlchemy query, compiled for MySQL with its parameters inlined."""
    from sqlalchemy.dialects import mysql

    return str(query.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))


def run_ranking(engine):
    from sqlalchemy import func, select

    from app.repositories import dashboard_repository as repo

    with engine.connect() as conn:
        ranked = repo._ranked()
        full = app_sql(select(func.count(), func.sum(ranked.c.percent)).select_from(ranked))
        print("whole ranking aggregate:", timed(conn, full, {}, runs=5, warmup=1)[:2])
        print(plan(conn, full, {}, lines=40))
        parts = {
            "population (distinct Present trainees)":
                "SELECT count(*) FROM (SELECT DISTINCT traineeUid FROM attendance WHERE status = 'Present') x",
            "marks (per-trainee sums)": f"SELECT count(*) FROM ({app_sql(select(repo._counted_marks()))}) x",
        }
        for name, sql in parts.items():
            print(f"{name:44}", timed(conn, sql, {}, runs=5, warmup=1)[:2])

        path = "'$.liveQuiz.assessmentSuiteUid'"
        json_hit = (f"(CASE WHEN JSON_VALID(c.sessionConfig) THEN COALESCE(JSON_EXTRACT(c.sessionConfig, {path}) = "
                    f"CAST(JSON_QUOTE(r.assessmentSuiteUid) AS JSON), 0) ELSE 0 END) = 1")
        live = "lower(coalesce(c.conferenceStatus, '')) <> 'cancelled'"
        counted = f"(r.id IS NOT NULL AND {live} AND (r.assessmentSuiteUid = c.postAssessmentUid OR {json_hit}))"
        single_pass = (
            "SELECT a.traineeUid, "
            f"SUM(CASE WHEN {counted} THEN r.totalScore END) AS score, SUM(CASE WHEN {counted} THEN r.maxScore END) AS maximum "
            "FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid "
            "LEFT JOIN assessment_results r ON r.conferenceUid = a.conferenceUid AND r.traineeUid = a.traineeUid AND r.status = 'Submitted' "
            "WHERE a.status = 'Present' GROUP BY a.traineeUid")
        variants = {
            "V1 current (population + marks + EXISTS)": full,
            "V2 single pass from Present attendance": f"SELECT count(*), sum(IF(maximum > 0, score * 1.0E0 / maximum * 100, 0)) FROM ({single_pass}) x",
        }
        print()
        for name, sql in variants.items():
            print(f"{name:44}", timed(conn, sql, {}, runs=7, warmup=1))
        print(plan(conn, variants["V2 single pass from Present attendance"], {}, lines=25))


def run_indexes(engine):
    """Each candidate: measure the statements it targets without it, add it (perf DB only), measure
    again, then drop it - the database is left as it was."""
    from sqlalchemy import func, select

    from app.repositories import dashboard_repository as repo

    ranked = repo._ranked()
    ranking = app_sql(select(func.count(), func.sum(ranked.c.percent)).select_from(ranked))
    with engine.connect() as conn:
        t = busiest(conn)
    attendance_page = (
        "SELECT a.id FROM attendance a JOIN conference c ON c.conferenceUid = a.conferenceUid "
        f"WHERE c.trainerEmployeeId = '{t}' ORDER BY a.timestamp DESC, a.id DESC LIMIT 11")
    candidates = [
        ("attendance (status, traineeUid)", "ALTER TABLE attendance ADD INDEX p6_att_status_trainee (status, traineeUid)",
         "ALTER TABLE attendance DROP INDEX p6_att_status_trainee",
         {"ranking statement": ranking,
          "population only": "SELECT count(*) FROM (SELECT DISTINCT traineeUid FROM attendance WHERE status = 'Present') x"}),
        ("attendance (conferenceUid, timestamp)", "ALTER TABLE attendance ADD INDEX p6_att_conf_ts (conferenceUid, timestamp)",
         "ALTER TABLE attendance DROP INDEX p6_att_conf_ts",
         {"trainer attendance page (sort by timestamp)": attendance_page}),
    ]
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        for name, add, drop, statements in candidates:
            before = {k: timed(conn, sql, {}, runs=7, warmup=1)[:2] for k, sql in statements.items()}
            conn.execute(text(add))
            conn.execute(text("ANALYZE TABLE attendance"))
            after = {k: timed(conn, sql, {}, runs=7, warmup=1)[:2] for k, sql in statements.items()}
            conn.execute(text(drop))
            print(f"\n{name}")
            for k in statements:
                print(f"   {k:44} before p50/p95 {before[k]}  after {after[k]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=["owned", "ranking", "indexes"])
    parser.add_argument("--db", required=True)
    args = parser.parse_args()
    engine = _safe.perf_engine(args.db)
    {"owned": run_owned, "ranking": run_ranking, "indexes": run_indexes}[args.what](engine)


if __name__ == "__main__":
    main()
