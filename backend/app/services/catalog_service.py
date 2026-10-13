from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import (
    AUDIENCE_CATEGORY,
    CHECKLIST_CATEGORY,
    SESSION_TYPE_CATEGORY,
    STATE_CATEGORY_GROUP,
    TRAINING_TYPE_CATEGORY,
    ZONE_CATEGORY_GROUP,
)
from app.models.conference import Conference
from app.repositories import catalog_repository
from app.schemas.catalog import MasterGroupOut, SelectOptionOut


def list_venues(db: Session, district: Optional[str]) -> list[SelectOptionOut]:
    """Powers the Add Training form's Venue picker, gated on District."""
    venues = catalog_repository.list_venues(db, district)
    return [SelectOptionOut(label=v.name, value=v.venueUid) for v in venues]


def _groups(db: Session, group: str) -> list[MasterGroupOut]:
    return [MasterGroupOut(name=name, options=options) for name, options in catalog_repository.list_category_groups(db, group)]


def list_zones(db: Session) -> list[MasterGroupOut]:
    """Powers the Add Training form's Zone and Region pickers: the zone categories (East,
    North, ...), each with its regions (its subcategories), saved as the master spells them
    ("North"). A training saved earlier as "North Zone" is the same zone everywhere zones are
    compared (utils/zones.py)."""
    return _groups(db, ZONE_CATEGORY_GROUP)


def list_states(db: Session) -> list[MasterGroupOut]:
    """Powers the Add Training form's State and District pickers: the state categories, each
    with its districts (its subcategories)."""
    return _groups(db, STATE_CATEGORY_GROUP)


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
