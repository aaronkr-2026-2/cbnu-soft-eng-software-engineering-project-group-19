import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
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
from app.models import Course, CourseReview, Enrollment, Lesson, User

router = APIRouter(prefix="/courses", tags=["Courses"])


def to_response(course: Course) -> CourseResponse:
    return CourseResponse(
        id=str(course.id),
        title=course.title,
        description=course.description,
        language=course.language,
        level=course.level,
        is_published=course.is_published,
        owner_id=str(course.owner_id),
    )


def to_catalog_response(course: Course) -> CourseCatalogResponse:
    return CourseCatalogResponse(
        id=str(course.id),
        title=course.title,
        description=course.description,
        language=course.language,
        level=course.level,
        is_published=course.is_published,
    )


@router.get("/catalog", response_model=list[CourseCatalogResponse])
def list_published_courses(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    language: Literal["uz", "en", "ru", "ko"] | None = None,
    level: Literal["beginner", "intermediate", "advanced"] | None = None,
    db: Session = Depends(get_db),
) -> list[CourseCatalogResponse]:
    query = db.query(Course).filter(Course.is_published.is_(True))
    search = q.strip() if q else ""
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Course.title.ilike(pattern), Course.description.ilike(pattern)))
    if language:
        query = query.filter(Course.language == language)
    if level:
        query = query.filter(Course.level == level)
    courses = query.order_by(Course.created_at.desc()).all()
    return [to_catalog_response(course) for course in courses]


@router.get("/catalog/{course_id}/outline", response_model=CourseOutlineResponse)
def get_published_course_outline(
    course_id: uuid.UUID,
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
    return CourseOutlineResponse(
        id=str(course.id), title=course.title, description=course.description,
        language=course.language, level=course.level,
        lessons=[CourseOutlineLesson(title=lesson.title, position=lesson.position) for lesson in lessons],
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
    return to_catalog_response(course)


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = get_owned_course(course_id, current_user.id, db)
    course.is_published = True
    db.commit()
    db.refresh(course)
    return to_response(course)


@router.post("/{course_id}/unpublish", response_model=CourseResponse)
def unpublish_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseResponse:
    course = Course(
        title=course_data.title,
        description=course_data.description,
        language=course_data.language,
        level=course_data.level,
        owner_id=current_user.id,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return to_response(course)


@router.get("", response_model=list[CourseResponse])
def list_my_courses(
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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

    for field, value in course_data.model_dump(exclude_unset=True).items():
        if value is not None or field == "description":
            setattr(course, field, value)

    db.commit()
    db.refresh(course)
    return to_response(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
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

    db.delete(course)
    db.commit()
