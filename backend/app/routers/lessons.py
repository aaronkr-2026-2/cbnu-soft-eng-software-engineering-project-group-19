import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.database import get_db
from app.models import Course, Enrollment, Lesson, User

router = APIRouter(prefix="/courses/{course_id}/lessons", tags=["Lessons"])


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


def to_response(lesson: Lesson) -> LessonResponse:
    return LessonResponse(
        id=str(lesson.id),
        course_id=str(lesson.course_id),
        title=lesson.title,
        content=lesson.content,
        position=lesson.position,
    )


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: uuid.UUID,
    lesson_data: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonResponse:
    course = get_owned_course(course_id, current_user.id, db)
    lesson = Lesson(
        course_id=course.id,
        title=lesson_data.title,
        content=lesson_data.content,
        position=lesson_data.position,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return to_response(lesson)


@router.get("", response_model=list[LessonResponse])
def list_lessons(
    course_id: uuid.UUID,
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
    return [to_response(lesson) for lesson in lessons]


@router.put("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    lesson_data: LessonUpdate,
    current_user: User = Depends(get_current_user),
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

    for field, value in lesson_data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(lesson, field, value)

    db.commit()
    db.refresh(lesson)
    return to_response(lesson)


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
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

    db.delete(lesson)
    db.commit()
