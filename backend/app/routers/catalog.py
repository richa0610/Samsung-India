from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin
from app.dependencies.database import get_db
from app.models.admin import Admin
from app.schemas.catalog import SelectOptionOut
from app.services import catalog_service

router = APIRouter(prefix="/admin", tags=["catalog"])


@router.get("/venues", response_model=list[SelectOptionOut])
def list_venues(
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin: Admin = Depends(get_current_admin),
):
    return catalog_service.list_venues(db, district)


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
