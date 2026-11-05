import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.review import CourseReviewUpsert, MyCourseReviewResponse
from app.database import get_db
from app.models import Course, CourseReview, Enrollment, Lesson, LessonProgress, User

router = APIRouter(prefix="/courses/{course_id}/reviews", tags=["Course Reviews"])


def require_enrollment(course_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    enrollment = db.query(Enrollment.id).filter(
        Enrollment.course_id == course_id, Enrollment.user_id == user_id
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course to review it")
    return course


@router.get("/me", response_model=MyCourseReviewResponse)
def get_my_course_review(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MyCourseReviewResponse:
    require_enrollment(course_id, current_user.id, db)
    review = db.query(CourseReview).filter(
        CourseReview.course_id == course_id, CourseReview.user_id == current_user.id
    ).first()
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return MyCourseReviewResponse(id=review.id, rating=review.rating, comment=review.comment, updated_at=review.updated_at)


@router.put("/me", response_model=MyCourseReviewResponse)
def upsert_my_course_review(
    course_id: uuid.UUID,
    review_data: CourseReviewUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MyCourseReviewResponse:
    course = require_enrollment(course_id, current_user.id, db)
    lesson_ids = [row[0] for row in db.query(Lesson.id).filter(Lesson.course_id == course.id).all()]
    if not lesson_ids:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Complete the course lessons before reviewing")
    completed_count = db.query(LessonProgress.id).filter(
        LessonProgress.user_id == current_user.id, LessonProgress.lesson_id.in_(lesson_ids)
    ).count()
    if completed_count != len(lesson_ids):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Complete every lesson before reviewing the course")

    review = db.query(CourseReview).filter(
        CourseReview.course_id == course_id, CourseReview.user_id == current_user.id
    ).first()
    comment = review_data.comment.strip() if review_data.comment and review_data.comment.strip() else None
    if review is None:
        review = CourseReview(user_id=current_user.id, course_id=course_id, rating=review_data.rating, comment=comment)
        db.add(review)
    else:
        review.rating = review_data.rating
        review.comment = comment
    db.commit()
    db.refresh(review)
    return MyCourseReviewResponse(id=review.id, rating=review.rating, comment=review.comment, updated_at=review.updated_at)
