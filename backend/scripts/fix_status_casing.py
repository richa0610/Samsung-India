"""One-off data fix: normalise `conference.status` casing.

The imported mmtbtwob_tops data has 7 rows with lowercase `'approved'`
(all trainer 9988770002). The frontend filters status case-sensitively
(`useTrainerAgendaList`, the Start-Session gate, status badges), so those
sessions silently vanish from the Training List / Pending Training List.

Title-cases any conference.status value that isn't already canonical
(`approved` -> `Approved`, `pending` -> `Pending`, ...). Idempotent.

    ../venv/Scripts/python.exe scripts/fix_status_casing.py
"""

import sys

from sqlalchemy import text

sys.path.insert(0, ".")
from app.database.connection import engine  # noqa: E402

CANON = "CONCAT(UPPER(LEFT(status,1)), LOWER(SUBSTRING(status,2)))"

with engine.begin() as conn:
    before = conn.execute(
        text("SELECT CAST(status AS BINARY) v, COUNT(*) c FROM conference "
             "WHERE status IS NOT NULL AND status <> '' GROUP BY v")
    ).fetchall()
    print("before:", [(v.decode() if isinstance(v, bytes) else v, c) for v, c in before])

    result = conn.execute(
        text(f"UPDATE conference SET status = {CANON} "
             f"WHERE status IS NOT NULL AND status <> '' "
             f"AND CAST(status AS BINARY) <> CAST({CANON} AS BINARY)")
    )
    print("rows updated:", result.rowcount)

    after = conn.execute(
        text("SELECT CAST(status AS BINARY) v, COUNT(*) c FROM conference "
             "WHERE status IS NOT NULL AND status <> '' GROUP BY v")
    ).fetchall()
    print("after: ", [(v.decode() if isinstance(v, bytes) else v, c) for v, c in after])

print("done.")
