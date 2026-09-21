from dataclasses import dataclass, field
from typing import Optional

from fastapi import Query

from app.models.conference import Conference


def _split(value: Optional[str]) -> list[str]:
    return [part.strip().lower() for part in value.split(",") if part.strip()] if value else []


@dataclass
class ConferenceFilters:
    """The admin panel's shared filter (date range, trainer, zone, region,
    session type, training type). Every list is comma-separated in the query
    string and matches case-insensitively; an empty filter matches everything."""

    start: Optional[str] = None
    end: Optional[str] = None
    trainers: list[str] = field(default_factory=list)
    zones: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    session_types: list[str] = field(default_factory=list)
    training_types: list[str] = field(default_factory=list)

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
        def norm(value: Optional[str]) -> str:
            return (value or "").strip().lower()

        if self.start and (conference.conferenceDate or "") < self.start:
            return False
        if self.end and (conference.conferenceDate or "") > self.end:
            return False
        if self.trainers and norm(conference.trainerEmployeeId) not in self.trainers:
            return False
        if self.zones and norm(conference.zone) not in self.zones:
            return False
        if self.regions and norm(conference.region) not in self.regions:
            return False
        if self.session_types and norm(conference.sessionType) not in self.session_types:
            return False
        if self.training_types and norm(conference.trainingType) not in self.training_types:
            return False
        return True


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
