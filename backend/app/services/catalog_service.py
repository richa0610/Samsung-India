from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import (
    AUDIENCE_CATEGORY,
    CHECKLIST_CATEGORY,
    SESSION_TYPE_CATEGORY,
    TRAINING_TYPE_CATEGORY,
    ZONE_CATEGORY_GROUP,
)
from app.core.exceptions import bad_request
from app.models.conference import Conference
from app.repositories import catalog_repository
from app.schemas.catalog import MasterGroupOut, SelectOptionOut
from app.services import location_service
from app.utils.zones import zone_key


def list_venues(
    db: Session, common_db: Session, district: Optional[str], state: Optional[str] = None
) -> list[SelectOptionOut]:
    """Powers the Add Training form's Venue picker, gated on District and its State (both from the
    pincode directory - location_service): the venues the venue table puts there, plus any whose
    pincode belongs to that district. An older app build sends no state: its district's venues by
    name only, as before."""
    pincodes = location_service.district_pincodes(common_db, state, district) if state and district else frozenset()
    venues = catalog_repository.list_venues(db, district, state, pincodes)
    return [SelectOptionOut(label=v.name, value=v.venueUid) for v in venues]


def list_zones(db: Session) -> list[MasterGroupOut]:
    """Powers the Add Training form's Zone and Region pickers: the zone categories (East,
    North, ...), each with its regions (its subcategories), saved as the master spells them
    ("North"). A training saved earlier as "North Zone" is the same zone everywhere zones are
    compared (utils/zones.py)."""
    return [
        MasterGroupOut(name=name, options=options)
        for name, options in catalog_repository.list_category_groups(db, ZONE_CATEGORY_GROUP)
    ]


def master_zone_region(db: Session, zone: Optional[str], region: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """A zone and region a self-registering trainee picked, as the master list names them - or 400
    when either isn't on it (the zone names the trainee's ID: SOUTH2610001). No zone = none picked
    (an older app build): (None, None)."""
    if not (zone or "").strip():
        return None, None
    groups = catalog_repository.list_category_groups(db, ZONE_CATEGORY_GROUP)
    match = next(((name, regions) for name, regions in groups if zone_key(name) == zone_key(zone)), None)
    if match is None:
        raise bad_request("Pick your zone from the list")
    zone_name, regions = match
    if not (region or "").strip():
        return zone_name, None
    region_name = next((r for r in regions if r.strip().lower() == region.strip().lower()), None)
    if region_name is None:
        raise bad_request("Pick a region of your zone from the list")
    return zone_name, region_name


def list_checklist_items(db: Session) -> list[SelectOptionOut]:
    """Powers the Add Training form's Checklist picker: the "Training Checklist" category's
    approved options only. Values are `subCategoryUid`s - `conference.checklistUid` stores a
    comma-separated list of these (see that column's comment in the schema)."""
    items = catalog_repository.list_approved_subcategories(db, CHECKLIST_CATEGORY)
    return [
        SelectOptionOut(label=i.subCategory.strip(), value=i.subCategoryUid)
        for i in items
        if i.subCategoryUid and (i.subCategory or "").strip()
    ]


def _options(values: list[str]) -> list[SelectOptionOut]:
    return [SelectOptionOut(label=v, value=v) for v in values]


def _distinct_options(db: Session, column) -> list[SelectOptionOut]:
    """Options for a picker with no master category: the distinct values this
    tenant has already used for `column` across its conferences. Empty until
    the tenant creates its first training that fills the field in."""
    return _options(catalog_repository.list_distinct_conference_values(db, column))


def _master_options(db: Session, category: str, column) -> list[SelectOptionOut]:
    """Options for a picker backed by a master category: its approved option names, saved as
    the name. While the category has none, the values already used on past trainings (this
    picker's source before the master list), so the picker never goes empty."""
    names = catalog_repository.list_approved_subcategory_names(db, category)
    return _options(names) if names else _distinct_options(db, column)


def list_training_hubs(db: Session) -> list[SelectOptionOut]:
    return _distinct_options(db, Conference.trainingHub)


def list_audiences(db: Session) -> list[SelectOptionOut]:
    return _master_options(db, AUDIENCE_CATEGORY, Conference.audience)


def list_session_types(db: Session) -> list[SelectOptionOut]:
    return _master_options(db, SESSION_TYPE_CATEGORY, Conference.sessionType)


def list_training_types(db: Session) -> list[SelectOptionOut]:
    return _master_options(db, TRAINING_TYPE_CATEGORY, Conference.trainingType)


def list_requested_by_options(db: Session) -> list[SelectOptionOut]:
    """Unlike the other pickers here, always guarantees an "Other" option
    so a trainer can type a requester that hasn't been used before -
    matches the free-text fallback add_training.tsx already offers."""
    options = _distinct_options(db, Conference.requestedBy)
    if not any(o.value.lower() == "other" for o in options):
        options.append(SelectOptionOut(label="Other", value="Other"))
    return options
