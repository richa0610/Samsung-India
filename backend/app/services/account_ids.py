"""How an account is named on the rows this app shares with the other system (user, 2026-10-17): by
its account ID - an admin-panel account's `adminUid`, a trainer's `agencyTeamUid` - as that system
writes them ("AGT001", "AGTM2620011"), never by its login name.

A row written before names its trainer by login name, so every check that asks "is this the same
trainer?" compares an account's keys - its ID AND its login name (`account_keys`) - never one
string with another."""

from dataclasses import replace
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.dependencies.filters import ConferenceFilters
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.repositories import admin_repository


def account_id(account: Admin | AgencyTeam) -> str:
    """The account's ID; its login name for an account that has none yet."""
    uid = account.adminUid if isinstance(account, Admin) else getattr(account, "agencyTeamUid", None)
    return (uid or "").strip() or account.username


def account_name(account: Admin | AgencyTeam) -> str:
    """The account's own name; its login name when it has none."""
    return (account.name or "").strip() or account.username


def account_keys(account: Optional[Admin | AgencyTeam]) -> frozenset[str]:
    """Every value a row may name this account by - its ID (rows written since 2026-10-17) or its
    login name (rows written before)."""
    if account is None:
        return frozenset()
    return frozenset(key for key in (account_id(account), (account.username or "").strip()) if key)


def find_account(db: Session, common_db: Optional[Session], value: Optional[str], *, fallback: bool = False) -> Optional[Admin | AgencyTeam]:
    """The trainer account a row names (by ID or login name): an agency-team account in this
    tenant's database first - where real trainers live - else an admin-table one in the shared
    database (a short session of its own when the caller has none, e.g. a trainee's request).
    None when nobody matches."""
    key = (value or "").strip()
    if not key:
        return None
    agents = admin_repository.get_agents_by_keys(db, {key})
    if agents:
        return agents[0]
    if common_db is not None:
        admins = admin_repository.get_admins_by_keys(common_db, {key})
        return admins[0] if admins else None
    if not fallback:
        return None

    from app.core.config import settings

    if settings.TESTING:
        return None

    from app.database.common import CommonSessionLocal  # local: what tests substitute, as in routers/ws.py

    try:
        shared = CommonSessionLocal()
        try:
            admins = admin_repository.get_admins_by_keys(shared, {key})
            if admins:
                shared.expunge(admins[0])  # usable after this session closes
            return admins[0] if admins else None
        finally:
            shared.close()
    except Exception:
        return None


def trainer_keys(db: Session, common_db: Optional[Session], value: Optional[str], *, fallback: bool = False) -> frozenset[str]:
    """Every value naming the same trainer as `value`: that account's keys, or just `value` itself
    for one no account matches."""
    key = (value or "").strip()
    account = find_account(db, common_db, key, fallback=fallback)
    return account_keys(account) if account is not None else frozenset({key} - {""})


def same_trainer(db: Session, common_db: Optional[Session], first: Optional[str], second: Optional[str]) -> bool:
    """Whether two rows name the same trainer - one by ID and the other by login name included."""
    first, second = (first or "").strip(), (second or "").strip()
    if not first or not second:
        return False
    return first == second or second in trainer_keys(db, common_db, first, fallback=True)


def login_name(db: Session, common_db: Optional[Session], value: Optional[str], *, fallback: bool = False) -> Optional[str]:
    """The login name of the trainer a row names - what the app's trainer pickers and live updates
    use; the stored value itself when no account matches."""
    account = find_account(db, common_db, value, fallback=fallback)
    return account.username if account is not None else ((value or "").strip() or None)


def names_by_key(db: Session, common_db: Optional[Session], values: Iterable[Optional[str]]) -> dict[str, str]:
    """Display names for the accounts these stored values name (ID or login name) - for "updated by"
    columns. A value no account matches is left out (the caller shows it as stored)."""
    keys = {value.strip() for value in values if value and value.strip()}
    names: dict[str, str] = {}
    if common_db is not None:
        for admin in admin_repository.get_admins_by_keys(common_db, keys):
            for key in account_keys(admin) & keys:
                names.setdefault(key, account_name(admin))
    for agent in admin_repository.get_agents_by_keys(db, keys):
        for key in account_keys(agent) & keys:
            names.setdefault(key, account_name(agent))
    return names


def with_trainer_ids(db: Session, common_db: Optional[Session], filters: Optional[ConferenceFilters]) -> Optional[ConferenceFilters]:
    """`filters` with each trainer the app filters by (a login name) also matched by that trainer's
    ID, so trainings stored either way are found."""
    if filters is None or not filters.trainers:
        return filters
    expanded = set(filters.trainers)
    for trainer in filters.trainers:
        expanded |= {key.lower() for key in trainer_keys(db, common_db, trainer, fallback=False)}
    return replace(filters, trainers=sorted(expanded))
