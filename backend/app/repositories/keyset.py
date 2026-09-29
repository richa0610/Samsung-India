"""Search + paging shared by every paged list (Training / Sessions, Trainee, Attendance).

Every paged list follows the same order of operations; a caller only supplies what is specific
to its entity - a `select()` with its authorization and filter conditions already in the WHERE,
its sort order and its search columns:

    authorization AND filters AND search  ->  count  ->  ORDER BY (sort, id)  ->  keyset / offset
    ->  LIMIT page_size + 1  ->  rows of the current page only

Two ways to move through a list:
  - `page` (1-based, an OFFSET) - what the tables' numbered page buttons use. `total` and
    `totalPages` come with every numbered page. The COUNT behind them runs once per distinct
    list and is then reused until that database's list data changes (database/change_tracking)
    or COUNT_TTL_SECONDS pass - so paging through a list doesn't recount it on every page.
  - `cursor` ("the rows after this one", keyset) - what export and "load more" walks use; it
    stays correct while rows are added and costs the same however deep it goes. No count is run
    for a cursor continuation (the caller already has it).
The order always ends with the row id, so ties are never ambiguous and no row is skipped or
repeated across pages. A cursor is opaque to the client, carries only the sort it was issued for,
a sort value and an id, and is ANDed onto the same authorized query - it can move within a list,
never widen it. A multi-key order (e.g. the Sessions screen's grouped order) supports page
numbers only."""

import base64
import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from sqlalchemy import Select, func, or_, select, tuple_
from sqlalchemy.orm import Session

from app.core.ttl_cache import TTLCache
from app.database.change_tracking import data_version

MAX_PAGE_SIZE = 200

# How long a count is trusted without a change this process saw - bounds staleness from writes it
# can't see (another worker, the legacy system writing to the same database).
COUNT_TTL_SECONDS = 60
_count_cache = TTLCache(ttl_seconds=COUNT_TTL_SECONDS, max_entries=5000)


@dataclass(frozen=True)
class SortOrder:
    """How a list is ordered. `clauses` is the full ORDER BY (ending with the id tie-breaker);
    `keyset_expression` is set when the order is a single expression + id, which is what a
    cursor can continue from."""

    key: str
    clauses: tuple
    id_column: Any
    keyset_expression: Any = None
    descending: bool = True
    cursor_value: Optional[Callable[[Any], Any]] = None
    datetime_value: bool = False

    @classmethod
    def keyset(cls, key, expression, id_column, *, descending, cursor_value, datetime_value=False) -> "SortOrder":
        direction = (expression.desc(), id_column.desc()) if descending else (expression.asc(), id_column.asc())
        return cls(key, direction, id_column, expression, descending, cursor_value, datetime_value)

    @classmethod
    def fixed(cls, key, clauses, id_column) -> "SortOrder":
        """A multi-key order; page numbers only (a cursor for it is refused)."""
        return cls(key, tuple(clauses) + (id_column.asc(),), id_column)


@dataclass(frozen=True)
class Page:
    rows: list
    next_cursor: Optional[str]
    total: Optional[int]
    page: Optional[int]  # the page number served; None for a cursor continuation
    page_size: int

    @property
    def total_pages(self) -> Optional[int]:
        return None if self.total is None else math.ceil(self.total / self.page_size)

    def __iter__(self):
        """Unpacks as the (rows, next_cursor, total) tuple the repositories used to return."""
        return iter((self.rows, self.next_cursor, self.total))

    def meta(self) -> dict:
        """The pagination fields every page response carries (schemas/_common.PageMeta)."""
        return {
            "nextCursor": self.next_cursor,
            "total": self.total,
            "page": self.page,
            "pageSize": self.page_size,
            "totalPages": self.total_pages,
        }


def _count(db: Session, count_stmt: Select) -> int:
    """The list's total, from the cache when this exact query (same SQL, same parameters - so the
    same authorization, filters and search) was counted since the database last changed."""
    engine = db.get_bind()
    compiled = count_stmt.compile(dialect=engine.dialect)
    key = (
        data_version(engine),
        str(compiled),
        tuple(sorted((name, repr(value)) for name, value in compiled.params.items())),
    )
    cached = _count_cache.get(key)
    if cached is not None:
        return cached
    total = int(db.scalar(count_stmt) or 0)
    _count_cache.set(key, total)
    return total


def clear_count_cache() -> None:
    """Forgets every cached count (tests)."""
    _count_cache.clear()


def search_conditions(expressions, search: Optional[str]) -> list:
    """One OR group over `expressions` (case-insensitive substring, LIKE wildcards escaped), or
    nothing for an empty search. Callers AND it with their authorization conditions - the OR
    stays inside this one group, so it can never widen the rows the caller may see."""
    text = (search or "").strip().lower()
    if not text:
        return []
    return [or_(*[func.lower(func.coalesce(expr, "")).contains(text, autoescape=True) for expr in expressions])]


def encode_cursor(sort_key: str, value: Any, row_id: int) -> str:
    if isinstance(value, datetime):
        value = value.isoformat()
    payload = {"s": sort_key, "v": value if value is not None else "", "id": row_id}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(sort_key: str, cursor: str, datetime_value: bool) -> tuple[Any, int]:
    """Raises ValueError / KeyError / TypeError on a malformed cursor, or one issued for another
    sort (it would skip or repeat rows) - callers turn that into a 400."""
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    if data["s"] != sort_key:
        raise ValueError("cursor was issued for a different sort")
    value = data["v"]
    if datetime_value:
        value = datetime.fromisoformat(value)
    elif not isinstance(value, (str, int, float)):
        raise ValueError("bad cursor value")
    return value, int(data["id"])


def paginate(
    db: Session,
    stmt: Select,
    order: SortOrder,
    *,
    cursor: Optional[str],
    limit: int,
    page: Optional[int],
    entities: bool = True,
) -> Page:
    """One page of an already-authorized, filtered and searched `stmt`. `entities=True` returns
    ORM objects (`select(Model)`), False the labelled rows of a column select."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    total = None
    if cursor is None:
        counted = stmt.with_only_columns(order.id_column, maintain_column_froms=True).order_by(None)
        total = _count(db, select(func.count()).select_from(counted.subquery()))

    if cursor:
        if order.keyset_expression is None:
            raise ValueError("this sort supports page numbers only")
        value, last_id = decode_cursor(order.key, cursor, order.datetime_value)
        after = tuple_(order.keyset_expression, order.id_column)
        stmt = stmt.where(after < tuple_(value, last_id) if order.descending else after > tuple_(value, last_id))

    stmt = stmt.order_by(*order.clauses)
    page_number = None if cursor else (page or 1)
    if page_number and page_number > 1:
        stmt = stmt.offset((page_number - 1) * limit)
    result = db.scalars(stmt.limit(limit + 1)) if entities else db.execute(stmt.limit(limit + 1))
    rows = list(result.all())

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        if order.cursor_value is not None:
            next_cursor = encode_cursor(order.key, order.cursor_value(rows[-1]), rows[-1].id)
    return Page(rows, next_cursor, total, page_number, limit)
