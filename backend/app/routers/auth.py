import base64
import binascii
import os
import smtplib
import time
import uuid
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.user import (
    AvatarUpload,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserLogin,
    UserPasswordChange,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.core.security import ALGORITHM, SECRET_KEY, create_access_token, create_password_reset_token, hash_password, verify_password
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
AVATAR_DIR = Path(__file__).resolve().parents[2] / "storage" / "avatars"
MAX_AVATAR_BYTES = 2 * 1024 * 1024
_password_reset_attempts: dict[str, list[float]] = {}


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        account_type=user.account_type,
        preferred_language=user.preferred_language,
        age=user.age,
        bio=user.bio,
        avatar_url="/auth/me/avatar" if user.avatar_url else None,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
) -> UserResponse:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        account_type=user_data.account_type,
        hashed_password=hash_password(user_data.password),
        preferred_language=user_data.preferred_language,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return to_user_response(new_user)


@router.post("/login", response_model=Token)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    user = db.query(User).filter(User.email == user_data.email).first()
    if user is None or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_type != user_data.account_type:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account uses a different sign-in page",
        )

    access_token = create_access_token(str(user.id), user.token_version)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return to_user_response(current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    if user_data.email is not None and user_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        current_user.email = user_data.email

    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    if user_data.preferred_language is not None:
        current_user.preferred_language = user_data.preferred_language
    if "age" in user_data.model_fields_set:
        current_user.age = user_data.age
    if "bio" in user_data.model_fields_set:
        current_user.bio = user_data.bio

    db.commit()
    db.refresh(current_user)
    return to_user_response(current_user)


@router.get("/me/avatar")
def get_my_avatar(
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    if not current_user.avatar_url or not current_user.avatar_url.startswith("/media/avatars/"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found")
    filename = Path(current_user.avatar_url).name
    avatar_path = (AVATAR_DIR / filename).resolve()
    if avatar_path.parent != AVATAR_DIR.resolve() or not avatar_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found")
    media_type = {".jpg":"image/jpeg", ".png":"image/png", ".webp":"image/webp"}.get(avatar_path.suffix)
    if not media_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile photo not found")
    return FileResponse(avatar_path, media_type=media_type, headers={"Cache-Control":"private, no-store"})


@router.put("/me/avatar", response_model=UserResponse)
def update_my_avatar(
    avatar_data: AvatarUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    try:
        header, encoded = avatar_data.data_url.split(",", 1)
        mime_type = header.removeprefix("data:").removesuffix(";base64")
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data")

    signatures = {
        "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
        "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
        "image/webp": (".webp", lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
    }
    signature = signatures.get(mime_type)
    if not signature or len(image_bytes) > MAX_AVATAR_BYTES or len(image_bytes) < 16 or not signature[1](image_bytes):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Use a JPEG, PNG, or WebP image up to 2 MB")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{signature[0]}"
    destination = AVATAR_DIR / filename
    destination.write_bytes(image_bytes)
    old_avatar_url = current_user.avatar_url
    current_user.avatar_url = f"/media/avatars/{filename}"
    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        destination.unlink(missing_ok=True)
        db.rollback()
        raise

    if old_avatar_url and old_avatar_url.startswith("/media/avatars/"):
        old_file = AVATAR_DIR / Path(old_avatar_url).name
        old_file.unlink(missing_ok=True)
    return to_user_response(current_user)


@router.post("/change-password")
def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    current_user.token_version += 1
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/password-reset/request")
def request_password_reset(
    reset_request: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    recent = [attempt for attempt in _password_reset_attempts.get(client_ip, []) if now - attempt < 900]
    if len(recent) >= 5:
        raise HTTPException(status_code=429, detail="Too many password reset requests. Try again later.")
    recent.append(now)
    _password_reset_attempts[client_ip] = recent

    smtp_host = os.getenv("SMTP_HOST")
    smtp_from = os.getenv("SMTP_FROM")
    smtp_username = (os.getenv("SMTP_USERNAME") or "").strip()
    # Google displays App Passwords in groups; remove copy/pasted whitespace.
    smtp_password = "".join((os.getenv("SMTP_PASSWORD") or "").split())
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    default_frontend_url = f"{render_url}/app" if render_url else "http://127.0.0.1:8000/app"
    frontend_url = (os.getenv("FRONTEND_BASE_URL") or default_frontend_url).rstrip("/")
    if not frontend_url.endswith("/app"):
        frontend_url += "/app"
    if not smtp_host or not smtp_from or not smtp_username or not smtp_password:
        raise HTTPException(status_code=503, detail="Password reset email is not configured on this server")

    user = db.query(User).filter(User.email == reset_request.email).first()
    if user is None:
        return {"message": "If that email belongs to an account, a reset link has been sent."}

    token = create_password_reset_token(str(user.id), user.token_version)
    reset_query = urlencode({"token": token, "account_type": user.account_type})
    reset_url = f"{frontend_url}/reset-password.html?{reset_query}"
    message = EmailMessage()
    message["Subject"] = "Reset your StudyFlow AI password"
    message["From"] = smtp_from
    message["To"] = user.email
    message.set_content(
        "We received a request to reset your StudyFlow AI password. "
        f"Open this link within 30 minutes: {reset_url}\n\n"
        "If you did not request this, ignore this email."
    )
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(smtp_username, smtp_password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        raise HTTPException(status_code=503, detail="Unable to send the reset email right now") from None
    return {"message": "If that email belongs to an account, a reset link has been sent."}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    try:
        payload = jwt.decode(reset_data.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("typ") != "password_reset":
            raise jwt.InvalidTokenError("Wrong token type")
        user_id = uuid.UUID(payload["sub"])
        token_version = payload["ver"]
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired") from None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.token_version != token_version:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    user.hashed_password = hash_password(reset_data.new_password)
    user.token_version += 1
    db.commit()
    return {"message": "Password updated. You can now sign in with the new password."}
