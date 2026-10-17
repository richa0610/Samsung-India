"""One-off data migration: convert every hex/slug entity UID in the database
to the new sequential ``<PREFIX>26NNNNN`` format (see ``app/utils/uid.py``),
rewriting all foreign-key references in lockstep, then seed ``uid_sequence``
so new inserts continue from where this stopped.

    ../venv/Scripts/python.exe scripts/migrate_uids.py            # apply
    ../venv/Scripts/python.exe scripts/migrate_uids.py --dry-run  # preview only

Safe to re-run: values already in the new format are skipped. Take a
mysqldump backup first (see backend/backups/).
"""

import re
import sys

from sqlalchemy import text

sys.path.insert(0, ".")
from app.database.connection import engine  # noqa: E402
from app.utils.uid import START, YEAR  # noqa: E402

DRY_RUN = "--dry-run" in sys.argv

# (prefix, table, own-uid column).  assessmentsuite: 'default:*' values are
# left untouched (referenced by literal string in questions + app code).
ENTITIES = [
    ("CONF", "conference", "conferenceUid"),
    ("TRN", "trainee", "traineeUid"),
    ("VEN", "venue", "venueUid"),
    ("ASM", "assessmentsuite", "assessmentSuiteUid"),
    ("RES", "assessment_results", "resultUid"),
    ("ATT", "attendance", "attendanceUid"),
    ("CAT", "category", "categoryUid"),
    ("SUB", "subcategory", "subCategoryUid"),
    ("ADM", "admin", "adminUid"),
    ("AGT", "agencyteam", "agencyTeamUid"),
]

# Foreign-key columns that hold a value from one of the maps above.
FK_REFS = [
    ("attendance", "conferenceUid", "CONF"),
    ("assessment_results", "conferenceUid", "CONF"),
    ("assessment", "conferenceUid", "CONF"),
    ("conference_activity_log", "conferenceUid", "CONF"),
    ("attendance_logs", "conferenceUid", "CONF"),
    ("attendance", "traineeUid", "TRN"),
    ("assessment_results", "traineeUid", "TRN"),
    ("assessment", "traineeUid", "TRN"),
    ("attendance_logs", "traineeUid", "TRN"),
    ("conference", "venueUid", "VEN"),
    ("conference", "preAssessmentUid", "ASM"),
    ("conference", "postAssessmentUid", "ASM"),
    ("conference", "surveyUid", "ASM"),
    ("questions", "assessmentSuiteUid", "ASM"),
    ("assessment_results", "assessmentSuiteUid", "ASM"),
    ("assessment", "assessmentSuiteUid", "ASM"),
    ("subcategory", "categoryUid", "CAT"),
]

# Referential checks: (child table, child col) must exist in (parent table, parent col)
INTEGRITY = [
    ("attendance", "conferenceUid", "conference", "conferenceUid"),
    ("assessment_results", "conferenceUid", "conference", "conferenceUid"),
    ("conference_activity_log", "conferenceUid", "conference", "conferenceUid"),
    ("attendance", "traineeUid", "trainee", "traineeUid"),
    ("assessment_results", "traineeUid", "trainee", "traineeUid"),
]


def _fmt(prefix: str, seq: int) -> str:
    return f"{prefix}{YEAR}{seq:05d}"


def _already_new(prefix: str, value: str) -> bool:
    return bool(re.fullmatch(rf"{prefix}{YEAR}\d{{5}}", value or ""))


def _orphan_count(conn, child_t, child_c, parent_t, parent_c) -> int:
    return conn.execute(
        text(
            f"SELECT COUNT(*) FROM `{child_t}` c "
            f"WHERE c.`{child_c}` IS NOT NULL AND c.`{child_c}` <> '' "
            f"AND NOT EXISTS (SELECT 1 FROM `{parent_t}` p WHERE p.`{parent_c}` = c.`{child_c}`)"
        )
    ).scalar()


