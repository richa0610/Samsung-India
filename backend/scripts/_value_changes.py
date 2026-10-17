"""What the align_* conversion scripts share: a planned change to one value of one row, saving every
change to an undo file before it is committed, and putting back exactly those values - only on rows
that still hold what the script wrote."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

STAMP = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class Change:
    table: str
    id: int
    column: str
    before: Optional[str]
    after: Optional[str]


def as_text(value) -> Optional[str]:
    """A stored value as a change records it (a date-time as "YYYY-MM-DD HH:MM:SS")."""
    return f"{value:{STAMP}}" if isinstance(value, datetime) else value


def _stored(model, column: str, text: Optional[str]):
    """A change's recorded text as the column's own type."""
    if text is not None and issubclass(getattr(model, column).type.python_type, datetime):
        return datetime.strptime(text, STAMP)
    return text


def rewrite(db: Session, tables: dict, changes: list[Change], *, reverse: bool = False) -> int:
    """Sets each change's new value (its old one when `reverse`) on the row still holding the other.
    Returns how many were set. `tables` maps a change's table name to its model."""
    done = 0
    for change in changes:
        model = tables[change.table]
        current, target = (change.after, change.before) if reverse else (change.before, change.after)
        column = getattr(model, change.column)
        holds = column.is_(None) if current is None else column == _stored(model, change.column, current)
        result = db.execute(
            update(model).where(model.id == change.id, holds).values({change.column: _stored(model, change.column, target)})
        )
        done += result.rowcount
    return done


def apply(db: Session, tables: dict, changes: list[Change], backup_dir: Path, name: str, tenant: str) -> tuple[int, Path]:
    """Makes the changes, saving every one to `backup_dir` before committing."""
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / f"{name}-{tenant}-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({"tenant": tenant, "changes": [asdict(c) for c in changes]}, indent=2), encoding="utf-8")
    done = rewrite(db, tables, changes)
    db.commit()
    return done, backup


def undo(db: Session, tables: dict, backup: Path, tenant: str) -> tuple[int, int]:
    """Puts back the values a backup lists, on rows still holding what the script wrote. Returns
    (put back, listed)."""
    saved = json.loads(backup.read_text(encoding="utf-8"))
    if saved.get("tenant") != tenant:
        raise SystemExit(f"{backup.name} is for tenant {saved.get('tenant')!r}, not {tenant!r} - nothing changed.")
    changes = [Change(**c) for c in saved["changes"]]
    done = rewrite(db, tables, changes, reverse=True)
    db.commit()
    return done, len(changes)
