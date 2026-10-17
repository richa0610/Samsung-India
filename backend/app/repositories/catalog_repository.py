from collections.abc import Collection
from typing import Iterable, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.models.category import Category, SubCategory
from app.models.venue import Venue
from app.repositories.location_repository import pincode_key_sql, place_key_sql
from app.utils.conference_format import NOT_ASSIGNED
from app.utils.places import place_spellings

APPROVED = "Approved"


def list_venues(
    db: Session,
    district: Optional[str] = None,
    state: Optional[str] = None,
    pincodes: Collection[str] = (),
) -> list[Venue]:
    """Approved venues, A to Z. With a `district`, only that district's: a venue whose own district
    names it (any case, "_" as a space, an old app build's code) - and, given a `state`, whose own
    state names it too or is blank, so a district name two states share never mixes them - or
    whose pincode is one of `pincodes` (the district's, from the pincode directory), whatever its
    own district / state say."""
    query = db.query(Venue).filter(Venue.status == APPROVED)
    if district:
        named_here = place_key_sql(Venue.district).in_(place_spellings(district))
        if state:
            stored_state = place_key_sql(Venue.state)
            named_here = and_(named_here, or_(stored_state == "", stored_state.in_(place_spellings(state))))
        in_district = [named_here]
        if pincodes:
            in_district.append(pincode_key_sql(Venue.pincode).in_(sorted(pincodes)))
        query = query.filter(or_(*in_district))
    return query.order_by(Venue.name).all()


def get_venues_by_uids(db: Session, venue_uids: set[str]) -> list[Venue]:
    if not venue_uids:
        return []
    return db.query(Venue).filter(Venue.venueUid.in_(venue_uids)).all()


def get_venue_by_uid(db: Session, venue_uid: str) -> Optional[Venue]:
    return db.query(Venue).filter(Venue.venueUid == venue_uid).first()


def list_approved_subcategories(db: Session, category_name: str) -> list[SubCategory]:
    """The approved options of the approved category named `category_name` (any letter case or
    spacing) - never another category's."""
    category_uids = select(Category.categoryUid).where(
        func.lower(func.trim(Category.name)) == category_name.strip().lower(), Category.status == APPROVED
    )
    return (
        db.query(SubCategory)
        .filter(SubCategory.categoryUid.in_(category_uids), SubCategory.status == APPROVED)
        .order_by(SubCategory.subCategory)
        .all()
    )


def list_approved_subcategory_names(db: Session, category_name: str) -> list[str]:
    return _sorted_names(sub.subCategory for sub in list_approved_subcategories(db, category_name))


def list_category_groups(db: Session, group: str) -> list[tuple[str, list[str]]]:
    """The approved categories marked `visibleOnWeb` = `group` (any case), each with its
    approved subcategory names - the zones and their regions (East -> East 1, ...). Two queries
    whatever the size; two categories with one name are one option."""
    categories = db.query(Category.categoryUid, Category.name).filter(
        func.lower(func.trim(Category.visibleOnWeb)) == group.strip().lower(), Category.status == APPROVED
    ).all()
    children = _approved_names_by_category(db, {uid for uid, _ in categories if uid})
    grouped: dict[str, list[str]] = {}
    for uid, name in categories:
        if name and name.strip():
            grouped.setdefault(name.strip(), []).extend(children.get(uid, []))
    return [(name, _sorted_names(grouped[name])) for name in _sorted_names(grouped)]


def _approved_names_by_category(db: Session, category_uids: set[str]) -> dict[str, list[str]]:
    """Each category's approved subcategory names."""
    names: dict[str, list[str]] = {}
    if category_uids:
        rows = db.query(SubCategory.categoryUid, SubCategory.subCategory).filter(
            SubCategory.categoryUid.in_(category_uids), SubCategory.status == APPROVED
        )
        for category_uid, name in rows:
            names.setdefault(category_uid, []).append(name)
    return names


def list_distinct_conference_values(db: Session, column, conditions: Optional[list] = None) -> list[str]:
    """Distinct, non-empty values already used for `column` across this
    tenant's conferences - backs the Training Hub / Requested By pickers (no
    master category), the Audience / Session Type / Training Type pickers
    while their master category has no options, and the Sessions screen's
    filter options. `conditions` narrows to the conferences a caller may see. The other system's
    "Not Assigned" placeholder (conference_format.NOT_ASSIGNED) is never an option."""
    rows = (
        db.query(column)
        .filter(column.isnot(None), column != "", func.lower(column) != NOT_ASSIGNED.lower(), *(conditions or []))
        .distinct()
        .all()
    )
    return _sorted_names(row[0] for row in rows)


def _sorted_names(values: Iterable[Optional[str]]) -> list[str]:
    """Trimmed, blanks dropped, each once, in case-insensitive order."""
    names = {value.strip() for value in values if value and value.strip()}
    return sorted(names, key=lambda s: s.lower())
