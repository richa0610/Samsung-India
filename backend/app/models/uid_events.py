"""``before_insert`` hooks that fill each model's identifier column with a
sequential ``<PREFIX><YY>NNNNN`` value (see ``app/utils/uid.py``) whenever one
wasn't set explicitly - except a training (conference), whose public ID is
``app/utils/conference_id.py``'s non-sequential format. Registered for every table whose UID used to default
to ``uuid4().hex``.

Imported for its side effects by ``app/models/__init__.py`` (last, after all
models are defined).
"""

from sqlalchemy import event

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
from app.utils.conference_id import new_conference_uid
from app.utils.uid import next_uid

# (model, uid attribute, prefix)
REGISTRY = [
    (LogsMaster, "logsUid", "LOG"),
    (Trainee, "traineeUid", "TRN"),
    (Venue, "venueUid", "VEN"),
    (AssessmentSuite, "assessmentSuiteUid", "ASM"),
    (Assessment, "assessmentUid", "AST"),
    (AssessmentResult, "resultUid", "RES"),
    (Attendance, "attendanceUid", "ATT"),
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


@event.listens_for(Conference, "before_insert")
def _fill_conference_uid(mapper, connection, target):
    """A training's public ID: CONF + YY + opaque company / trainer codes + random digits
    (app/utils/conference_id.py) - not the sequential counter the other tables use, so training
    IDs can't be listed by counting."""
    if not target.conferenceUid:
        target.conferenceUid = new_conference_uid(connection, target.company, target.trainerEmployeeId)
