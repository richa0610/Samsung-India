from dataclasses import dataclass, field
from typing import Optional

from fastapi import Query

from app.models.conference import Conference
from app.utils.zones import zone_key


def _split(value: Optional[str]) -> list[str]:
    return [part.strip().lower() for part in value.split(",") if part.strip()] if value else []


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


@dataclass
class ConferenceFilters:
    """The admin panel's shared filter (date range, trainer, zone, region,
    session type, training type). Every list is comma-separated in the query
    string and matches case-insensitively; an empty filter matches everything.
    Zones are kept as their `zone_key`, so "North" and "North Zone" are one zone."""

    start: Optional[str] = None
    end: Optional[str] = None
    trainers: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    session_types: list[str] = field(default_factory=list)
    training_types: list[str] = field(default_factory=list)
    # Mandatory identity scope (the caller's own `company`) - set server-side
    # by data_scope_service.apply_identity_scope, never from a query param, so
    # it can't be widened by anything the client sends. None = unrestricted.
    company: Optional[str] = None

    def __post_init__(self) -> None:
        self.zones = list(dict.fromkeys(key for key in map(zone_key, self.zones) if key))

    @property
    def active(self) -> bool:
        return bool(
            self.start
            or self.end
            or self.trainers
            or self.zones
            or self.regions
            or self.session_types
            or self.training_types
        )

    def matches(self, conference: Conference) -> bool:
        """Whether one training passes every filter that's set."""
        return (
            self._within_dates(conference.conferenceDate)
            and self._in_company(conference.company)
            and self._in_lists(conference)
        )

    def _within_dates(self, date: Optional[str]) -> bool:
        """Inclusive range. An undated training fails a start date, but not an end date on its own."""
        day = date or ""
        after_start = not self.start or day >= self.start
        before_end = not self.end or day <= self.end
        return after_start and before_end

    def _in_company(self, company: Optional[str]) -> bool:
        return not self.company or _norm(company) == _norm(self.company)

    def _in_lists(self, conference: Conference) -> bool:
        """Every list filter that's set - trainer, zone, region, session type, training type."""
        pairs = (
            (self.trainers, _norm(conference.trainerEmployeeId)),
            (self.zones, zone_key(conference.zone)),
            (self.regions, _norm(conference.region)),
            (self.session_types, _norm(conference.sessionType)),
            (self.training_types, _norm(conference.trainingType)),
        )
        return all(value in wanted for wanted, value in pairs if wanted)


def get_conference_filters(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    trainers: Optional[str] = Query(None),
    zones: Optional[str] = Query(None),
    regions: Optional[str] = Query(None),
    session_types: Optional[str] = Query(None),
    training_types: Optional[str] = Query(None),
) -> ConferenceFilters:
    return ConferenceFilters(
        start=start or None,
        end=end or None,
        trainers=_split(trainers),
        zones=_split(zones),
        regions=_split(regions),
        session_types=_split(session_types),
        training_types=_split(training_types),
    )
