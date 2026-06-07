import uuid
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=255, examples=["Jane Doe"])]
    email: Annotated[EmailStr, Field(examples=["jane@example.com"])]
    password: Annotated[str, Field(min_length=8, examples=["Str0ng!Pass"])]
    role: Annotated[UserRole, Field(examples=[UserRole.STUDENT])]

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, v: object) -> object:
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        errors: list[str] = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v):
            errors.append("at least one special character")
        if errors:
            raise ValueError("Password must contain " + ", ".join(errors))
        return v

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, Field(examples=["jane@example.com"])]
    password: Annotated[str, Field(examples=["Str0ng!Pass"])]


class RefreshRequest(BaseModel):
    refresh_token: Annotated[str, Field(examples=["<refresh_token>"])]


class LogoutRequest(BaseModel):
    refresh_token: Annotated[str, Field(examples=["<refresh_token>"])]


class UserInfo(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo
