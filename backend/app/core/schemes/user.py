from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints


MIN_FULL_NAME_LENGTH = 2
MAX_FULL_NAME_LENGTH = 150
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

FullName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=MIN_FULL_NAME_LENGTH, max_length=MAX_FULL_NAME_LENGTH
    ),
]
Password = Annotated[str, Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)]


class UserRegister(BaseModel):
    email: EmailStr
    full_name: FullName
    password: Password
    preferred_language: Literal["uz", "en", "ru", "ko"] = "uz"
    account_type: Literal["learner", "author"] = "learner"
    author_invite: str | None = Field(default=None, min_length=43, max_length=43)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    account_type: Literal["learner", "author"] = "learner"
    preferred_language: str
    age: int | None = None
    bio: str | None = None
    avatar_url: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    account_type: Literal["learner", "author"] = "learner"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    full_name: FullName | None = None
    email: EmailStr | None = None
    preferred_language: Literal["uz", "en", "ru", "ko"] | None = None
    age: int | None = Field(default=None, ge=5, le=120)
    bio: str | None = Field(default=None, max_length=500)


class AvatarUpload(BaseModel):
    data_url: str = Field(min_length=40, max_length=2_800_000)


class UserPasswordChange(BaseModel):
    current_password: str
    new_password: Password


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    new_password: Password
