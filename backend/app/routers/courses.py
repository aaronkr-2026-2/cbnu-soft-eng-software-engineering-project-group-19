import uuid
import hashlib
import html
import mimetypes
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
import jwt
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_author
from app.core.localization import get_course_translation, get_lesson_translation
from app.core.schemes.review import CourseReviewResponse
from app.core.schemes.course import (
    CourseCatalogResponse,
    CourseCreate,
    CourseOutlineLesson,
    CourseOutlineResponse,
    CourseResponse,
    CourseUpdate,
)
from app.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY, create_course_banner_token
from app.models import Course, CourseReview, CourseTranslation, Enrollment, Lesson, LessonTranslation, User

router = APIRouter(prefix="/courses", tags=["Courses"])
RESOURCE_DIR = Path(__file__).resolve().parents[2] / "storage" / "course-materials"
BANNER_DIR = Path(__file__).resolve().parents[2] / "storage" / "lesson-banners"
COURSE_BANNER_DIR = Path(__file__).resolve().parents[2] / "storage" / "course-banners"
MAX_BANNER_BYTES = 8 * 1024 * 1024


def render_course_banner(course: Course) -> bytes:
    fingerprint = hashlib.sha256(f"{course.title}:{course.category}".encode()).hexdigest()
    hue = int(fingerprint[:4], 16) % 360
    title, category = html.escape(course.title[:60]), html.escape(course.category[:35])
    tagline = html.escape({"uz":"Kod yozing · Tajriba qiling · Natijani ko‘ring","en":"Code · Experiment · Build","ru":"Пишите код · Экспериментируйте · Создавайте","ko":"코드 작성 · 실험 · 만들기"}.get(course.language, "Code · Experiment · Build"))
    topic = f"{course.title} {course.category}".lower()
    if "python" in topic:
        palette, icon = ("#102e2a", "#2ca98b", "#d7f36a"), '<path d="M914 125h76a34 34 0 0 1 34 34v45h-93a31 31 0 0 0-31 31v-76a34 34 0 0 1 34-34Z" fill="#d7f36a"/><circle cx="968" cy="153" r="5" fill="#173b35"/><path d="M1007 365h-76a34 34 0 0 1-34-34v-45h93a31 31 0 0 0 31-31v76a34 34 0 0 1-34 34Z" fill="#64d5bd"/><circle cx="953" cy="337" r="5" fill="#173b35"/><path d="M988 204v72" stroke="#fff" stroke-opacity=".55" stroke-width="5" stroke-dasharray="7 9"/>'
    elif "api" in topic or "fastapi" in topic:
        palette, icon = ("#102d40", "#1787c9", "#a9e5ff"), '<rect x="887" y="134" width="108" height="66" rx="15" fill="#d8f5ff"/><rect x="887" y="223" width="108" height="66" rx="15" fill="#8bd7f4"/><rect x="887" y="312" width="108" height="45" rx="15" fill="#43acd8"/><path d="M1006 167h34v138h-34M1006 256h34" fill="none" stroke="#d7f36a" stroke-width="7" stroke-linecap="round"/><circle cx="913" cy="167" r="6" fill="#1686ba"/><circle cx="913" cy="256" r="6" fill="#1686ba"/><path d="M939 167h39m-39 89h39m-39 78h39" stroke="#1686ba" stroke-width="6" stroke-linecap="round"/>'
    elif "git" in topic or "linux" in topic or "devops" in topic:
        palette, icon = ("#302044", "#895ac6", "#e8d7ff"), '<path d="M950 151v173M950 205h74v72M950 250h-71v72" fill="none" stroke="#e9dcff" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="950" cy="142" r="19" fill="#d7f36a"/><circle cx="1031" cy="285" r="19" fill="#8fe3ca"/><circle cx="870" cy="330" r="19" fill="#ffb990"/><rect x="875" y="178" width="154" height="68" rx="12" fill="#170f23" stroke="#c5a9ef" stroke-width="4"/><path d="m899 207 13 12-13 12m27 0h30" fill="none" stroke="#d7f36a" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    else:
        palette, icon = ("#2f394f", "#667da8", "#e1edff"), '<rect x="879" y="143" width="150" height="198" rx="20" fill="#fff" fill-opacity=".9"/><path d="M910 191h89m-89 34h89m-89 34h62m-62 34h76" stroke="#647ba3" stroke-width="9" stroke-linecap="round"/><path d="m965 111 13 26 28 4-20 20 5 28-26-13-25 13 5-28-21-20 29-4Z" fill="#d7f36a"/>'
    dark, accent, soft = palette
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 480" role="img" aria-label="{title}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{dark}"/><stop offset="1" stop-color="{accent}"/></linearGradient><pattern id="p" width="38" height="38" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.5" fill="#fff" fill-opacity=".16"/></pattern></defs>
<rect width="1200" height="480" rx="30" fill="url(#g)"/><rect width="1200" height="480" rx="30" fill="url(#p)"/><circle cx="954" cy="245" r="196" fill="#fff" fill-opacity=".07"/><circle cx="954" cy="245" r="145" fill="none" stroke="#fff" stroke-opacity=".14" stroke-width="2"/>
{icon}<text x="68" y="112" fill="{soft}" font-family="Arial,sans-serif" font-size="22" font-weight="700" letter-spacing="4">{category.upper()}</text><text x="68" y="218" fill="#fff" font-family="Arial,sans-serif" font-size="48" font-weight="700">{title}</text><text x="68" y="282" fill="#fff" fill-opacity=".78" font-family="Arial,sans-serif" font-size="24">{tagline}</text><rect x="68" y="330" width="68" height="6" rx="3" fill="#d7f36a"/></svg>'''
    return svg.encode("utf-8")


def save_course_banner(course: Course, db: Session) -> None:
    COURSE_BANNER_DIR.mkdir(parents=True, exist_ok=True)
    old_key = course.banner_key
    key = f"{uuid.uuid4().hex}.svg"
    (COURSE_BANNER_DIR / key).write_bytes(render_course_banner(course))
    course.banner_key = key
    db.commit()
    db.refresh(course)
    if old_key:
        (COURSE_BANNER_DIR / Path(old_key).name).unlink(missing_ok=True)


def store_course_banner(course: Course, image_bytes: bytes, extension: str, db: Session) -> None:
    COURSE_BANNER_DIR.mkdir(parents=True, exist_ok=True)
    old_key = course.banner_key
    key = f"{uuid.uuid4().hex}.{extension}"
    path = COURSE_BANNER_DIR / key
    path.write_bytes(image_bytes)
    course.banner_key = key
    try:
        db.commit()
        db.refresh(course)
    except Exception:
        path.unlink(missing_ok=True)
        db.rollback()
        raise
    if old_key:
        (COURSE_BANNER_DIR / Path(old_key).name).unlink(missing_ok=True)


def course_banner_url(course: Course) -> str | None:
    if not course.banner_key:
        return None
    url = f"/courses/{course.id}/banner?v={course.banner_key}"
    if not course.is_published:
        url += f"&token={create_course_banner_token(str(course.id), course.banner_key)}"
    return url


def to_response(course: Course) -> CourseResponse:
    return CourseResponse(
        id=str(course.id),
        title=course.title,
        description=course.description,
        category=course.category,
        price_uzs=course.price_uzs,
        language=course.language,
        level=course.level,
        is_published=course.is_published,
        owner_id=str(course.owner_id),
        banner_url=course_banner_url(course),
    )


def to_catalog_response(course: Course, language: str = "uz", db: Session | None = None) -> CourseCatalogResponse:
    translation = get_course_translation(course, language, db) if db else None
    return CourseCatalogResponse(
        id=str(course.id),
        title=translation.title if translation else course.title,
        description=translation.description if translation else course.description,
        category=translation.category if translation else course.category,
        price_uzs=course.price_uzs,
        language=course.language,
        level=course.level,
        is_published=course.is_published,
        display_language=translation.language if translation else course.language,
        translated=translation is not None,
        banner_url=course_banner_url(course),
    )


@router.get("/catalog", response_model=list[CourseCatalogResponse])
def list_published_courses(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    language: Literal["uz", "en", "ru", "ko"] = Query(default="uz"),
    db: Session = Depends(get_db),
) -> list[CourseCatalogResponse]:
    query = db.query(Course).filter(Course.is_published.is_(True), Course.language == language)
    search = q.strip() if q else ""
    if search:
        pattern = f"%{search}%"
        matching_lessons = db.query(Lesson.course_id).filter(
            or_(Lesson.title.ilike(pattern), Lesson.content.ilike(pattern))
        )
        query = query.filter(or_(Course.title.ilike(pattern), Course.description.ilike(pattern), Course.category.ilike(pattern), Course.id.in_(matching_lessons)))
    courses = query.order_by(Course.created_at.desc()).all()
    return [to_catalog_response(course, language, db) for course in courses]


@router.get("/catalog/{course_id}/outline", response_model=CourseOutlineResponse)
def get_published_course_outline(
    course_id: uuid.UUID,
    language: Literal["uz", "en", "ru", "ko"] = Query(default="uz"),
    db: Session = Depends(get_db),
) -> CourseOutlineResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.is_published.is_(True)).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published course not found")
    lessons = db.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.position, Lesson.created_at).all()
    review_count, average_rating = db.query(
        func.count(CourseReview.id), func.avg(CourseReview.rating)
    ).filter(CourseReview.course_id == course_id).one()
    review_rows = (
        db.query(CourseReview, User.full_name)
        .join(User, User.id == CourseReview.user_id)
        .filter(CourseReview.course_id == course_id)
        .order_by(CourseReview.created_at.desc())
        .limit(6)
        .all()
    )
    course_translation = get_course_translation(course, language, db)
    outline_lessons = []
    for lesson in lessons:
        lesson_translation = get_lesson_translation(lesson, course, language, db)
        outline_lessons.append(CourseOutlineLesson(
            title=lesson_translation.title if lesson_translation else lesson.title,
            position=lesson.position,
            banner_url=f"/courses/{course.id}/lessons/{lesson.id}/banner" if lesson.banner_key else None,
        ))
    return CourseOutlineResponse(
        id=str(course.id), title=course_translation.title if course_translation else course.title,
        description=course_translation.description if course_translation else course.description,
        category=course_translation.category if course_translation else course.category,
        language=course.language, level=course.level, price_uzs=course.price_uzs,
        display_language=course_translation.language if course_translation else course.language,
        translated=course_translation is not None,
        banner_url=course_banner_url(course),
        lessons=outline_lessons,
        average_rating=round(float(average_rating), 1) if average_rating is not None else None,
        review_count=review_count,
        reviews=[CourseReviewResponse(
            id=review.id, reviewer_name=name, rating=review.rating,
            comment=review.comment, created_at=review.created_at,
        ) for review, name in review_rows],
    )


@router.get("/catalog/{course_id}", response_model=CourseCatalogResponse)
def get_published_course(
    course_id: uuid.UUID,
    language: Literal["uz", "en", "ru", "ko"] = Query(default="uz"),
    db: Session = Depends(get_db),
) -> CourseCatalogResponse:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.is_published.is_(True))
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published course not found",
        )
    return to_catalog_response(course, language, db)


def get_owned_course(
    course_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session,
) -> Course:
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


@router.post("/{course_id}/publish", response_model=CourseResponse)
def publish_course(
    course_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = get_owned_course(course_id, current_user.id, db)
    if not course.banner_key:
        save_course_banner(course, db)
    course.is_published = True
    db.commit()
    db.refresh(course)
    return to_response(course)


@router.post("/{course_id}/unpublish", response_model=CourseResponse)
def unpublish_course(
    course_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = get_owned_course(course_id, current_user.id, db)
    course.is_published = False
    db.commit()
    db.refresh(course)
    return to_response(course)


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = Course(
        title=course_data.title,
        description=course_data.description,
        category=course_data.category.strip(),
        price_uzs=course_data.price_uzs,
        language=course_data.language,
        level=course_data.level,
        owner_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    save_course_banner(course, db)
    return to_response(course)


@router.get("/{course_id}/banner")
def read_course_banner(course_id: uuid.UUID, token: str | None = None, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None or not course.banner_key:
        raise HTTPException(status_code=404, detail="Course banner not found")
    if not course.is_published:
        try:
            payload = jwt.decode(token or "", SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=404, detail="Course banner not found") from None
        if payload.get("typ") != "course_banner" or payload.get("course_id") != str(course_id) or payload.get("banner_key") != course.banner_key:
            raise HTTPException(status_code=404, detail="Course banner not found")
    path = COURSE_BANNER_DIR / Path(course.banner_key).name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Course banner not found")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, headers={"Cache-Control":"public, max-age=3600, immutable", "X-Content-Type-Options":"nosniff"})


@router.put("/{course_id}/banner", response_model=CourseResponse)
async def upload_course_banner(
    course_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = get_owned_course(course_id, current_user.id, db)
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    extensions = {"image/png":"png", "image/jpeg":"jpg", "image/webp":"webp"}
    if content_type not in extensions:
        raise HTTPException(status_code=415, detail="Choose a PNG, JPEG, or WebP banner")
    image = bytearray()
    async for chunk in request.stream():
        image.extend(chunk)
        if len(image) > MAX_BANNER_BYTES:
            raise HTTPException(status_code=413, detail="Banner must be 8 MB or smaller")
    data = bytes(image)
    valid = (content_type == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n")) or (content_type == "image/jpeg" and data.startswith(b"\xff\xd8\xff")) or (content_type == "image/webp" and len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    if not valid:
        raise HTTPException(status_code=415, detail="The banner file does not match its selected image type")
    store_course_banner(course, data, extensions[content_type], db)
    return to_response(course)


@router.get("", response_model=list[CourseResponse])
def list_my_courses(
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> list[CourseResponse]:
    courses = (
        db.query(Course)
        .filter(Course.owner_id == current_user.id)
        .order_by(Course.created_at.desc())
        .all()
    )
    return [to_response(course) for course in courses]


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: uuid.UUID,
    course_data: CourseUpdate,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.owner_id == current_user.id)
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    updates = course_data.model_dump(exclude_unset=True)
    if updates.get("language") and updates["language"] != course.language and db.query(Lesson.id).filter(Lesson.course_id == course.id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A course language is fixed after its first lesson. Create a new course in the other language so lesson text stays correctly labeled.")
    if {"title", "description", "language"} & updates.keys():
        db.query(CourseTranslation).filter(CourseTranslation.course_id == course.id).delete(synchronize_session=False)
    if updates.get("language") and updates["language"] != course.language:
        lesson_ids = db.query(Lesson.id).filter(Lesson.course_id == course.id)
        db.query(LessonTranslation).filter(LessonTranslation.lesson_id.in_(lesson_ids)).delete(synchronize_session=False)
    for field, value in updates.items():
        if value is not None or field == "description":
            setattr(course, field, value)

    db.commit()
    db.refresh(course)
    generated_banner = bool(course.banner_key and course.banner_key.endswith(".svg"))
    if not course.banner_key or (generated_banner and {"title", "category", "language"} & updates.keys()):
        save_course_banner(course, db)
    return to_response(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> None:
    course = (
        db.query(Course)
        .filter(Course.id == course_id, Course.owner_id == current_user.id)
        .first()
    )
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    resource_keys = [
        row[0] for row in db.query(Lesson.resource_key).filter(Lesson.course_id == course.id, Lesson.resource_key.is_not(None)).all()
    ]
    banner_keys = [
        row[0] for row in db.query(Lesson.banner_key).filter(Lesson.course_id == course.id, Lesson.banner_key.is_not(None)).all()
    ]
    db.delete(course)
    db.commit()
    for resource_key in resource_keys:
        (RESOURCE_DIR / Path(resource_key).name).unlink(missing_ok=True)
    for banner_key in banner_keys:
        (BANNER_DIR / Path(banner_key).name).unlink(missing_ok=True)
