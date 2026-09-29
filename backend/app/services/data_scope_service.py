from dataclasses import replace

from sqlalchemy.orm import Session

from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.data_scope import DataScope


def apply_identity_scope(
    db: Session, principal: Admin | AgencyTeam, filters: ConferenceFilters
) -> ConferenceFilters:
    """Narrows `filters` to the caller's own company and assigned zone(s), so
    an admin or trainer can never pull another company's or another zone's
    trainings into an org-wide view - regardless of what they pass as query
    filters (a client-requested zone outside their own is dropped, never
    added to). Zone assignment comes from `data_scopes` (the legacy RBAC
    table, scope_type='zone'); an account with no zone rows there is
    unrestricted on zone, same as one with no `company` set - both are
    "not yet configured" rather than "sees nothing", so rolling this out
    can't silently lock anyone out."""
    table_type = "admin" if isinstance(principal, Admin) else "agencyteam"
    allowed_zones = [
        row.scope_value.strip().lower()
        for row in db.query(DataScope).filter(
            DataScope.table_type == table_type,
            DataScope.user_id == principal.id,
            DataScope.scope_type == "zone",
        )
        if row.scope_value and row.scope_value.strip()
    ]

    zones = filters.zones
    if allowed_zones:
        zones = [z for z in filters.zones if z in allowed_zones] if filters.zones else allowed_zones

    return replace(filters, zones=zones, company=principal.company or None)
