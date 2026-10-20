"""One state / district, several spellings. The pincode directory (India Post) writes names in
capitals ("UTTAR PRADESH"), the app saves them as words ("Uttar Pradesh"), and older app builds
saved the built-in list's codes ("uttar_pradesh", "up"). Every state / district comparison goes
through `place_key`, so all of them are one place (user, 2026-10-14)."""

import re
from typing import Optional

# The old built-in list's codes that aren't simply the name with "_" for each space.
_LEGACY_CODES = {
    "up": "uttar pradesh",
    "dadra nh daman diu": "dadra and nagar haveli and daman and diu",
    "chandigarh city": "chandigarh",
    "puducherry city": "puducherry",
}

# Joining words kept lower case inside a name ("Jammu and Kashmir").
_JOINING_WORDS = frozenset({"and", "of", "the", "&"})
# A short code in brackets stays in capitals: "AURANGABAD(BH)" -> "Aurangabad(BH)".
_BRACKETED_CODE = re.compile(r"\(([A-Za-z]{1,3})\)")


def _plain(value: Optional[str]) -> str:
    """Trimmed and lower-cased, "_" read as a space - the SQL twin is catalog_repository.place_key_sql."""
    return (value or "").strip().lower().replace("_", " ")


def place_key(value: Optional[str]) -> str:
    """The comparison form of a state / district: "Uttar Pradesh", "UTTAR PRADESH", "uttar_pradesh"
    and "up" are all "uttar pradesh"."""
    key = _plain(value)
    return _LEGACY_CODES.get(key, key)


def place_spellings(value: Optional[str]) -> list[str]:
    """Every stored form (as `_plain` reads it) that is this place - for a SQL `IN`: the name
    itself plus any old code that stands for it ("uttar pradesh" -> also "up")."""
    key = place_key(value)
    return sorted({key, *(code for code, name in _LEGACY_CODES.items() if name == key)})


def place_name(raw: Optional[str]) -> str:
    """A state / district as the app shows and saves it. A name typed in all capitals or all small
    letters (the pincode directory's "UTTAR PRADESH") reads "Uttar Pradesh"; one already in mixed
    case is kept as it was written. Spaces are tidied either way."""
    text = " ".join((raw or "").split())
    if text != text.upper() and text != text.lower():
        return text
    words = [_title_word(word, first=index == 0) for index, word in enumerate(text.lower().split(" "))]
    return _BRACKETED_CODE.sub(lambda match: f"({match.group(1).upper()})", " ".join(words))


def _title_word(word: str, *, first: bool) -> str:
    if not first and word in _JOINING_WORDS:
        return word
    # Capitalise after a start, a bracket, a hyphen or a dot: "y.s.r." -> "Y.S.R.", "north-east".
    return re.sub(r"(^|[(\-.])([a-z])", lambda match: match.group(1) + match.group(2).upper(), word)
