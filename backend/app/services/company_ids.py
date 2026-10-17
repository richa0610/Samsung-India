"""A training's company as the other system stores it (user, 2026-10-17): the company's agency ID from
the shared registry (`agency.agencyUid`, e.g. "AGEN2497849"), not its name. A company that isn't
registered there keeps its name.

Admin grants and the app's forms name a company by its name, and rows written before store the
name too - so every comparison uses a company's keys: its normalized name AND its agency ID(s)."""

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.repositories import agency_repository


def _name_key(name: Optional[str]) -> str:
    """How two spellings of one company name compare: trimmed, inner spacing collapsed, any case."""
    return " ".join((name or "").split()).lower()


def company_id(common_db: Optional[Session], name: Optional[str]) -> Optional[str]:
    """What to store for a company given by name: its agency ID, else the name as given."""
    text = (name or "").strip()
    if not text or common_db is None:
        return text or None
    wanted = _name_key(text)
    return next((uid for uid, company in agency_repository.list_companies(common_db) if _name_key(company) == wanted), text)


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
