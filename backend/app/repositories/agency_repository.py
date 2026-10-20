"""The other system's company registry - `agency`, in the shared (Common) database. Read-only here:
companies are registered by that system (or scripts/add_agency.py)."""

from sqlalchemy.orm import Session

from app.models.agency import Agency


def list_companies(common_db: Session) -> list[tuple[str, str]]:
    """Every registered company as (agencyUid, companyName); rows missing either are left out. The
    registry holds one row per client company, so it is read whole."""
    return [(uid, name) for uid, name in common_db.query(Agency.agencyUid, Agency.companyName) if uid and name]
