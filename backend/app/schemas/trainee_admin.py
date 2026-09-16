from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas._common import (
    DigitStr,
    IdStr,
    NameStr,
    OptDigitStr,
    OptIdStr,
    OptShortStr,
    OptTextStr,
    ShortStr,
)

ApprovalStatus = Literal["Approved", "Pending", "Rejected"]


class TraineeAdminIn(BaseModel):
    """Payload for POST /admin/trainees - the trainer/admin-side "register a
    new trainee" form. Mirrors NewTraineeInput on the frontend."""

    traineeUid: IdStr
    profilePhoto: OptShortStr = None
    agencyId: OptIdStr = None
    fullName: NameStr
    designation: ShortStr
    gender: ShortStr
    dob: Optional[date] = None
    primaryEmail: EmailStr
    primaryPhone: DigitStr
    altEmail: Optional[EmailStr] = None
    altPhone: OptDigitStr = None
    address: OptTextStr = None
    state: OptShortStr = None
    district: OptShortStr = None
    zone: ShortStr
    region: ShortStr
    company: ShortStr
    requestedBy: ShortStr
    trainerId: IdStr
    trainerName: ShortStr
    supervisorId: IdStr
    supervisorName: ShortStr
    supervisorDesignation: OptShortStr = None
    joinedOn: Optional[date] = None
    jobStatus: ShortStr
    jobCity: OptShortStr = None
    jobPincode: OptDigitStr = None
    resignedOn: Optional[date] = None
    username: IdStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


class TraineeAdminOut(BaseModel):
    traineeUid: str
    registeredAt: str
    approvalStatus: ApprovalStatus
    profilePhoto: Optional[str] = None
    agencyId: Optional[str] = None
    fullName: str
    designation: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    primaryEmail: str
    primaryPhone: str
    altEmail: Optional[str] = None
    altPhone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    zone: Optional[str] = None
    region: Optional[str] = None
    company: Optional[str] = None
    requestedBy: Optional[str] = None
    trainerId: Optional[str] = None
    trainerName: Optional[str] = None
    supervisorId: Optional[str] = None
    supervisorName: Optional[str] = None
    supervisorDesignation: Optional[str] = None
    joinedOn: Optional[str] = None
    jobStatus: Optional[str] = None
    jobCity: Optional[str] = None
    jobPincode: Optional[str] = None
    resignedOn: Optional[str] = None
    username: Optional[str] = None
    updatedBy: Optional[str] = None
    updationOn: Optional[str] = None
    timestamp: Optional[str] = None
