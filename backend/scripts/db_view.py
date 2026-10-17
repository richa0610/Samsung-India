"""Read-only DB browser.

Usage (from backend/):
    venv/Scripts/python.exe scripts/db_view.py                      # databases + tables + row counts
    venv/Scripts/python.exe scripts/db_view.py tops_samsung_db       # tables in one DB
    venv/Scripts/python.exe scripts/db_view.py tops_samsung_db trainee [limit]   # rows (newest first)

Columns that look like secrets (password, secret, token, key, hash) are masked.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text  # noqa: E402

from app.database.common import common_engine  # noqa: E402

SYSTEM_DBS = {"information_schema", "mysql", "performance_schema", "sys"}
SECRET_HINTS = ("password", "passwd", "secret", "token", "key", "hash", "otp")


def list_tables(conn, db):
    rows = conn.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema=:d ORDER BY table_name"),
        {"d": db},
    ).fetchall()
    print(f"\n== {db} ({len(rows)} tables)")
    for (table,) in rows:
        count = conn.execute(text(f"SELECT COUNT(*) FROM `{db}`.`{table}`")).scalar()
        print(f"  {table:35} {count}")


def show_rows(conn, db, table, limit):
    columns = [
        r[0]
        for r in conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema=:d AND table_name=:t ORDER BY ordinal_position"
            ),
            {"d": db, "t": table},
        )
    ]
    if not columns:
        sys.exit(f"No table {db}.{table}")
    order = f" ORDER BY `{columns[0]}` DESC"
    result = conn.execute(text(f"SELECT * FROM `{db}`.`{table}`{order} LIMIT {int(limit)}"))
    print(f"== {db}.{table} (showing up to {limit} rows)\n")
    for i, row in enumerate(result, 1):
        print(f"--- row {i}")
        for col, value in zip(columns, row):
            if value is not None and any(h in col.lower() for h in SECRET_HINTS):
                value = "***"
            text_value = str(value)
            if len(text_value) > 120:
                text_value = text_value[:117] + "..."
            print(f"  {col:30} {text_value}")


def main():
    args = sys.argv[1:]
    with common_engine.connect() as conn:
        if not args:
            dbs = [r[0] for r in conn.execute(text("SHOW DATABASES")) if r[0] not in SYSTEM_DBS]
            for db in dbs:
                list_tables(conn, db)
        elif len(args) == 1:
            list_tables(conn, args[0])
        else:
            show_rows(conn, args[0], args[1], args[2] if len(args) > 2 else 10)


if __name__ == "__main__":
    main()
