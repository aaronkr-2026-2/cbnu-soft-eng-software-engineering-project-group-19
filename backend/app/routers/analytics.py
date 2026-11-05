import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.analytics import CourseAnalyticsResponse
from app.database import get_db
from app.models import Course, CourseReview, Enrollment, FinalExamAttempt, Lesson, LessonProgress, User

router = APIRouter(prefix="/courses/{course_id}/analytics", tags=["Course Analytics"])


@router.get("", response_model=CourseAnalyticsResponse)
def get_course_analytics(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseAnalyticsResponse:
    course = db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrollment_ids = [row[0] for row in db.query(Enrollment.user_id).filter(Enrollment.course_id == course_id).all()]
    enrollment_count = len(enrollment_ids)
    lesson_count = db.query(Lesson.id).filter(Lesson.course_id == course_id).count()
    completed_learners = 0
    if lesson_count and enrollment_ids:
        completion_rows = (
            db.query(LessonProgress.user_id, func.count(func.distinct(LessonProgress.lesson_id)))
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .filter(Lesson.course_id == course_id, LessonProgress.user_id.in_(enrollment_ids))
            .group_by(LessonProgress.user_id)
            .all()
        )
        completed_learners = sum(1 for _, completed_count in completion_rows if completed_count == lesson_count)

    review_count, average_rating = db.query(
        func.count(CourseReview.id), func.avg(CourseReview.rating)
    ).filter(CourseReview.course_id == course_id).one()
    exam_attempts, exam_passes = db.query(
        func.count(FinalExamAttempt.id), func.count(FinalExamAttempt.id).filter(FinalExamAttempt.passed.is_(True))
    ).filter(FinalExamAttempt.course_id == course_id).one()
    exam_attempts = exam_attempts or 0
    exam_passes = exam_passes or 0

    return CourseAnalyticsResponse(
        course_id=course.id,
        course_title=course.title,
        enrollment_count=enrollment_count,
        completed_learners=completed_learners,
        completion_rate=round(completed_learners / enrollment_count * 100, 1) if enrollment_count else 0.0,
        average_rating=round(float(average_rating), 1) if average_rating is not None else None,
        review_count=review_count or 0,
        final_exam_attempts=exam_attempts,
        final_exam_passes=exam_passes,
        final_exam_pass_rate=round(exam_passes / exam_attempts * 100, 1) if exam_attempts else 0.0,
    )
