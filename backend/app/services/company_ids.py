"""A training's company as the other system stores it (user, 2026-10-17): the company's agency ID from
the shared registry (`agency.agencyUid`, e.g. "AGEN2497849"), not its name. A company that isn't
registered there keeps its name.

Admin grants and the app's forms name a company by its name, and rows written before store the
name too - so every comparison uses a company's keys: its normalized name AND its agency ID(s)."""

from dataclasses import dataclass
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.core.exceptions import conflict
from app.repositories import agency_repository, tenant_repository


@dataclass(frozen=True)
class TenantCompany:
    """The company a tenant's records belong to."""

    name: str    # as admin grants and screens name it
    stored: str  # what a record stores for it: its agency ID (the name when it isn't registered)


def _name_key(name: Optional[str]) -> str:
    """How two spellings of one company name compare: trimmed, inner spacing collapsed, any case."""
    return " ".join((name or "").split()).lower()


def registered_id(common_db: Optional[Session], name: Optional[str]) -> Optional[str]:
    """The agency ID registered under a company name (any spelling), or None when there is none."""
    wanted = _name_key(name)
    if not wanted or common_db is None:
        return None
    return next((uid for uid, company in agency_repository.list_companies(common_db) if _name_key(company) == wanted), None)


def company_id(common_db: Optional[Session], name: Optional[str]) -> Optional[str]:
    """What to store for a company given by name: its agency ID, else the name as given."""
    text = (name or "").strip()
    return registered_id(common_db, text) or text or None


def tenant_company(common_db: Optional[Session], tenant_id: Optional[str]) -> Optional[TenantCompany]:
    """The company of the tenant a caller is signed in to (user, 2026-10-18) - never one a form
    sends. Stored as the tenant's linked agency (`tenants.agency_uid`), else looked up by its name.
    None when the tenant has no registry row (only the default tenant can run without one)."""
    tenant = tenant_repository.get(common_db, tenant_id) if common_db is not None and tenant_id else None
    if tenant is None:
        return None
    return TenantCompany(tenant.company_name, tenant.agency_uid or company_id(common_db, tenant.company_name))


def require_tenant_company(common_db: Optional[Session], tenant_id: Optional[str]) -> TenantCompany:
    """`tenant_company` for a record about to be filed under it (a training, a trainee) - refused
    (409) for a tenant missing from the registry: there is no company to file it under."""
    company = tenant_company(common_db, tenant_id)
    if company is None:
        raise conflict("This organisation isn't registered yet, so it has no company to file this under")
    return company


def company_keys(common_db: Optional[Session], names: Iterable[str]) -> dict[str, frozenset[str]]:
    """For each company name (already trimmed and lower-cased, as admin grants hold it): every
    value - lower-cased - a row may store for it - the name and each agency ID registered under it."""
    keys = {name: {name} for name in names if name}
    if not keys or common_db is None:
        return {name: frozenset(values) for name, values in keys.items()}
    by_name: dict[str, set[str]] = {}
    for uid, company in agency_repository.list_companies(common_db):
        by_name.setdefault(_name_key(company), set()).add(uid.strip().lower())
    return {name: frozenset(values | by_name.get(_name_key(name), set())) for name, values in keys.items()}


def company_names(common_db: Optional[Session], stored: Iterable[Optional[str]]) -> dict[str, str]:
    """The registered name of each stored agency ID among `stored` - what the app shows. A stored
    name (or an ID nobody registered) is left out; the caller shows it as stored."""
    wanted = {value.strip() for value in stored if value and value.strip()}
    if not wanted or common_db is None:
        return {}
    return {uid: company for uid, company in agency_repository.list_companies(common_db) if uid in wanted}


def company_name(common_db: Optional[Session], stored: Optional[str]) -> Optional[str]:
    """One stored company as the app shows it: a registered agency ID's name, else as stored."""
    return company_names(common_db, [stored]).get(stored, stored) if stored else stored
