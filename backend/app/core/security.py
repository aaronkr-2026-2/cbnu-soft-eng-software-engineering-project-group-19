import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if (
    not SECRET_KEY
    or len(SECRET_KEY.encode("utf-8")) < 32
    or SECRET_KEY.lower() in {"change-me", "secret", "your-secret-key"}
    or SECRET_KEY.lower().startswith("replace-with-")
):
    raise RuntimeError(
        "SECRET_KEY must be a private random value of at least 32 bytes. "
        "Set it in the environment or backend/.env file."
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
DUMMY_PASSWORD_HASH = password_hash.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: str, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "ver": token_version,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(user_id: str, token_version: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    return jwt.encode(
        {"typ": "password_reset", "sub": user_id, "ver": token_version, "exp": expires},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_lesson_resource_token(course_id: str, lesson_id: str, resource_key: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    return jwt.encode(
        {
            "typ": "lesson_resource",
            "course_id": course_id,
            "lesson_id": lesson_id,
            "resource_key": resource_key,
            "exp": expires,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_lesson_material_token(course_id: str, lesson_id: str, material_id: str, resource_key: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    return jwt.encode(
        {
            "typ": "lesson_material",
            "course_id": course_id,
            "lesson_id": lesson_id,
            "material_id": material_id,
            "resource_key": resource_key,
            "exp": expires,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_lesson_banner_token(course_id: str, lesson_id: str, banner_key: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    return jwt.encode(
        {
            "typ": "lesson_banner",
            "course_id": course_id,
            "lesson_id": lesson_id,
            "banner_key": banner_key,
            "exp": expires,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def create_course_banner_token(course_id: str, banner_key: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=2)
    return jwt.encode({"typ": "course_banner", "course_id": course_id, "banner_key": banner_key, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)
