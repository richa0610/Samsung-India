"""The State / District pickers, and which pincodes make up a district - all from the India Post
directory (`pincode`, shared Common database), the only source for them (user, 2026-10-14: it
replaces the master list's "State" categories entirely; the same list for every company).

The directory has one row per post office, written in capitals by the other system. Here it
becomes one entry per state, each with its districts: spellings that differ only in letter case,
spacing or "_" are one place (utils/places.place_key), shown as words ("UTTAR PRADESH" ->
"Uttar Pradesh", utils/places.place_name) - the form the app saves.

Cached for an hour in this process (the plan the user approved): the post-office list changes
rarely, the table has no index on these columns, and the trainee registration form reads it
before sign-in - so a request is served from memory instead of grouping the whole table again.
A change made in the other system shows within the hour."""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.core.ttl_cache import TTLCache
from app.repositories import location_repository
from app.schemas.catalog import MasterGroupOut
from app.utils.places import place_key, place_name

CACHE_SECONDS = 3600
_cache = TTLCache(ttl_seconds=CACHE_SECONDS, max_entries=2000)
_DIRECTORY = "directory"


@dataclass
class _Place:
    name: str  # as shown and saved
    spellings: set[str] = field(default_factory=set)  # as stored in the directory


@dataclass
class _State(_Place):
    districts: dict[str, _Place] = field(default_factory=dict)  # by place_key


def clear_cache() -> None:
    """Forgets the cached directory - for tests, which build a new one each time."""
    _cache.clear()


def _directory(common_db: Session) -> dict[str, _State]:
    """{state key: the state, its stored spellings and its districts}. The first spelling read (the
    rows come sorted) names the place, so the shown name never changes between requests."""
    cached = _cache.get(_DIRECTORY)
    if cached is not None:
        return cached
    states: dict[str, _State] = {}
    for raw_state, raw_district in location_repository.state_district_pairs(common_db):
        state = states.setdefault(place_key(raw_state), _State(place_name(raw_state)))
        state.spellings.add(raw_state)
        district = state.districts.setdefault(place_key(raw_district), _Place(place_name(raw_district)))
        district.spellings.add(raw_district)
    _cache.set(_DIRECTORY, states)
    return states


def _by_name(names) -> list[str]:
    return sorted(names, key=str.lower)


def state_groups(common_db: Session) -> list[MasterGroupOut]:
    """Every state with its districts, A to Z - the State picker and, under the chosen state, the
    District picker. Empty when the directory is (no fallback, user 2026-10-14)."""
    states = _directory(common_db).values()
    return [
        MasterGroupOut(name=state.name, options=_by_name(district.name for district in state.districts.values()))
        for state in sorted(states, key=lambda state: state.name.lower())
    ]


def district_pincodes(common_db: Session, state: Optional[str], district: Optional[str]) -> frozenset[str]:
    """The pincodes of `district` in `state` (any spelling of either), or none when the directory
    doesn't have that pair - a district name that also exists in another state never mixes them."""
    entry = _directory(common_db).get(place_key(state))
    district_entry = entry.districts.get(place_key(district)) if entry else None
    if district_entry is None:
        return frozenset()
    cache_key = ("pincodes", place_key(state), place_key(district))
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached
    pincodes = frozenset(location_repository.pincodes_of(common_db, entry.spellings, district_entry.spellings))
    _cache.set(cache_key, pincodes)
    return pincodes
