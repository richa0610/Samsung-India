from typing import Optional

from pydantic import BaseModel


class SelectOptionOut(BaseModel):
    """Generic {label, value} shape for picker options - matches the
    frontend's `SelectOption` type (src/components/ui/SearchableSelect.tsx).

    `name` is optional and only populated by pickers whose `label` isn't
    itself the plain display name (e.g. the trainer picker prefixes the
    employee ID onto `label`, so callers that need the bare name for
    storage - not just display - can use `name` instead)."""

    label: str
    value: str
    name: Optional[str] = None
