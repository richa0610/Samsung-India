"""Reads of the India Post directory (`pincode`, in the shared Common database) - see
services/location_service.py for how they become the State / District pickers."""

from collections.abc import Collection

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.pincode import Pincode


def place_key_sql(column):
    """SQL twin of utils.places' comparison form: trimmed, lower-cased, "_" read as a space.
    Compare it `IN place_spellings(...)`, which also covers the old app builds' codes."""
    return func.replace(func.lower(func.trim(func.coalesce(column, ""))), "_", " ")


def pincode_key_sql(column):
    """A stored pincode without its spaces ("431 001" -> "431001") - the SQL twin of `pincode_key`."""
    return func.replace(func.trim(func.coalesce(column, "")), " ", "")


def pincode_key(value: str | None) -> str:
    return "".join((value or "").split())


def _has_text(column):
    return func.trim(func.coalesce(column, "")) != ""


def state_district_pairs(common_db: Session) -> list[tuple[str, str]]:
    """Every (state, district) the directory names, as stored - one row per pair however many post
    offices it has, blanks left out, in a fixed order."""
    rows = common_db.execute(
        select(Pincode.stateName, Pincode.district)
        .where(_has_text(Pincode.stateName), _has_text(Pincode.district))
        .group_by(Pincode.stateName, Pincode.district)
        .order_by(Pincode.stateName, Pincode.district)
    ).all()
    return [(state, district) for state, district in rows]


def pincodes_of(common_db: Session, state_spellings: Collection[str], district_spellings: Collection[str]) -> set[str]:
    """The pincodes of one district, given the state's and the district's stored spellings exactly
    as `state_district_pairs` returned them (plain `IN`s, no function around the columns)."""
    if not state_spellings or not district_spellings:
        return set()
    rows = common_db.execute(
        select(Pincode.pincode)
        .where(Pincode.stateName.in_(sorted(state_spellings)), Pincode.district.in_(sorted(district_spellings)))
        .distinct()
    ).scalars()
    return {key for key in map(pincode_key, rows) if key}
