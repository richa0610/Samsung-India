"""``before_insert`` hooks that fill each model's identifier column with a
sequential ``<PREFIX><YY>NNNNN`` value (see ``app/utils/uid.py``) whenever one
wasn't set explicitly - a training's skipping numbers the other system's imported rows already have
(``app/utils/conference_id.py``) - except assessment answers and results, which take the other
system's ``SUB`` / ``LIVE`` + date style. Registered for every table whose UID used
to default to ``uuid4().hex``.

Imported for its side effects by ``app/models/__init__.py`` (last, after all
models are defined).
"""

from types import SimpleNamespace

from sqlalchemy import event, select

from app.models.accounts import Accounts
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.attendance_log import AttendanceLog
from app.models.booking import Booking
from app.models.category import Category, SubCategory
from app.models.conference import Conference
from app.models.logs_master import LogsMaster
from app.models.quiz import Assessment, AssessmentResult, AssessmentSuite
from app.models.trainee import Trainee
from app.models.venue import Venue
from app.utils.conference_format import quiz_suite_uids
from app.utils.conference_id import new_conference_uid
from app.utils.helpers import audience_class
from app.utils.uid import next_daily_uid, next_uid
from app.utils.zones import zone_code

# (model, uid attribute, prefix)
REGISTRY = [
    (LogsMaster, "logsUid", "LOG"),
    (Venue, "venueUid", "VEN"),
    (AssessmentSuite, "assessmentSuiteUid", "ASM"),
    (AttendanceLog, "logUid", "ATL"),
    (Category, "categoryUid", "CAT"),
    (SubCategory, "subCategoryUid", "SUB"),
    (Admin, "adminUid", "ADM"),
    (AgencyTeam, "agencyTeamUid", "AGT"),
    (Accounts, "accountsUid", "ACC"),
    (Booking, "bookingUid", "BKG"),
]


def _register(model, attr, prefix):
    @event.listens_for(model, "before_insert")
    def _fill_uid(mapper, connection, target, _attr=attr, _prefix=prefix):
        if not getattr(target, _attr, None):
            setattr(target, _attr, next_uid(connection, _prefix))


for _model, _attr, _prefix in REGISTRY:
    _register(_model, _attr, _prefix)


def _answer_kind(connection, conference_uid, suite_uid) -> str:
    """LIVE when `suite_uid` is that training's Live Quiz, else SUB (a Standard Test or Survey)."""
    table = Conference.__table__
    config = connection.execute(select(table.c.sessionConfig).where(table.c.conferenceUid == conference_uid)).scalar()
    return "LIVE" if suite_uid and suite_uid in quiz_suite_uids(SimpleNamespace(sessionConfig=config)) else "SUB"


def _register_daily(model, attr):
    @event.listens_for(model, "before_insert")
    def _fill_uid(mapper, connection, target, _attr=attr):
        if not getattr(target, _attr, None):
            kind = _answer_kind(connection, target.conferenceUid, target.assessmentSuiteUid)
            setattr(target, _attr, next_daily_uid(connection, kind))


# Answers and results take the other system's style (user, 2026-10-16): LIVE or SUB + the IST date + a
# 4-digit count, e.g. SUB2610160007 (app/utils/uid.py next_daily_uid).
for _model, _attr in ((Assessment, "assessmentUid"), (AssessmentResult, "resultUid")):
    _register_daily(_model, _attr)


# A trainee's ID starts with their zone, as the other system's do (user, 2026-10-16): the zone's
# letters in capitals + YY + a running number per zone, e.g. SOUTH2610001; TRN for a trainee with no
# zone (utils/zones.zone_code). The app makes it - the forms no longer ask for one.
NO_ZONE_TRAINEE_PREFIX = "TRN"


@event.listens_for(Trainee, "before_insert")
def _fill_trainee_uid(mapper, connection, target):
    if not target.traineeUid:
        target.traineeUid = next_uid(connection, zone_code(target.zone) or NO_ZONE_TRAINEE_PREFIX)


# An attendance row's ID names how the trainee reached the training, as the other system's do
# (user, 2026-10-16): NATD a new user (registered through the QR), ATN one on the trainer's roster,
# EXATD an existing / unassigned one - + YY + a running number, e.g. NATD2610001.
ATTENDANCE_PREFIXES = {"FRESH": "NATD", "ASSIGNED": "ATN", "UNASSIGNED": "EXATD"}


@event.listens_for(Attendance, "before_insert")
def _fill_attendance_uid(mapper, connection, target):
    """The type comes from the row's own audience tag (utils/helpers.audience_class) - set by every
    path that creates a row before it is saved; a row without one is an existing user's."""
    if not target.attendanceUid:
        target.attendanceUid = next_uid(connection, ATTENDANCE_PREFIXES[audience_class(target)])


@event.listens_for(Conference, "before_insert")
def _fill_conference_uid(mapper, connection, target):
    """A training's public ID in the other system's shape: CONF + YY + a running number, e.g.
    CONF2610001 (app/utils/conference_id.py)."""
    if not target.conferenceUid:
        target.conferenceUid = new_conference_uid(connection)
