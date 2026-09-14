from app.models.accounts import Accounts
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.category import Category, SubCategory
from app.models.attendance_log import AttendanceLog
from app.models.booking import Booking
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.conference_activity_log import ConferenceActivityLog
from app.models.data_scope import DataScope
from app.models.quiz import Assessment, AssessmentResult, AssessmentSuite, Question
from app.models.system_module import SystemModule
from app.models.trainee import Trainee
from app.models.uid_sequence import UidSequence
from app.models.user_permission import UserPermission
from app.models.venue import Venue

# Registers before_insert UID hooks - must be last, after every model above.
import app.models.uid_events  # noqa: E402,F401

__all__ = [
    # Existing models (updated for mmtbtwob_tops)
    "Admin",
    "AgencyTeam",
    "Attendance",
    "Category",
    "SubCategory",
    "Conference",
    "ConferenceActivityLog",
    "Assessment",
    "AssessmentResult",
    "AssessmentSuite",
    "Question",
    "Trainee",
    # New models from mmtbtwob_tops
    "Accounts",
    "AttendanceLog",
    "Booking",
    "DataScope",
    "SystemModule",
    "UidSequence",
    "UserPermission",
    "Venue",
    # Common DB (DB-per-tenant split)
    "Tenant",
]
