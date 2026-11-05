import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.progress import CourseProgressResponse, LessonProgressResponse
from app.database import get_db
from app.models import Course, Enrollment, Lesson, LessonProgress, User

router = APIRouter(prefix="/courses/{course_id}/progress", tags=["Progress"])


def require_enrollment(course_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> None:
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id == user_id)
        .first()
    )
    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Enroll in the course to track progress",
        )


def to_response(progress: LessonProgress, course_id: uuid.UUID) -> LessonProgressResponse:
    return LessonProgressResponse(
        course_id=str(course_id),
        lesson_id=str(progress.lesson_id),
        completed_at=progress.completed_at,
    )


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonProgressResponse,
)
def complete_lesson(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonProgressResponse:
    require_enrollment(course_id, current_user.id, db)

    lesson = (
        db.query(Lesson)
        .filter(Lesson.id == lesson_id, Lesson.course_id == course_id)
        .first()
    )
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found in this course",
        )

    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == current_user.id,
            LessonProgress.lesson_id == lesson.id,
        )
        .first()
    )
    if progress is None:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson.id)
        db.add(progress)
        db.commit()
        db.refresh(progress)

    return to_response(progress, course_id)


@router.get("/me", response_model=CourseProgressResponse)
def get_my_course_progress(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseProgressResponse:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )
    require_enrollment(course_id, current_user.id, db)

    total_lessons = db.query(Lesson).filter(Lesson.course_id == course_id).count()
    completed_ids = [
        row[0]
        for row in (
            db.query(LessonProgress.lesson_id)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .filter(
                LessonProgress.user_id == current_user.id,
                Lesson.course_id == course_id,
            )
            .all()
        )
    ]
    completed_count = len(completed_ids)
    progress_percent = round(completed_count / total_lessons * 100, 2) if total_lessons else 0.0

    return CourseProgressResponse(
        course_id=str(course_id),
        total_lessons=total_lessons,
        completed_lessons=completed_count,
        progress_percent=progress_percent,
        completed_lesson_ids=[str(lesson_id) for lesson_id in completed_ids],
    )
