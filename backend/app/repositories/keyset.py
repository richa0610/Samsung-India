"""Search + paging shared by the paged list repositories (Training List, Trainee List).

Every paged list follows the same order of operations, so a caller only supplies what is
specific to its entity (the query with its authorization and filter conditions already in the
WHERE, its sort expression and its search columns):

    authorization AND filters AND search  ->  count (first page only)  ->  keyset / offset  ->  rows

Keyset paging ("the rows after this one") stays correct while rows are added and costs the same
however deep it goes; `page` (an OFFSET) is what the table's numbered page buttons use. Order is
always (sort expression, id), the id breaking ties. A cursor is opaque to the client and carries
only a sort value and an id - it can move within a list, never widen it, because it is ANDed onto
the same authorized query."""

import base64
import json
from datetime import datetime
from typing import Any, Callable, Optional

from sqlalchemy import func, or_, tuple_
from sqlalchemy.orm import Query

MAX_PAGE_SIZE = 200


def search_conditions(expressions, search: Optional[str]) -> list:
    """One OR group over `expressions` (case-insensitive substring, LIKE wildcards escaped), or
    nothing for an empty search. Callers AND it with their authorization conditions - the OR
    stays inside this one group, so it can never widen the rows the caller may see."""
    text = (search or "").strip().lower()
    if not text:
        return []
    return [or_(*[func.lower(func.coalesce(expr, "")).contains(text, autoescape=True) for expr in expressions])]


def encode_cursor(value: Any, row_id: int) -> str:
    if isinstance(value, datetime):
        value = value.isoformat()
    return base64.urlsafe_b64encode(json.dumps({"v": value if value is not None else "", "id": row_id}).encode()).decode()


def decode_cursor(cursor: str, datetime_value: bool) -> tuple[Any, int]:
    """Raises ValueError / KeyError / TypeError on a malformed cursor - callers turn that into 400."""
    data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    value = data["v"]
    if datetime_value and isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value, int(data["id"])


def paginate(
    query: Query,
    sort_expr,
    id_column,
    *,
    descending: bool,
    cursor: Optional[str],
    limit: int,
    page: Optional[int],
    cursor_value: Callable[[Any], Any],
    datetime_sort: bool = False,
) -> tuple[list, Optional[str], Optional[int]]:
    """(rows, next_cursor, total) for an already-authorized, filtered and searched `query`.
    `total` is only computed on the first page (no cursor, page 1) - it doesn't change while
    paging. `cursor_value(row)` is the row's sort value, stored in the next cursor."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    total = query.count() if cursor is None and page in (None, 1) else None

    if cursor:
        value, last_id = decode_cursor(cursor, datetime_sort)
        after = tuple_(sort_expr, id_column)
        query = query.filter(after < tuple_(value, last_id) if descending else after > tuple_(value, last_id))

    order = (sort_expr.desc(), id_column.desc()) if descending else (sort_expr.asc(), id_column.asc())
    query = query.order_by(*order)
    if page and page > 1 and not cursor:
        query = query.offset((page - 1) * limit)
    rows = query.limit(limit + 1).all()

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = encode_cursor(cursor_value(rows[-1]), rows[-1].id)
    return rows, next_cursor, total
