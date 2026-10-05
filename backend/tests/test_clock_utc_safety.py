"""Regression test for a real bug hit while running the backend on a dev machine whose own
clock is not UTC (this one is IST): a session that had actually run for about 3 minutes
(CONF2610082) showed a "time consumed" of 5h 32m.

Root cause: this stack's naive datetimes are meant to be UTC everywhere (see
app/utils/date_utils.py:to_utc_iso) - true of MySQL's own `NOW()` on the Aiven-hosted database,
and true of the app process's `datetime.now()` only when the host it runs on happens to be set
to UTC (true on Render, not true on a local dev machine in another timezone). Several services
called the bare, host-clock-dependent `datetime.now()` for "now" values that get stored in, or
compared against, those UTC columns - `_module_active_seconds` (module runtime), `conference
.actualStartedAt`/`actualEndedAt`, `AssessmentResult.submittedAt`, `Attendance(Log).markedAt`,
and various remark timestamps. On a host whose local clock is IST, that silently added the
IST-UTC offset (5h30m) to anything computed against a value MySQL or `utc_now()` had written.

The fix: `app/utils/date_utils.py:utc_now()` - a naive-UTC "now", derived from an absolute
(tz-aware) reading rather than the host's own local wall clock, the same way `ist_now()` already
did for the IST equivalent. Every one of those call sites now uses it instead of a bare
`datetime.now()`.
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import TenantBase
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.services import training_service
from app.utils import date_utils


class UtcNowIgnoresTheHostsOwnClock(unittest.TestCase):
    """Pins the fix itself: `utc_now()` must come from the tz-aware UTC reading, never from a
    bare, timezone-less `datetime.now()` - which is exactly what a host's local clock is."""

    def test_utc_now_matches_the_tz_aware_reading_even_if_local_now_lies(self):
        real_datetime = date_utils.datetime

        class BogusLocalClock(real_datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is not None:
                    return real_datetime.now(tz)
                # A "local" clock reading 5h30m ahead of UTC - this machine's actual
                # situation (IST) right now, simulated so the test is deterministic
                # on any host.
                return real_datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=5, minutes=30)

        with patch.object(date_utils, "datetime", BogusLocalClock):
            result = date_utils.utc_now()
            true_utc = real_datetime.now(timezone.utc).replace(tzinfo=None)

        self.assertLess(abs((result - true_utc).total_seconds()), 5)


class ModuleRuntimeIgnoresTheHostsOwnClock(unittest.TestCase):
    """Functional check on the exact card that showed the wrong number: a module logged as
    STARTED a few minutes ago (in real UTC, via `utc_now()` - the same function the app now
    uses to write it) must show a few minutes of runtime, not the host's UTC offset added on."""

    def setUp(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        TenantBase.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

    def test_a_session_started_three_minutes_ago_shows_about_three_minutes(self):
        conference = Conference(
            conferenceUid="CONF-CLOCK-TEST",
            enableCheckIn=1,
            activeModuleId="ATTENDANCE",
            actualStartedAt=date_utils.utc_now() - timedelta(minutes=3),
        )
        self.db.add(conference)
        self.db.flush()
        self.db.add(
            ConferenceActivityLog(
                conferenceUid=conference.conferenceUid,
                moduleId="ATTENDANCE",
                action="STARTED",
                timestamp=date_utils.utc_now() - timedelta(minutes=3),
            )
        )
        self.db.commit()

        seconds = training_service._module_active_seconds(self.db, conference)

        self.assertIsNotNone(seconds)
        # ~180s of real elapsed time - the bug this pins showed ~19920s (5h32m) instead.
        self.assertGreaterEqual(seconds, 150)
        self.assertLess(seconds, 400)


if __name__ == "__main__":
    unittest.main()
