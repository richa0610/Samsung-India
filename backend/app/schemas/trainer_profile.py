from typing import Optional

from pydantic import BaseModel, Field

from app.schemas._common import (
    OptDateLikeStr,
    OptDigitStr,
    OptEmailLike,
    OptShortStr,
    OptTextStr,
)


class TrainerProfileOut(BaseModel):
    """Matches the frontend's TrainerProfile type
    (src/api/trainerProfile.ts) field-for-field. Backed by the real
    `admin` table for an Admin-model login (nearly every field has a
    matching column there) and by the much smaller real `agencyteam`
    table for an AgencyTeam-model login (see `_agency_to_profile` in
    routers/trainer.py for which fields are actually real there vs
    blank placeholders)."""

    name: str
    email: str
    mobileNumber: str
    altPhone: str
    gender: str
    dob: str

    city: str
    district: str
    state: str
    pincode: str
    landmark: str
    # No backing column on either table (see below) - always true, PATCH
    # accepts but doesn't persist it.
    permanentSameAsLocal: bool

    aadharNumber: str
    aadharFile: str
    profilePicture: str
    about: str
    resume: str
    otherDocument: str

    facebookUsername: str
    twitterUsername: str
    instagramUsername: str
    linkedinUsername: str
    youtubeUsername: str
    github: str

    jobStatus: str
    joinedOn: str
    role: str
    designation: str
    salary: str
    companyEmail: str
    visitingCard: str
    idCard: str
    offerLetter: str
    letterhead: str
    promocode: str

    username: str
    # Never populated from the real hashed value - write-only on PATCH.
    password: str
    remarks: str
    agreedToTerms: bool


class TrainerProfileUpdate(BaseModel):
    """Same fields as TrainerProfileOut, all optional - a PATCH only ever
    sends one section's worth (see PROFILE_SECTION_FIELDS on the
    frontend), and `model_dump(exclude_unset=True)` is used to apply only
    what was actually sent."""

    name: OptShortStr = None
    email: OptEmailLike = None
    mobileNumber: OptDigitStr = None
    altPhone: OptDigitStr = None
    gender: OptShortStr = None
    dob: OptDateLikeStr = None

    city: OptShortStr = None
    district: OptShortStr = None
    state: OptShortStr = None
    pincode: OptDigitStr = None
    landmark: OptShortStr = None
    permanentSameAsLocal: Optional[bool] = None

    aadharNumber: OptDigitStr = None
    aadharFile: OptShortStr = None
    profilePicture: OptShortStr = None
    about: OptTextStr = None
    resume: OptShortStr = None
    otherDocument: OptShortStr = None

    facebookUsername: OptShortStr = None
    twitterUsername: OptShortStr = None
    instagramUsername: OptShortStr = None
    linkedinUsername: OptShortStr = None
    youtubeUsername: OptShortStr = None
    github: OptShortStr = None

    jobStatus: OptShortStr = None
    joinedOn: OptDateLikeStr = None
    role: OptShortStr = None
    designation: OptShortStr = None
    salary: OptDigitStr = None
    companyEmail: OptEmailLike = None
    visitingCard: OptShortStr = None
    idCard: OptShortStr = None
    offerLetter: OptShortStr = None
    letterhead: OptShortStr = None
    promocode: OptShortStr = None

    username: OptShortStr = None
    password: Optional[str] = Field(default=None, max_length=128)
    remarks: OptTextStr = None
    agreedToTerms: Optional[bool] = None
