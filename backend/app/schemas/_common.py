"""Reusable constrained field types for request models.

The frontend (`src/utils/validation`) already trims, strips control chars and
caps length on every form field - but the server can never trust that, so
these aliases enforce the same limits on the API boundary. Output/response
models don't need them (the data is ours by then).

Length caps are deliberately generous: the goal is to stop a client sending
multi-megabyte values (memory / DB abuse, `bcrypt` slow-hash DoS), not to
second-guess legitimate content.
"""

from typing import Annotated, Optional

from pydantic import BaseModel, StringConstraints

# Single-line free text (names, labels, cities, dropdown values).
ShortStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
OptShortStr = Optional[ShortStr]

# A non-empty single-line value (person / entity names).
NameStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
]

# Opaque identifiers (UIDs, employee IDs, usernames, category keys).
IdStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)]
OptIdStr = Optional[IdStr]

# Multi-line prose (address, remarks, "about", question text).
TextStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
OptTextStr = Optional[TextStr]

# Digit strings kept as text in the DB (phone, pincode, batch size, salary).
DigitStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^\d*$", max_length=20)
]
OptDigitStr = Optional[DigitStr]

# Exactly a 10-digit Indian mobile number.
Phone10Str = Annotated[str, StringConstraints(pattern=r"^\d{10}$")]

# Date / time values that travel as strings ("YYYY-MM-DD", "HH:MM").
DateLikeStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=40)]
OptDateLikeStr = Optional[DateLikeStr]

# Bounded email length; format checked by EmailStr where the field is required.
OptEmailLike = Annotated[
    Optional[str], StringConstraints(strip_whitespace=True, max_length=254)
]


class PageMeta(BaseModel):
    """The pagination fields every paged list response carries (repositories/keyset.Page.meta).

    `nextCursor` - "the rows after this page" for keyset walks (export, load more); null on the
    last page, and for orders that page by number only. `total` / `totalPages` - every row the
    caller may see that matches the filters / search - sent with every numbered page, omitted
    (null) on a cursor continuation. `page` - the page served (null for a cursor continuation);
    `pageSize` - the rows per page actually applied (after the 1..200 clamp)."""

    nextCursor: Optional[str] = None
    total: Optional[int] = None
    page: Optional[int] = None
    pageSize: Optional[int] = None
    totalPages: Optional[int] = None
