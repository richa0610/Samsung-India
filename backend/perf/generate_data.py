"""Synthetic dataset for the attendance performance tests (Phase B).

    PERF_DB_URL=... python -m perf.generate_data --rows 100000 --db perf_attendance_100k

Creates (or, with --drop, recreates) the database, builds the tenant schema from the app's
models, adds the legacy indexes production has but the models don't declare, and loads a
seeded, repeatable dataset. Nothing here is real: names are synthetic word combinations,
contact details use reserved test values, and no production data is read.

Shape (all knobs are constants below, so a run is fully described by --rows and --seed):
  conferences  ~ rows / 30      trainees ~ rows / 4      attendance = --rows
  8 companies (one dominant: ~70% of rows), 4 zones, ~14 regions, 60 trainers (a few very busy),
  attendance status mix 45% Present / 30% Pending / 15% Joined / 10% Absent,
  timestamps skewed to the recent past with minute-level ties,
  post-test results for ~60% of Present/Joined attendees (1-3 attempts).
Limitations: the distributions are invented (real skew will differ), it is a single node with
no concurrent writers, and text fields are shorter/simpler than real free-text.
"""

import argparse
import json
import random
import time
from datetime import date, datetime, timedelta

from perf import _safe  # noqa: F401,E402 - must come before any `app` import

from sqlalchemy import text  # noqa: E402

from app.database.connection import TenantBase  # noqa: E402
from app.models import *  # noqa: E402,F401,F403 - registers every table
from app.models.attendance import Attendance  # noqa: E402
from app.models.conference import Conference  # noqa: E402
from app.models.quiz import AssessmentResult  # noqa: E402
from app.models.trainee import Trainee  # noqa: E402

COMPANIES = [
    ("Samsung India", 0.70), ("Quess Corp", 0.10), ("Acme Retail", 0.08), ("Nova Telecom", 0.06),
    ("Orbit Mobile", 0.03), ("Zenith Stores", 0.02), ("Kite Wireless", 0.005), ("Pixel Hub", 0.005),
]
ZONES = {
    "North Zone": ["North 1", "North 2", "North 3", "Delhi NCR"],
    "South Zone": ["South 1", "South 2", "South 3"],
    "East Zone": ["East 1", "East 2", "East 3"],
    "West Zone": ["West 1", "West 2", "West 3", "Gujarat"],
}
TRAINING_TYPES = ["Webinar", "Classroom Training", "Product Training", "Workshop"]
STATUS_MIX = [("Present", 0.45), ("Pending", 0.30), ("Joined", 0.15), ("Absent", 0.10)]
CONF_STATUS_MIX = [("Completed", 0.55), ("Scheduled", 0.22), ("Ongoing", 0.05), ("Cancelled", 0.08), ("Completed ", 0.10)]
FIRST = ["Asha", "Ravi", "Meera", "Kiran", "Deepa", "Arjun", "Neha", "Rahul", "Priya", "Vikram", "Sana", "Imran", "Anita", "Suresh", "Divya", "Manoj"]
LAST = ["Kumar", "Sharma", "Nair", "Iyer", "Singh", "Verma", "Das", "Reddy", "Khan", "Patel", "Joshi", "Menon"]
STATES = [("Delhi", ["New Delhi", "Noida"]), ("Uttar Pradesh", ["Agra", "Lucknow"]), ("Karnataka", ["Bengaluru", "Mysuru"]), ("Maharashtra", ["Pune", "Mumbai"]), ("West Bengal", ["Kolkata"]), ("Gujarat", ["Surat", "Ahmedabad"])]
CHUNK = 5000


def weighted(rng, pairs):
    values, weights = zip(*pairs)
    return rng.choices(values, weights=weights, k=1)[0]


