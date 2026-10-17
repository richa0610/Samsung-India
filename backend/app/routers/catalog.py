from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.dependencies.database import get_common_db, get_db
from app.models.admin import Admin
from app.schemas.catalog import MasterGroupOut, SelectOptionOut
from app.services import catalog_service, location_service

router = APIRouter(prefix="/admin", tags=["catalog"])

# A state / district name from the pickers (the longest Indian names are well under this).
PlaceQuery = Annotated[Optional[str], Query(max_length=150)]


@router.get("/venues", response_model=list[SelectOptionOut])
def list_venues(
    district: PlaceQuery = None,
    state: PlaceQuery = None,
    db: Session = Depends(get_db),
    common_db: Session = Depends(get_common_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_venues(db, common_db, district, state)


@router.get("/zones", response_model=list[MasterGroupOut])
def list_zones(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_zones(db)


@router.get("/states", response_model=list[MasterGroupOut])
def list_states(
    common_db: Session = Depends(get_common_db),
    _admin: Admin = Depends(get_current_admin),
):
    """The same list as the public GET /locations/states; kept for the app builds already installed."""
    return location_service.state_groups(common_db)


@router.get("/checklist-items", response_model=list[SelectOptionOut])
def list_checklist_items(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_checklist_items(db)


@router.get("/training-hubs", response_model=list[SelectOptionOut])
def list_training_hubs(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_training_hubs(db)


@router.get("/audiences", response_model=list[SelectOptionOut])
def list_audiences(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_audiences(db)


@router.get("/session-types", response_model=list[SelectOptionOut])
def list_session_types(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_session_types(db)


@router.get("/training-types", response_model=list[SelectOptionOut])
def list_training_types(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_training_types(db)


@router.get("/requested-by-options", response_model=list[SelectOptionOut])
def list_requested_by_options(
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_requested_by_options(db)
