from typing import Optional

from sqlalchemy.orm import Session

from app.models.conference import Conference
from app.repositories import catalog_repository
from app.schemas.catalog import SelectOptionOut


def list_venues(db: Session, district: Optional[str]) -> list[SelectOptionOut]:
    """Powers the Add Training form's Venue picker, gated on District."""
    venues = catalog_repository.list_venues(db, district)
    return [SelectOptionOut(label=v.name, value=v.venueUid) for v in venues]


def list_checklist_items(db: Session) -> list[SelectOptionOut]:
    """Powers the Add Training form's Checklist picker. Values are
    `subCategoryUid`s - `conference.checklistUid` stores a comma-separated
    list of these (see that column's comment in the schema)."""
    items = catalog_repository.list_checklist_items(db)
    return [SelectOptionOut(label=i.subCategory, value=i.subCategoryUid) for i in items]


def _distinct_options(db: Session, column) -> list[SelectOptionOut]:
    """Options for a picker with no master table: the distinct values this
    tenant has already used for `column` across its conferences. Empty until
    the tenant creates its first training that fills the field in."""
    values = catalog_repository.list_distinct_conference_values(db, column)
    return [SelectOptionOut(label=v, value=v) for v in values]


def list_training_hubs(db: Session) -> list[SelectOptionOut]:
    return _distinct_options(db, Conference.trainingHub)


def list_audiences(db: Session) -> list[SelectOptionOut]:
    return _distinct_options(db, Conference.audience)


def list_session_types(db: Session) -> list[SelectOptionOut]:
    return _distinct_options(db, Conference.sessionType)


def list_training_types(db: Session) -> list[SelectOptionOut]:
    return _distinct_options(db, Conference.trainingType)


def list_requested_by_options(db: Session) -> list[SelectOptionOut]:
    """Unlike the other pickers here, always guarantees an "Other" option
    so a trainer can type a requester that hasn't been used before -
    matches the free-text fallback add_training.tsx already offers."""
    values = catalog_repository.list_distinct_conference_values(db, Conference.requestedBy)
    options = [SelectOptionOut(label=v, value=v) for v in values]
    if not any(o.value.lower() == "other" for o in options):
        options.append(SelectOptionOut(label="Other", value="Other"))
    return options
