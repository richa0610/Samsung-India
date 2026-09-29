"""Knows when a database's list data last changed, so a list's total can be counted once and then
reused until something is actually added, removed or edited (repositories/keyset.paginate).

Every connection that executes an INSERT / UPDATE / DELETE touching `conference`, `attendance` or
`trainee` is marked; when that transaction COMMITS, the database's version goes up by one. A
rolled-back write changes nothing. This sits at the engine level, so it sees every write this
process makes - ORM saves, bulk updates, raw SQL, scripts - not just the ones a service
remembered to announce. Writes by another process (a second worker, a script run elsewhere, the
legacy PHP system) can't be seen here; the count cache's short expiry covers those.

Versions are per engine (per physical database): two tenants never share one, and an engine
object that goes away takes its version with it (no id reuse surprises)."""

import itertools
import re
import threading
import weakref

from sqlalchemy import event
from sqlalchemy.engine import Engine

# The tables whose contents decide what the paged lists count.
_LIST_TABLES = re.compile(r"\b(conference|attendance|trainee)\b", re.IGNORECASE)
_WRITE = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE)\b", re.IGNORECASE)

_lock = threading.Lock()
_versions: "weakref.WeakKeyDictionary[Engine, int]" = weakref.WeakKeyDictionary()
_tokens: "weakref.WeakKeyDictionary[Engine, int]" = weakref.WeakKeyDictionary()
_next_token = itertools.count(1)


def data_version(engine: Engine) -> tuple[int, int]:
    """(this engine's unique token, its current version) - part of every cached count's key."""
    with _lock:
        if engine not in _tokens:
            _tokens[engine] = next(_next_token)
        return _tokens[engine], _versions.get(engine, 0)


def _bump(engine: Engine) -> None:
    with _lock:
        _versions[engine] = _versions.get(engine, 0) + 1


@event.listens_for(Engine, "after_cursor_execute")
def _mark_list_write(conn, cursor, statement, parameters, context, executemany) -> None:
    if _WRITE.match(statement) and _LIST_TABLES.search(statement):
        conn.info["list_data_written"] = True


@event.listens_for(Engine, "commit")
def _bump_on_commit(conn) -> None:
    if conn.info.pop("list_data_written", False):
        _bump(conn.engine)


@event.listens_for(Engine, "rollback")
def _forget_on_rollback(conn) -> None:
    conn.info.pop("list_data_written", None)
