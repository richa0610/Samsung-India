"""The page request every paged list accepts - one definition, so validation is identical
everywhere: `limit` 1..200 (repositories/keyset.MAX_PAGE_SIZE), `page` 1..100000, `cursor` at
most 500 characters. Anything outside is a 422 before the list is touched."""

from dataclasses import dataclass
from typing import Optional

from fastapi import Query

from app.repositories.keyset import MAX_PAGE_SIZE

MAX_PAGE_NUMBER = 100_000


@dataclass(frozen=True)
class PageRequest:
    cursor: Optional[str]
    limit: int
    page: Optional[int]


def page_request(default_limit: int):
    """A dependency for a list whose default page size is `default_limit`."""

    def dependency(
        cursor: Optional[str] = Query(None, max_length=500),
        limit: int = Query(default_limit, ge=1, le=MAX_PAGE_SIZE),
        page: Optional[int] = Query(None, ge=1, le=MAX_PAGE_NUMBER),
    ) -> PageRequest:
        return PageRequest(cursor, limit, page)

    return dependency
