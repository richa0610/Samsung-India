"""Status strings are stored Title-Cased ('Approved', 'Pending',
'Completed', ...) and the frontend filters them case-sensitively (the
Training List / Pending list, the Start-Session gate, status badges).

Real imported data can't be trusted to follow that - mmtbtwob_tops shipped
rows with lowercase 'approved' - so normalise any DB-read status value
before putting it in an API response.
"""


def title_status(value: str | None) -> str | None:
    """'approved' -> 'Approved', 'PENDING' -> 'Pending'. Leaves None/'' as-is.
    Single-word statuses only, which is all this domain uses."""
    if not value:
        return value
    return value[:1].upper() + value[1:].lower()
