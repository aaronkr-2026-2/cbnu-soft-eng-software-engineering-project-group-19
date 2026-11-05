from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    preferred_language: Literal["uz", "en", "ru", "ko"] = "uz"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    preferred_language: str
    age: int | None = None
    bio: str | None = None
    avatar_url: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    email: EmailStr | None = None
    preferred_language: Literal["uz", "en", "ru", "ko"] | None = None
    age: int | None = Field(default=None, ge=5, le=120)
    bio: str | None = Field(default=None, max_length=500)

class AvatarUpload(BaseModel):
    data_url: str = Field(min_length=40, max_length=2_800_000)

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )
