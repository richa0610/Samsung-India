from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.tenant import TenantOut


class TraineeRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: int
    email: EmailStr
    gender: Optional[str] = Field(default=None, max_length=50)
    designation: Optional[str] = Field(default=None, max_length=150)
    employee_id: Optional[str] = Field(default=None, max_length=100)
    supervisorName: Optional[str] = Field(default=None, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    # From the master list (checked on the server); the zone starts the trainee's ID. Optional: an
    # older app build sends neither - that trainee's ID starts TRN.
    zone: Optional[str] = Field(default=None, max_length=120)
    region: Optional[str] = Field(default=None, max_length=150)
    # Registering signs the trainee in on this device (TraineeLogin.deviceId) - not saved on the trainee.
    deviceId: Optional[str] = Field(default=None, max_length=100)
    deviceName: Optional[str] = Field(default=None, max_length=255)

    @field_validator("state")
    @classmethod
    def state_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("State is required")
        return value.strip()

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid_mobile(cls, value: int) -> int:
        if not 6_000_000_000 <= value <= 9_999_999_999:
            raise ValueError("Phone number must be a valid 10-digit mobile number")
        return value


class TraineeLogin(BaseModel):
    # What the trainee typed into "Company ID / Phone No": their Trainee UID, username or phone number.
    identifier: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)
    # The signed-in device (services/device_sessions): the app's install ID and a name to show. An
    # older app sends neither - each of its sign-ins then counts as a new device.
    deviceId: Optional[str] = Field(default=None, max_length=100)
    deviceName: Optional[str] = Field(default=None, max_length=255)
    # Signing in to join a training from its QR code: the company (tenant ID) the QR names. The
    # account signed in to must be there, else 403 "No training access" (user, 2026-10-22).
    company: Optional[str] = Field(default=None, max_length=100)

    @field_validator("identifier")
    @classmethod
    def identifier_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Enter your Company ID or Phone No")
        return value.strip()


class TraineeUpdate(BaseModel):
    """All fields optional - the trainee only sends what they actually
    changed on their Edit Profile form."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[int] = None
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    supervisorName: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


class TraineeOut(BaseModel):
    id: int
    traineeUid: str
    name: str
    phone: int
    email: str
    gender: Optional[str] = None
    designation: Optional[str] = None
    employee_id: Optional[str] = None
    supervisorName: Optional[str] = None
    supervisorDesignation: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    zone: Optional[str] = None
    region: Optional[str] = None
    profilePhoto: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    trainee: TraineeOut
    # The company signed in to - set when the sign-in named none (services/sign_in_service).
    company: Optional[TenantOut] = None
