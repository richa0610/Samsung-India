"""One zone, two spellings. The master list (`category` rows grouped under "Zone") names a zone
"North"; trainings, trainees and admin grants saved before it say "North Zone". Every zone
comparison - admin filters, access grants, their SQL twins - goes through `zone_key`, so both
spellings are the same zone and older records keep matching (user, 2026-10-13)."""

from typing import Optional

_SUFFIX = " zone"


def zone_key(value: Optional[str]) -> str:
    """The zone trimmed and lower-cased, without a trailing " Zone": "North Zone" -> "north"."""
    key = (value or "").strip().lower()
    if key.endswith(_SUFFIX):
        key = key[: -len(_SUFFIX)].rstrip()
    return key


def zone_spellings(value: Optional[str]) -> tuple[str, str]:
    """Both stored forms (trimmed, lower-cased) of a zone, for a SQL `IN`: ("north", "north zone")."""
    key = zone_key(value)
    return key, f"{key}{_SUFFIX}"
