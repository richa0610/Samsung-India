"""A company's dropdown lists - `category` and `subcategory`: the zones and their regions, audiences,
session types, ... (user, 2026-10-20). A company without lists of its own gets the default
company's, so every company's forms offer the same choices: by the automatic company setup
(services/tenant_setup) and by scripts/reset_and_seed.py."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

from app.utils import uid as uid_utils

LIST_TABLES = ("category", "subcategory")
# The counters of their IDs (CAT2610001 / SUB2610001): raised past the copied ones, so the next
# list item the company adds can't repeat one.
LIST_COUNTERS = ("CAT", "SUB")


def _quoted(conn: Connection, name: str) -> str:
    return conn.dialect.identifier_preparer.quote(name)


def has_lists(engine: Engine) -> bool:
    with engine.connect() as conn:
        present = set(inspect(conn).get_table_names())
        return any(conn.execute(text(f"SELECT COUNT(*) FROM {_quoted(conn, t)}")).scalar() for t in LIST_TABLES if t in present)


def copy_lists(source: Engine, target: Engine) -> dict[str, int]:
    """The source company's dropdown lists into `target` - only when `target` has none of its own -
    with their IDs as they are (a region keeps pointing at its zone) and `target`'s CAT / SUB counters
    raised past them. The columns both tables have are copied; the row ids are `target`'s own.
    Returns the rows copied per table ({} when `target` kept its own)."""
    if has_lists(target):
        return {}
    copied = {}
    with source.connect() as src, target.begin() as dst:
        for table in LIST_TABLES:
            theirs = {c["name"] for c in inspect(dst).get_columns(table)}
            columns = [c["name"] for c in inspect(src).get_columns(table) if c["name"] in theirs and c["name"] != "id"]
            rows = src.execute(text(f"SELECT {', '.join(_quoted(src, c) for c in columns)} FROM {_quoted(src, table)} ORDER BY id")).all()
            if rows:
                names = ", ".join(_quoted(dst, c) for c in columns)
                marks = ", ".join(f":c{i}" for i in range(len(columns)))
                dst.execute(text(f"INSERT INTO {_quoted(dst, table)} ({names}) VALUES ({marks})"),
                            [{f"c{i}": v for i, v in enumerate(row)} for row in rows])
            copied[table] = len(rows)
        for prefix in LIST_COUNTERS:
            next_val = src.execute(text("SELECT next_val FROM uid_sequence WHERE prefix = :p"), {"p": prefix}).scalar()
            if next_val:
                uid_utils.raise_counter_floor(dst, prefix, next_val)
    return copied
