from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class TraineeRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: int
    email: EmailStr
    gender: Optional[str] = Field(default=None, max_length=50)
    designation: Optional[str] = Field(default=None, max_length=150)
    employee_id: Optional[str] = Field(default=None, max_length=100)
    supervisorName: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid_mobile(cls, value: int) -> int:
        if not 6_000_000_000 <= value <= 9_999_999_999:
            raise ValueError("Phone number must be a valid 10-digit mobile number")
        return value


class TraineeLogin(BaseModel):
    phone: int


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
    state: Optional[str] = None
    district: Optional[str] = None
    profilePhoto: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    trainee: TraineeOut
