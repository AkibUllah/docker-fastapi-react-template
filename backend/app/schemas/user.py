from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("password must be at least 8 characters")
    if value.isdigit() or value.isalpha():
        raise ValueError("password must mix letters and digits")
    return value


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    is_superuser: bool = False

    _strength = field_validator("password")(validate_password_strength)


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", max_length=120)
    password: str = Field(min_length=8, max_length=128)

    _strength = field_validator("password")(validate_password_strength)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    is_superuser: bool | None = None

    @field_validator("password")
    @classmethod
    def strength(cls, value: str | None) -> str | None:
        return validate_password_strength(value) if value is not None else None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