def insert_chunks(conn, table, rows):
    for start in range(0, len(rows), CHUNK):
        conn.execute(table.insert(), rows[start:start + CHUNK])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, required=True, help="number of attendance rows")
    parser.add_argument("--db", required=True, help="database name, must start with perf_")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--drop", action="store_true", help="drop and recreate the database first")
    args = parser.parse_args()

    started = time.perf_counter()
    rng = random.Random(args.seed)
    _safe.ensure_database(args.db, drop_first=args.drop)
    engine = _safe.perf_engine(args.db)
    TenantBase.metadata.create_all(bind=engine)
    with engine.begin() as conn:  # indexes production has (legacy website) that the models do not declare
        for ddl in (
            "ALTER TABLE attendance ADD UNIQUE KEY unique_session_attendance (conferenceUid, traineeUid)",
            "ALTER TABLE assessment_results ADD KEY idx_conf_suite (conferenceUid, assessmentSuiteUid)",
            "ALTER TABLE assessment_results ADD UNIQUE KEY unique_attempt (traineeUid, assessmentSuiteUid, attemptNumber)",
            "ALTER TABLE trainee ADD UNIQUE KEY uid (uid, email)",
        ):
            try:
                conn.execute(text(ddl))
            except Exception as exc:  # already present when re-running without --drop
                print("  (skipped)", ddl[:60], "->", str(getattr(exc, "orig", exc))[:60])

    n_conf = max(args.rows // 30, 10)
    n_trainee = max(args.rows // 4, 50)
    trainers = [(f"T{n:04d}", f"{rng.choice(FIRST)} {rng.choice(LAST)}") for n in range(60)]
    trainer_weights = [1 / (rank + 1) ** 0.8 for rank in range(len(trainers))]  # a few very busy trainers
    today = date(2026, 9, 25)

    conferences, conf_meta = [], []
    for n in range(n_conf):
        zone = rng.choice(list(ZONES))
        state, districts = rng.choice(STATES)
        trainer_id, trainer_name = rng.choices(trainers, weights=trainer_weights, k=1)[0]
        day = today - timedelta(days=int(rng.expovariate(1 / 60)) % 240)  # recent-skewed
        uid = f"CONF{n:07d}"
        company = weighted(rng, COMPANIES)
        conferences.append(
            {
                "conferenceUid": uid,
                "zone": zone,
                "region": rng.choice(ZONES[zone]),
                "company": company,
                "trainerEmployeeId": trainer_id,
                "trainerName": trainer_name,
                "conferenceDate": day.isoformat(),
                "conferenceStatus": weighted(rng, CONF_STATUS_MIX),
                "status": weighted(rng, [("Approved", 0.9), ("Pending", 0.07), ("Rejected", 0.03)]),
                "sessionType": rng.choice(["Online", "Offline"]),
                "audience": rng.choice(["Retail", "Distributor", "Promoter"]),
                "trainingType": rng.choice(TRAINING_TYPES),
                "state": state,
                "district": rng.choice(districts),
                "postAssessmentUid": f"SUITE{rng.randint(1, 12):03d}" if rng.random() < 0.8 else None,
            }
        )
        conf_meta.append((uid, company, day, conferences[-1]["postAssessmentUid"]))

    trainees = []
    for n in range(n_trainee):
        trainees.append(
            {
                "traineeUid": f"TR{n:08d}",
                "name": f"{rng.choice(FIRST)} {rng.choice(LAST)} {n}",
                "email": f"trainee{n}@example.test",
                "phone": 9_000_000_000 + n,
                "uid": f"HO{n:07d}",
                "supervisorName": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                "username": f"trainee{n}",
            }
        )
    trainee_weights = [1 / (rank + 1) ** 0.5 for rank in range(n_trainee)]  # some trainees attend far more

    # Who attends which conference: ~rows/conferences each (gaussian), popular trainees more often,
    # then topped up at random so the total is exactly --rows.
    per_conf = max(args.rows // n_conf, 1)
    attendees: list[set[int]] = []
    for _ in conf_meta:
        want = max(1, int(rng.gauss(per_conf, per_conf * 0.4)))
        picked: set[int] = set()
        while len(picked) < min(want, n_trainee):
            picked.update(rng.choices(range(n_trainee), weights=trainee_weights, k=want - len(picked)))
        attendees.append(picked)
    total = sum(len(p) for p in attendees)
    while total > args.rows:  # trim the biggest overshoot first
        big = max(range(len(attendees)), key=lambda i: len(attendees[i]))
        attendees[big].pop()
        total -= 1
    while total < args.rows:
        c = rng.randrange(len(attendees))
        t = rng.randrange(n_trainee)
        if t not in attendees[c]:
            attendees[c].add(t)
            total += 1

    attendance, results = [], []
    next_attempt: dict[tuple[str, str], int] = {}  # attempts count up per (trainee, suite) across trainings
    serial = 0
    for (uid, company, day, post_suite), picked in zip(conf_meta, attendees):
        for t in sorted(picked):
            status = weighted(rng, STATUS_MIX)
            stamp = datetime.combine(day, datetime.min.time()) + timedelta(hours=rng.randint(8, 18), minutes=rng.randint(0, 59))
            trainee_uid = trainees[t]["traineeUid"]
            attendance.append(
                {
                    "attendanceUid": f"ATT{serial:09d}",
                    "conferenceUid": uid,
                    "traineeUid": trainee_uid,
                    "phone": trainees[t]["phone"] if rng.random() < 0.7 else None,
                    "markedOn": stamp.strftime("%H:%M") if status == "Present" else None,
                    "timestamp": stamp,
                    "checkOutTime": stamp + timedelta(hours=rng.randint(1, 4)) if status == "Present" and rng.random() < 0.7 else None,
                    "updatedBy": rng.choice(["admin", "trainer", None]),
                    "status": status,
                    "sessionMeta": json.dumps({"audience": rng.choice(["ASSIGNED", "UNASSIGNED", "FRESH"])}),
                }
            )
            if status in ("Present", "Joined") and post_suite and rng.random() < 0.6:
                for _ in range(rng.randint(1, 3)):
                    suite = post_suite if rng.random() < 0.85 else "SUITE900"
                    attempt = next_attempt.get((trainee_uid, suite), 0) + 1
                    next_attempt[(trainee_uid, suite)] = attempt
                    score = rng.randint(0, 20)
                    results.append(
                        {
                            "resultUid": f"RES{len(results):09d}",
                            "conferenceUid": uid,
                            "traineeUid": trainee_uid,
                            "assessmentSuiteUid": suite,
                            "attemptNumber": attempt,
                            "totalScore": score,
                            "maxScore": 20,
                            "percentage": round(score / 20 * 100, 2),
                            "status": "Submitted" if rng.random() < 0.9 else "Started",
                        }
                    )
            serial += 1

    print(f"generated in memory: {len(conferences)} conferences, {len(trainees)} trainees, {len(attendance)} attendance, {len(results)} results "
          f"({time.perf_counter() - started:.1f}s)")
    load_started = time.perf_counter()
    with engine.begin() as conn:
        insert_chunks(conn, Conference.__table__, conferences)
        insert_chunks(conn, Trainee.__table__, trainees)
        insert_chunks(conn, Attendance.__table__, attendance)
        insert_chunks(conn, AssessmentResult.__table__, results)
    load_seconds = time.perf_counter() - load_started

    with engine.connect() as conn:
        for table in ("conference", "trainee", "attendance", "assessment_results"):
            conn.execute(text(f"ANALYZE TABLE {table}"))
        sizes = conn.execute(
            text(
                "SELECT table_name, table_rows, ROUND(data_length/1048576,1), ROUND(index_length/1048576,1) "
                "FROM information_schema.tables WHERE table_schema = DATABASE() "
                "AND table_name IN ('conference','trainee','attendance','assessment_results')"
            )
        ).all()
    meta = {
        "database": args.db,
        "seed": args.seed,
        "rows": {"conference": len(conferences), "trainee": len(trainees), "attendance": len(attendance), "assessment_results": len(results)},
        "load_seconds": round(load_seconds, 1),
        "attendance_rows_per_second": round(len(attendance) / load_seconds),
        "sizes_mb": {t: {"approx_rows": int(r), "data": float(d), "indexes": float(i)} for t, r, d, i in sizes},
    }
    with open(f"perf/results/dataset_{args.db}.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
