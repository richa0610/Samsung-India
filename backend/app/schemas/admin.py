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


class AdminAuthSession(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminOut
