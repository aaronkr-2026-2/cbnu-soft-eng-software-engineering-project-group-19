import uuid
import logging
import os
import html
import mimetypes
from pathlib import Path
from typing import Literal

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_author
from app.core.ai import AIConfigurationError, AIProviderError, generate_lesson_banner
from app.core.localization import get_lesson_translation
from app.core.schemes.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.core.security import ALGORITHM, SECRET_KEY, create_lesson_banner_token, create_lesson_resource_token
from app.database import get_db
from app.models import Course, CourseModule, Enrollment, Lesson, LessonTranslation, User, VideoWatchProgress

router = APIRouter(prefix="/courses/{course_id}/lessons", tags=["Lessons"])
RESOURCE_DIR = Path(__file__).resolve().parents[2] / "storage" / "course-materials"
BANNER_DIR = Path(__file__).resolve().parents[2] / "storage" / "lesson-banners"
logger = logging.getLogger(__name__)
MAX_RESOURCE_BYTES = 150 * 1024 * 1024
MAX_TOTAL_RESOURCE_BYTES = 1024 * 1024 * 1024
MAX_BANNER_BYTES = 8 * 1024 * 1024
RESOURCE_TYPES = {
    "application/pdf": ("pdf", ".pdf"),
    "video/mp4": ("video", ".mp4"),
    "video/webm": ("video", ".webm"),
    "audio/mpeg": ("audio", ".mp3"),
    "audio/mp4": ("audio", ".m4a"),
    "audio/wav": ("audio", ".wav"),
    "audio/ogg": ("audio", ".ogg"),
    "audio/webm": ("audio", ".webm"),
}


def has_expected_signature(content_type: str, header: bytes) -> bool:
    if content_type == "application/pdf":
        return header.startswith(b"%PDF-")
    if content_type in {"video/mp4", "audio/mp4"}:
        return len(header) >= 12 and header[4:8] == b"ftyp"
    if content_type in {"video/webm", "audio/webm"}:
        return header.startswith(b"\x1aE\xdf\xa3")
    if content_type == "audio/mpeg":
        return header.startswith(b"ID3") or (len(header) > 1 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)
    if content_type == "audio/wav":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WAVE"
    if content_type == "audio/ogg":
        return header.startswith(b"OggS")
    return False


def get_owned_course(course_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Course:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.owner_id == user_id)
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    return course


def get_readable_course(course_id: uuid.UUID, user: User, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if course.owner_id == user.id:
        return course
    if not course.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    enrollment = (
        db.query(Enrollment.id)
        .filter(
            Enrollment.course_id == course.id,
            Enrollment.user_id == user.id,
        )
        .first()
    )
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def to_response(
    lesson: Lesson,
    course: Course | None = None,
    translation: LessonTranslation | None = None,
) -> LessonResponse:
    resource_url = None
    if lesson.resource_key:
        token = create_lesson_resource_token(
            str(lesson.course_id), str(lesson.id), lesson.resource_key
        )
        resource_url = f"/courses/{lesson.course_id}/lessons/{lesson.id}/resource?token={token}"
    banner_url = None
    if lesson.banner_key:
        banner_url = f"/courses/{lesson.course_id}/lessons/{lesson.id}/banner?v={lesson.banner_key}"
        if course and not course.is_published:
            banner_url += f"&token={create_lesson_banner_token(str(lesson.course_id), str(lesson.id), lesson.banner_key)}"
    return LessonResponse(
        id=str(lesson.id),
        course_id=str(lesson.course_id),
        title=translation.title if translation else lesson.title,
        content=translation.content if translation else lesson.content,
        resource_type=lesson.resource_type,
        resource_url=resource_url,
        resource_mime_type=lesson.resource_mime_type,
        external_video_url=lesson.external_video_url,
        banner_url=banner_url,
        content_language=translation.language if translation else (course.language if course else "uz"),
        translated=translation is not None,
        position=lesson.position,
        module_id=str(lesson.module_id) if lesson.module_id else None,
    )


def store_lesson_banner(lesson: Lesson, image_bytes: bytes, db: Session) -> None:
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = "png"
    elif image_bytes.lstrip().startswith(b"<svg") or b"<svg " in image_bytes[:256]:
        extension = "svg"
    else:
        raise ValueError("Generated lesson banner is not a supported image")
    old_key = lesson.banner_key
    key = f"{uuid.uuid4().hex}.{extension}"
    (BANNER_DIR / key).write_bytes(image_bytes)
    lesson.banner_key = key
    try:
        db.commit()
        db.refresh(lesson)
    except Exception:
        (BANNER_DIR / key).unlink(missing_ok=True)
        db.rollback()
        raise
    if old_key:
        (BANNER_DIR / Path(old_key).name).unlink(missing_ok=True)


def render_lesson_topic_banner(course: Course, lesson: Lesson) -> bytes:
    topic = f"{course.title} {lesson.title} {lesson.content[:600]}".lower()
    title = html.escape(lesson.title[:55])
    course_title = html.escape(course.title[:42])
    digest = uuid.uuid5(uuid.NAMESPACE_URL, f"{course.id}:{lesson.id}:{lesson.title}").int
    hue = digest % 360
    if "python" in topic or "for sikli" in topic or "python" in lesson.title.lower():
        art = '<path d="M926 130h69a31 31 0 0 1 31 31v42h-83a28 28 0 0 0-28 28v-70a31 31 0 0 1 31-31Z" fill="#d7f36a"/><circle cx="973" cy="157" r="5" fill="#173b35"/><path d="M1000 357h-69a31 31 0 0 1-31-31v-42h83a28 28 0 0 0 28-28v70a31 31 0 0 1-31 31Z" fill="#69d8bf"/><circle cx="953" cy="330" r="5" fill="#173b35"/><path d="M985 205v77" stroke="#fff" stroke-width="5" stroke-dasharray="7 8" opacity=".65"/>'
    elif "api" in topic or "http" in topic or "fastapi" in topic:
        art = '<rect x="888" y="137" width="126" height="60" rx="14" fill="#effaff"/><rect x="888" y="220" width="126" height="60" rx="14" fill="#a8e4f7"/><rect x="888" y="303" width="126" height="60" rx="14" fill="#55bddb"/><path d="M914 167h73m-73 83h73m-73 83h73" stroke="#15536e" stroke-width="7" stroke-linecap="round"/><path d="M1026 167h25v166h-25" fill="none" stroke="#d7f36a" stroke-width="6"/>'
    elif "git" in topic or "linux" in topic or "terminal" in topic or "devops" in topic:
        art = '<rect x="878" y="143" width="174" height="96" rx="17" fill="#171323" stroke="#e6d7ff" stroke-width="4"/><path d="m902 177 16 15-16 15m32 0h34" fill="none" stroke="#d7f36a" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><path d="M963 249v51m0 0h-66v30m66-30h68v30" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/><circle cx="897" cy="340" r="16" fill="#ffb88d"/><circle cx="1031" cy="340" r="16" fill="#8fe3ca"/>'
    else:
        art = '<rect x="882" y="145" width="155" height="198" rx="19" fill="#fff" fill-opacity=".92"/><path d="M912 190h95m-95 35h95m-95 35h68m-68 35h78" stroke="#587066" stroke-width="9" stroke-linecap="round"/><path d="m967 101 12 25 28 4-20 19 5 28-25-13-25 13 5-28-20-19 28-4Z" fill="#d7f36a"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 480" role="img" aria-label="{title}"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="hsl({hue} 42% 18%)"/><stop offset="1" stop-color="hsl({(hue+55)%360} 60% 36%)"/></linearGradient><pattern id="p" width="38" height="38" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#fff" opacity=".16"/></pattern></defs><rect width="1200" height="480" rx="30" fill="url(#g)"/><rect width="1200" height="480" rx="30" fill="url(#p)"/><circle cx="969" cy="245" r="175" fill="#fff" opacity=".07"/><circle cx="969" cy="245" r="131" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="2"/>{art}<text x="68" y="103" fill="#d7f36a" font-family="Arial,sans-serif" font-size="22" font-weight="700">{course_title}</text><text x="68" y="218" fill="#fff" font-family="Arial,sans-serif" font-size="48" font-weight="700">{title}</text><rect x="68" y="260" width="72" height="6" rx="3" fill="#d7f36a"/><text x="68" y="316" fill="#fff" fill-opacity=".68" font-family="Arial,sans-serif" font-size="22">{html.escape(course.category[:35])}</text></svg>'''
    return svg.encode("utf-8")


def store_author_lesson_banner(lesson: Lesson, image: bytes, content_type: str, db: Session) -> None:
    expected = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
    if content_type == "image/webp":
        valid = len(image) >= 12 and image[:4] == b"RIFF" and image[8:12] == b"WEBP"
    else:
        valid = content_type in expected and image.startswith(expected[content_type])
    if not valid:
        raise HTTPException(status_code=415, detail="The banner file does not match PNG, JPEG, or WebP format")
    BANNER_DIR.mkdir(parents=True, exist_ok=True)
    extension = {"image/png":"png", "image/jpeg":"jpg", "image/webp":"webp"}[content_type]
    key = f"{uuid.uuid4().hex}.{extension}"
    path = BANNER_DIR / key
    path.write_bytes(image)
    old_key = lesson.banner_key
    lesson.banner_key = key
    try:
        db.commit()
        db.refresh(lesson)
    except Exception:
        path.unlink(missing_ok=True)
        db.rollback()
        raise
    if old_key:
        (BANNER_DIR / Path(old_key).name).unlink(missing_ok=True)


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: uuid.UUID,
    lesson_data: LessonCreate,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> LessonResponse:
    course = get_owned_course(course_id, current_user.id, db)
    module = None
    if lesson_data.module_id:
        module = db.query(CourseModule).filter(
            CourseModule.id == lesson_data.module_id, CourseModule.course_id == course.id
        ).first()
        if module is None:
            raise HTTPException(status_code=404, detail="Module not found")
    lesson = Lesson(
        course_id=course.id,
        module_id=module.id if module else None,
        title=lesson_data.title,
        content=lesson_data.content,
        resource_type=lesson_data.resource_type,
        external_video_url=lesson_data.external_video_url,
        position=lesson_data.position,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    try:
        image = generate_lesson_banner(course.title, lesson.title, lesson.content)
    except AIConfigurationError:
        image = render_lesson_topic_banner(course, lesson)
    except AIProviderError:
        logger.warning("AI lesson banner generation failed for lesson %s; using topic illustration", lesson.id)
        image = render_lesson_topic_banner(course, lesson)
    store_lesson_banner(lesson, image, db)
    return to_response(lesson, course)


@router.delete("/{lesson_id}/resource", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson_resource(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> None:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course.id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    old_resource_key = lesson.resource_key
    lesson.resource_type = "text"
    lesson.resource_key = None
    lesson.resource_mime_type = None
    lesson.external_video_url = None
    db.query(VideoWatchProgress).filter_by(lesson_id=lesson.id).delete(synchronize_session=False)
    db.commit()
    if old_resource_key:
        (RESOURCE_DIR / Path(old_resource_key).name).unlink(missing_ok=True)


@router.put("/{lesson_id}/resource")
async def upload_lesson_resource(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> LessonResponse:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course.id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in RESOURCE_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload a PDF, MP4/WebM video, or MP3/M4A/WAV/OGG/WebM audio file")
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_RESOURCE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Resource must be 150 MB or smaller")

    RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
    stored_bytes = sum(
        item.stat().st_size
        for item in RESOURCE_DIR.iterdir()
        if item.is_file() and item.suffix != ".upload"
    )
    if stored_bytes >= MAX_TOTAL_RESOURCE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Course material storage limit reached")
    temporary_path = RESOURCE_DIR / f"{uuid.uuid4().hex}.upload"
    size = 0
    header = bytearray()
    try:
        with temporary_path.open("wb") as resource_file:
            async for chunk in request.stream():
                size += len(chunk)
                if size > MAX_RESOURCE_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Resource must be 150 MB or smaller")
                if stored_bytes + size > MAX_TOTAL_RESOURCE_BYTES:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Course material storage limit reached")
                if len(header) < 32:
                    header.extend(chunk[:32 - len(header)])
                resource_file.write(chunk)
        if size == 0 or not has_expected_signature(content_type, bytes(header)):
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="The uploaded file does not match its selected type")

        kind, extension = RESOURCE_TYPES[content_type]
        resource_key = f"{uuid.uuid4().hex}{extension}"
        destination = RESOURCE_DIR / resource_key
        temporary_path.replace(destination)
        old_resource_key = lesson.resource_key
        lesson.resource_type = kind
        lesson.resource_key = resource_key
        lesson.resource_mime_type = content_type
        lesson.external_video_url = None
        db.query(VideoWatchProgress).filter_by(lesson_id=lesson.id).delete(synchronize_session=False)
        try:
            db.commit()
            db.refresh(lesson)
        except Exception:
            destination.unlink(missing_ok=True)
            db.rollback()
            raise
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    if old_resource_key:
        (RESOURCE_DIR / Path(old_resource_key).name).unlink(missing_ok=True)
    return to_response(lesson, course)


@router.get("/{lesson_id}/resource")
def read_lesson_resource(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    token: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Resource link expired or invalid") from error

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
    if (
        lesson is None
        or payload.get("typ") != "lesson_resource"
        or payload.get("course_id") != str(course_id)
        or payload.get("lesson_id") != str(lesson_id)
        or payload.get("resource_key") != lesson.resource_key
        or not lesson.resource_key
        or not lesson.resource_mime_type
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course resource not found")

    resource_path = (RESOURCE_DIR / Path(lesson.resource_key).name).resolve()
    if resource_path.parent != RESOURCE_DIR.resolve() or not resource_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course resource not found")
    return FileResponse(
        resource_path,
        media_type=lesson.resource_mime_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("", response_model=list[LessonResponse])
def list_lessons(
    course_id: uuid.UUID,
    language: Literal["uz", "en", "ru", "ko"] = Query(default="uz"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LessonResponse]:
    course = get_readable_course(course_id, current_user, db)
    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course.id)
        .order_by(Lesson.position, Lesson.created_at)
        .all()
    )
    return [to_response(lesson, course, get_lesson_translation(lesson, course, language, db)) for lesson in lessons]


@router.get("/{lesson_id}/banner")
def read_lesson_banner(course_id: uuid.UUID, lesson_id: uuid.UUID, token: str | None = None, db: Session = Depends(get_db)):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course_id).first()
    if lesson is None or not lesson.banner_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson banner not found")
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None or not course.is_published:
        try:
            payload = jwt.decode(token or "", SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson banner not found") from None
        if (
            payload.get("typ") != "lesson_banner"
            or payload.get("course_id") != str(course_id)
            or payload.get("lesson_id") != str(lesson_id)
            or payload.get("banner_key") != lesson.banner_key
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson banner not found")
    path = BANNER_DIR / Path(lesson.banner_key).name
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson banner not found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control": "public, max-age=3600, immutable", "X-Content-Type-Options": "nosniff"})


@router.put("/{lesson_id}/banner", response_model=LessonResponse)
async def upload_lesson_banner(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> LessonResponse:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course.id).first()
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=415, detail="Choose a PNG, JPEG, or WebP banner")
    image = bytearray()
    async for chunk in request.stream():
        image.extend(chunk)
        if len(image) > MAX_BANNER_BYTES:
            raise HTTPException(status_code=413, detail="Banner must be 8 MB or smaller")
    store_author_lesson_banner(lesson, bytes(image), content_type, db)
    return to_response(lesson, course)


@router.post("/{lesson_id}/banner/generate", response_model=LessonResponse)
def create_lesson_banner(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> LessonResponse:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id, Lesson.course_id == course.id).first()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    try:
        image_bytes = generate_lesson_banner(course.title, lesson.title, lesson.content)
    except AIConfigurationError:
        image_bytes = render_lesson_topic_banner(course, lesson)
    except AIProviderError as exc:
        logger.warning("AI banner generation failed for lesson %s: %s", lesson.id, exc)
        image_bytes = render_lesson_topic_banner(course, lesson)
    store_lesson_banner(lesson, image_bytes, db)
    return to_response(lesson, course)


@router.put("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    lesson_data: LessonUpdate,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> LessonResponse:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id, Lesson.course_id == course.id)
        .first()
    )
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    values = lesson_data.model_dump(exclude_unset=True)
    if "module_id" in values and values["module_id"] is not None:
        module = db.query(CourseModule).filter(
            CourseModule.id == values["module_id"], CourseModule.course_id == course.id
        ).first()
        if module is None:
            raise HTTPException(status_code=404, detail="Module not found")
    old_banner_key = lesson.banner_key if {"title", "content"} & values.keys() else None
    db.query(LessonTranslation).filter(LessonTranslation.lesson_id == lesson.id).delete(synchronize_session=False)
    for field, value in values.items():
        if value is not None or field in {"external_video_url", "module_id"}:
            setattr(lesson, field, value)
    if old_banner_key:
        lesson.banner_key = None

    db.commit()
    db.refresh(lesson)
    if old_banner_key:
        (BANNER_DIR / Path(old_banner_key).name).unlink(missing_ok=True)
        try:
            image_bytes = generate_lesson_banner(course.title, lesson.title, lesson.content)
        except AIConfigurationError:
            image_bytes = render_lesson_topic_banner(course, lesson)
        except AIProviderError as exc:
            logger.warning("AI banner refresh failed for lesson %s: %s", lesson.id, exc)
            image_bytes = render_lesson_topic_banner(course, lesson)
        store_lesson_banner(lesson, image_bytes, db)
    return to_response(lesson, course)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> None:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id, Lesson.course_id == course.id)
        .first()
    )
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    old_resource_key = lesson.resource_key
    old_banner_key = lesson.banner_key
    db.delete(lesson)
    db.commit()
    if old_resource_key:
        (RESOURCE_DIR / Path(old_resource_key).name).unlink(missing_ok=True)
    if old_banner_key:
        (BANNER_DIR / Path(old_banner_key).name).unlink(missing_ok=True)
