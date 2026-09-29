from typing import Optional

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    # Cap both: an unbounded password is a bcrypt slow-hash DoS vector, and
    # an unbounded username is pointless DB-query load.
    username: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=1, max_length=128)


class AdminOut(BaseModel):
    username: str
    name: str
    role: str
    offerId: Optional[str] = None
    company: Optional[str] = None
    tenant_id: Optional[str] = None
    profilePicture: Optional[str] = None


class AdminAuthSession(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut


class AdminAccessScopeOut(BaseModel):
    """The caller's own admin_access grant, shaped for the frontend to narrow its filter
    OPTIONS against - a usability convenience only. It grants nothing by itself: the backend
    still enforces the real boundary on every request regardless of what this says (see
    access_service.resolve_scope / access_scope_conditions). `None` means "not restricted on
    this axis"; a list means "only these" (values are lower-cased/trimmed, the same form
    ConferenceFilters already sends on the wire)."""

    allowed: bool
    isSuper: bool
    role: Optional[str] = None
    zones: Optional[list[str]] = None
    regions: Optional[list[str]] = None


class TrainingTypeStatusCount(BaseModel):
    status: str
    count: int


class TrainingTypeGroup(BaseModel):
    type: str
    statuses: list[TrainingTypeStatusCount] = []


class TrainingStatsOut(BaseModel):
    planned: int = 0
    completed: int = 0
    pending: int = 0
    ratePercent: float = 0.0
    typeBreakdown: list[TrainingTypeGroup] = []


class AudienceStatusItem(BaseModel):
    label: str
    count: int
    color: Optional[str] = None


class AudienceSection(BaseModel):
    title: str
    items: list[AudienceStatusItem] = []


class AudienceStatsOut(BaseModel):
    participants: int = 0
    present: int = 0
    absent: int = 0
    presentPercent: float = 0.0
    absentPercent: float = 0.0
    typeBreakdown: list[AudienceSection] = []


class TrainerStatusItem(BaseModel):
    label: str
    count: int


class TrainerStatusSection(BaseModel):
    title: str = "In Training"
    items: list[TrainerStatusItem] = []


class TrainerStatsOut(BaseModel):
    pool: int = 0
    inTraining: int = 0
    idle: int = 0
    utilizationPercent: float = 0.0
    statusAnalysis: list[TrainerStatusSection] = []


class AssessmentGapItem(BaseModel):
    label: str
    value: str
    color: Optional[str] = None


class AssessmentGapSection(BaseModel):
    title: str
    items: list[AssessmentGapItem] = []


class AssessmentStatsOut(BaseModel):
    attempts: int = 0
    passCount: int = 0
    failCount: int = 0
    avgPercent: float = 0.0
    eligibilityGaps: list[AssessmentGapSection] = []


class AdminDashboardStatsOut(BaseModel):
    """Org-wide (not per-trainer) summary for the admin dashboard's four
    overview cards - Training/Audience/Trainers/Assessment."""

    training: TrainingStatsOut
    audience: AudienceStatsOut
    trainers: TrainerStatsOut
    assessment: AssessmentStatsOut
