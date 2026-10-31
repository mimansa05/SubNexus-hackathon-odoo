
import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not (re.search(r"[A-Z]", v) and re.search(r"[a-z]", v) and re.search(r"[^A-Za-z0-9]", v)):
            raise ValueError("Password needs an uppercase letter, a lowercase letter and a special character")
        return v


class VerifyEmailRequest(BaseModel):
    token: str


class ResendRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    full_name: str | None
    email: EmailStr
    role: str
    is_active: bool
    email_verified: bool = True

    model_config = ConfigDict(from_attributes=True)


class StaffCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
