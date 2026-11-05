import secrets
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.passkeys import consume_passkey_proof
from app.core.schemes.certificate import CertificateResponse, CertificateVerificationResponse
from app.database import get_db
from app.models import Course, CourseCertificate, Enrollment, FinalExamAttempt, Lesson, LessonProgress, User

router = APIRouter(prefix="/courses/{course_id}/certificate", tags=["Certificates"])
public_router = APIRouter(tags=["Certificates"])


def to_response(certificate: CourseCertificate) -> CertificateResponse:
    return CertificateResponse(
        id=certificate.id,
        certificate_code=certificate.certificate_code,
        recipient_name=certificate.recipient_name,
        course_title=certificate.course_title,
        issued_at=certificate.issued_at,
    )


def require_enrollment(course_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    enrollment = (
        db.query(Enrollment.id)
        .filter(Enrollment.course_id == course_id, Enrollment.user_id == user_id)
        .first()
    )
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Enroll in the course first")
    return course


@router.post("", response_model=CertificateResponse)
def issue_my_certificate(
    course_id: uuid.UUID,
    passkey_proof: str | None = Header(default=None, alias="X-Passkey-Proof"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CertificateResponse:
    course = require_enrollment(course_id, current_user.id, db)
    existing = (
        db.query(CourseCertificate)
        .filter(CourseCertificate.course_id == course_id, CourseCertificate.user_id == current_user.id)
        .first()
    )
    if existing is not None:
        return to_response(existing)

    lesson_count = db.query(Lesson.id).filter(Lesson.course_id == course_id).count()
    if lesson_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course without lessons cannot issue a certificate",
        )
    completed_count = (
        db.query(LessonProgress.id)
        .join(Lesson, Lesson.id == LessonProgress.lesson_id)
        .filter(Lesson.course_id == course_id, LessonProgress.user_id == current_user.id)
        .count()
    )
    if completed_count != lesson_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complete every lesson before requesting a certificate",
        )
    passed_exam = db.query(FinalExamAttempt.id).filter(
        FinalExamAttempt.course_id == course_id,
        FinalExamAttempt.user_id == current_user.id,
        FinalExamAttempt.passed.is_(True),
    ).first()
    if passed_exam is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pass the course final exam before requesting a certificate",
        )

    consume_passkey_proof(passkey_proof, current_user.id, "certificate", db)
    certificate = CourseCertificate(
        user_id=current_user.id,
        course_id=course_id,
        recipient_name=current_user.full_name,
        course_title=course.title,
        certificate_code=f"SF-{secrets.token_hex(16).upper()}",
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return to_response(certificate)


@router.get("/me", response_model=CertificateResponse)
def get_my_certificate(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CertificateResponse:
    require_enrollment(course_id, current_user.id, db)
    certificate = (
        db.query(CourseCertificate)
        .filter(CourseCertificate.course_id == course_id, CourseCertificate.user_id == current_user.id)
        .first()
    )
    if certificate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate has not been issued")
    return to_response(certificate)


@public_router.get(
    "/certificates/verify/{certificate_code}",
    response_model=CertificateVerificationResponse,
)
def verify_certificate(
    certificate_code: str,
    db: Session = Depends(get_db),
) -> CertificateVerificationResponse:
    normalized_code = certificate_code.strip().upper()
    certificate = (
        db.query(CourseCertificate)
        .filter(CourseCertificate.certificate_code == normalized_code)
        .first()
    )
    if certificate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return CertificateVerificationResponse(
        valid=True,
        certificate_code=certificate.certificate_code,
        recipient_name=certificate.recipient_name,
        course_title=certificate.course_title,
        issued_at=certificate.issued_at,
    )
