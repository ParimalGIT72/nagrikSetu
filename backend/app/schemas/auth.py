from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    role: Literal["citizen"] = "citizen"


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: Literal["citizen", "officer", "admin"]
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int