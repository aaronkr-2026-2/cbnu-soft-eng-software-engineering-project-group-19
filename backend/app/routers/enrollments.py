import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemes.enrollment import EnrollmentResponse
from app.database import get_db
from app.models import Course, Enrollment, User

router = APIRouter(tags=["Enrollments"])


def to_response(enrollment: Enrollment, course: Course) -> EnrollmentResponse:
    return EnrollmentResponse(
        id=str(enrollment.id),
        course_id=str(course.id),
        course_title=course.title,
        enrolled_at=enrollment.enrolled_at,
    )


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def enroll_in_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
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

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )
    if existing_enrollment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this course",
        )

    enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return to_response(enrollment, course)


@router.get("/enrollments/me", response_model=list[EnrollmentResponse])
def list_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EnrollmentResponse]:
    records = (
        db.query(Enrollment, Course)
        .join(Course, Course.id == Enrollment.course_id)
        .filter(Enrollment.user_id == current_user.id)
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )
    return [to_response(enrollment, course) for enrollment, course in records]
