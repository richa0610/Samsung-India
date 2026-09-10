from datetime import datetime, timedelta, timezone

# The venue clock. Every conference in this system is in India, and
# `conferenceDate`/`conferenceTime` (and the per-module times) are entered in
# local venue time. IST is a fixed UTC+5:30 with no DST, so a plain offset is
# exact and needs no tz database.
IST = timezone(timedelta(hours=5, minutes=30))


def ist_now() -> datetime:
    """Current venue (IST) wall-clock time as a naive datetime, for comparing
    against the naive `conferenceDate`/`conferenceTime` strings. Derived from
    an absolute UTC reading, so it's correct whether the host runs on UTC
    (Render) or on local time (a dev machine)."""
    return datetime.now(timezone.utc).astimezone(IST).replace(tzinfo=None)


def utc_naive_to_ist(dt: datetime | None) -> datetime | None:
    """Convert a naive UTC datetime (how timestamps are stored on this stack -
    e.g. `conference.actualStartedAt`) to naive IST wall-clock time, so it can
    be compared against parsed `conferenceDate`/`conferenceTime` values."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).astimezone(IST).replace(tzinfo=None)


def ist_to_iso(dt: datetime | None) -> str | None:
    """Tag a naive venue-local (IST) datetime - e.g. a parsed
    `conferenceDate`/`conferenceTime` - with its +05:30 offset so the app
    reads it as the correct instant."""
    if dt is None:
        return None
    return dt.replace(tzinfo=IST).isoformat()


def to_utc_iso(dt: datetime | None) -> str | None:
    """A naive `datetime` - whether from Python's `datetime.now()` on the app
    server or MySQL's `NOW()` - is UTC wall-clock time on this stack (Render +
    Aiven). Tag it explicitly before sending it to the app: without an offset,
    `Date.parse()` on the phone misreads it as already being in the device's
    own local time (see `useLiveRuntime.ts`), which is off by exactly the
    device's UTC offset (5h30m for IST) for anything still "live"."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).isoformat()


def parse_module_start(conference_date: str | None, time_str: str | None) -> datetime | None:
    """`conferenceDate`/`conferenceTime` (and each module's own configured
    start/end time) are free-text columns filled in by whoever schedules the
    training (e.g. "2026-07-25" / "10:00 AM"). This is the one place that
    combines and parses them - change the format string here if the admin
    panel that writes those columns ever changes its format."""
    if not conference_date or not time_str:
        return None
    try:
        return datetime.strptime(f"{conference_date} {time_str}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        return None


def time_to_minutes(raw: str | None) -> int | None:
    """"10:00 AM" / "14:30" -> minutes since midnight, for ordering a session's
    modules by their planned start time. Returns None for a missing/unparseable
    value so callers can sort those last."""
    if not raw:
        return None
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            parsed = datetime.strptime(raw.strip(), fmt)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return None


def duration(start: str | None, end: str | None) -> str | None:
    """Formats a "10:00 AM" -> "11:30 AM" pair as "1h 30m" for display."""
    if not start or not end:
        return None
    try:
        started = datetime.strptime(start, "%I:%M %p")
        ended = datetime.strptime(end, "%I:%M %p")
    except ValueError:
        return None

    minutes = int((ended - started).total_seconds() // 60)
    if minutes <= 0:
        return None

    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"