def run():
    with engine.begin() as conn:
        # 1. orphans before
        before = {k: _orphan_count(conn, *k) for k in
                  [(a, b, c, d) for a, b, c, d in INTEGRITY]}

        # 2. build old -> new maps
        maps: dict[str, dict[str, str]] = {}
        for prefix, table, col in ENTITIES:
            rows = conn.execute(
                text(f"SELECT id, `{col}` FROM `{table}` "
                     f"WHERE `{col}` IS NOT NULL AND `{col}` <> '' ORDER BY id")
            ).fetchall()
            m: dict[str, str] = {}
            seq = START
            for _id, val in rows:
                if prefix == "ASM" and val.startswith("default:"):
                    continue
                if _already_new(prefix, val):
                    seq = max(seq, int(val[len(prefix) + len(YEAR):]) + 1)
                    continue
                m[val] = _fmt(prefix, seq)
                seq += 1
            maps[prefix] = m
            print(f"  {prefix:4} {table:24} {len(m):4} to migrate"
                  + (f"  (e.g. {next(iter(m.values()))})" if m else ""))

        if DRY_RUN:
            print("\n-- dry run, sample mappings --")
            for prefix, m in maps.items():
                for i, (o, n) in enumerate(m.items()):
                    if i >= 3:
                        break
                    print(f"  {prefix}: {o}  ->  {n}")
            raise SystemExit("dry run: rolling back")

        # 3. rewrite own-UID columns
        for prefix, table, col in ENTITIES:
            for old, new in maps[prefix].items():
                conn.execute(text(f"UPDATE `{table}` SET `{col}` = :n WHERE `{col}` = :o"),
                             {"n": new, "o": old})

        # 4. rewrite foreign-key references
        for table, col, prefix in FK_REFS:
            for old, new in maps[prefix].items():
                conn.execute(text(f"UPDATE `{table}` SET `{col}` = :n WHERE `{col}` = :o"),
                             {"n": new, "o": old})

        # 5. conference.checklistUid: comma-separated list of subCategoryUid
        sub_map = maps["SUB"]
        rows = conn.execute(
            text("SELECT id, checklistUid FROM conference "
                 "WHERE checklistUid IS NOT NULL AND checklistUid <> ''")
        ).fetchall()
        for rid, val in rows:
            tokens = [t.strip() for t in val.split(",") if t.strip()]
            new_val = ",".join(sub_map.get(t, t) for t in tokens)
            if new_val != val:
                conn.execute(text("UPDATE conference SET checklistUid = :v WHERE id = :i"),
                             {"v": new_val, "i": rid})

        # 6. seed uid_sequence (next_val = highest used seq + 1, per prefix)
        all_prefixes = [p for p, _, _ in ENTITIES] + ["AST", "ATL", "ACC", "BKG"]
        for prefix in all_prefixes:
            entity = next((e for e in ENTITIES if e[0] == prefix), None)
            nxt = START
            if entity:
                _, table, col = entity
                mx = conn.execute(
                    text(f"SELECT MAX(CAST(SUBSTRING(`{col}`, :cut) AS UNSIGNED)) "
                         f"FROM `{table}` WHERE `{col}` LIKE :like"),
                    {"cut": len(prefix) + len(YEAR) + 1, "like": f"{prefix}{YEAR}%"},
                ).scalar()
                if mx:
                    nxt = int(mx) + 1
            conn.execute(
                text("INSERT INTO uid_sequence (prefix, next_val) VALUES (:p, :v) "
                     "ON DUPLICATE KEY UPDATE next_val = GREATEST(next_val, :v)"),
                {"p": prefix, "v": nxt},
            )
            print(f"  uid_sequence[{prefix}] -> {nxt}")

        # 7. orphans after - must not have grown
        after = {k: _orphan_count(conn, *k) for k in
                 [(a, b, c, d) for a, b, c, d in INTEGRITY]}
        print("\n  referential integrity (orphans before -> after):")
        ok = True
        for k in before:
            flag = "" if after[k] <= before[k] else "  <-- REGRESSION"
            if after[k] > before[k]:
                ok = False
            print(f"    {k[0]}.{k[1]} -> {k[2]}: {before[k]} -> {after[k]}{flag}")
        if not ok:
            raise SystemExit("ABORT: orphaned references increased - rolling back")

        print("\n  committing.")


if __name__ == "__main__":
    print(f"UID migration ({'DRY RUN' if DRY_RUN else 'APPLY'})\n")
    run()
    print("done.")
