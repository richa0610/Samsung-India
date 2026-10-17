from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_common_db, get_db
from app.schemas.catalog import MasterGroupOut
from app.services import catalog_service, location_service

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/states", response_model=list[MasterGroupOut])
def list_states(common_db: Session = Depends(get_common_db)):
    """Every state with its districts, from the pincode directory. Public: the trainee registration
    form needs it before anyone has signed in. It holds only the public India Post place names -
    nothing of any company - and is served from memory (location_service's hourly cache)."""
    return location_service.state_groups(common_db)


@router.get("/zones", response_model=list[MasterGroupOut])
def list_zones(db: Session = Depends(get_db)):
    """Every zone with its regions, from this organisation's master list - the same list as the staff
    GET /admin/zones. Public: the trainee registration form needs it before anyone has signed in (the
    zone starts the trainee's ID). Zone and region names only."""
    return catalog_service.list_zones(db)
