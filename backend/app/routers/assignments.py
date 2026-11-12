import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_author
from app.core.localization import get_assignment_translation
from app.core.schemes.assignment import (
    AssignmentGrade,
    AssignmentSubmissionCreate,
    AssignmentSubmissionResponse,
    LessonAssignmentResponse,
    LessonAssignmentUpsert,
)
from app.database import get_db
from app.models import (
    AssignmentSubmission,
    AssignmentTranslation,
    Course,
    Enrollment,
    Lesson,
    LessonAssignment,
    User,
)

router = APIRouter(tags=["Lesson assignments"])


def lesson_context(course_id: uuid.UUID, lesson_id: uuid.UUID, db: Session) -> tuple[Course, Lesson]:
    course = db.query(Course).filter(Course.id == course_id).first()
    lesson = db.query(Lesson).filter(
        Lesson.id == lesson_id, Lesson.course_id == course_id
    ).first()
    if course is None or lesson is None:
        raise HTTPException(status_code=404, detail="Course or lesson not found")
    return course, lesson


def owned_assignment_context(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    user: User,
    db: Session,
) -> tuple[Course, Lesson]:
    course, lesson = lesson_context(course_id, lesson_id, db)
    if course.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Course or lesson not found")
    return course, lesson


def submission_response(submission: AssignmentSubmission, learner_name: str | None = None) -> AssignmentSubmissionResponse:
    return AssignmentSubmissionResponse(
        id=str(submission.id),
        assignment_id=str(submission.assignment_id),
        answer=submission.answer,
        status=submission.status,
        score=submission.score,
        feedback=submission.feedback,
        submitted_at=submission.submitted_at,
        graded_at=submission.graded_at,
        learner_name=learner_name,
    )


@router.get(
    "/courses/{course_id}/lessons/{lesson_id}/assignment",
    response_model=LessonAssignmentResponse | None,
)
def get_lesson_assignment(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    language: Literal["uz", "en", "ru", "ko"] = Query(default="uz"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LessonAssignmentResponse | None:
    course, lesson = lesson_context(course_id, lesson_id, db)
    is_owner = course.owner_id == current_user.id
    if not is_owner:
        enrolled = db.query(Enrollment.id).filter(
            Enrollment.course_id == course.id, Enrollment.user_id == current_user.id
        ).first()
        if not course.is_published or enrolled is None:
            raise HTTPException(status_code=404, detail="Course or lesson not found")
    assignment = db.query(LessonAssignment).filter(LessonAssignment.lesson_id == lesson.id).first()
    if assignment is None:
        return None
    translation = get_assignment_translation(assignment, course, language, db)
    submission = None if is_owner else db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id,
        AssignmentSubmission.user_id == current_user.id,
    ).first()
    return LessonAssignmentResponse(
        id=str(assignment.id),
        lesson_id=str(lesson.id),
        title=translation.title if translation else assignment.title,
        instructions=translation.instructions if translation else assignment.instructions,
        max_score=assignment.max_score,
        my_submission=submission_response(submission) if submission else None,
    )


@router.put(
    "/courses/{course_id}/lessons/{lesson_id}/assignment",
    response_model=LessonAssignmentResponse,
)
def upsert_lesson_assignment(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    assignment_data: LessonAssignmentUpsert,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> LessonAssignmentResponse:
    _course, lesson = owned_assignment_context(course_id, lesson_id, current_user, db)
    assignment = db.query(LessonAssignment).filter(LessonAssignment.lesson_id == lesson.id).first()
    if assignment is None:
        assignment = LessonAssignment(lesson_id=lesson.id)
        db.add(assignment)
    elif assignment.title != assignment_data.title.strip() or assignment.instructions != assignment_data.instructions.strip():
        db.query(AssignmentTranslation).filter(
            AssignmentTranslation.assignment_id == assignment.id
        ).delete(synchronize_session=False)
    assignment.title = assignment_data.title.strip()
    assignment.instructions = assignment_data.instructions.strip()
    assignment.max_score = assignment_data.max_score
    db.commit()
    db.refresh(assignment)
    return LessonAssignmentResponse(
        id=str(assignment.id), lesson_id=str(lesson.id), title=assignment.title,
        instructions=assignment.instructions, max_score=assignment.max_score,
    )


@router.delete(
    "/courses/{course_id}/lessons/{lesson_id}/assignment",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lesson_assignment(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> None:
    _course, lesson = owned_assignment_context(course_id, lesson_id, current_user, db)
    assignment = db.query(LessonAssignment).filter(LessonAssignment.lesson_id == lesson.id).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id
    ).delete(synchronize_session=False)
    db.query(AssignmentTranslation).filter(
        AssignmentTranslation.assignment_id == assignment.id
    ).delete(synchronize_session=False)
    db.delete(assignment)
    db.commit()


@router.post(
    "/courses/{course_id}/lessons/{lesson_id}/assignment/submissions",
    response_model=AssignmentSubmissionResponse,
)
def submit_assignment(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    submission_data: AssignmentSubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentSubmissionResponse:
    course, lesson = lesson_context(course_id, lesson_id, db)
    enrolled = db.query(Enrollment.id).filter(
        Enrollment.course_id == course.id, Enrollment.user_id == current_user.id
    ).first()
    if course.owner_id == current_user.id or not course.is_published or enrolled is None:
        raise HTTPException(status_code=404, detail="Course or lesson not found")
    assignment = db.query(LessonAssignment).filter(LessonAssignment.lesson_id == lesson.id).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment.id,
        AssignmentSubmission.user_id == current_user.id,
    ).first()
    if submission is None:
        submission = AssignmentSubmission(
            assignment_id=assignment.id, user_id=current_user.id, answer=submission_data.answer.strip()
        )
        db.add(submission)
    else:
        submission.answer = submission_data.answer.strip()
        submission.status = "submitted"
        submission.score = None
        submission.feedback = None
        submission.graded_at = None
        submission.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission_response(submission)


@router.get(
    "/courses/{course_id}/lessons/{lesson_id}/assignment/submissions",
    response_model=list[AssignmentSubmissionResponse],
)
def list_assignment_submissions(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> list[AssignmentSubmissionResponse]:
    _course, lesson = owned_assignment_context(course_id, lesson_id, current_user, db)
    assignment = db.query(LessonAssignment).filter(LessonAssignment.lesson_id == lesson.id).first()
    if assignment is None:
        return []
    rows = db.query(AssignmentSubmission, User.full_name).join(
        User, User.id == AssignmentSubmission.user_id
    ).filter(AssignmentSubmission.assignment_id == assignment.id).order_by(
        AssignmentSubmission.submitted_at.desc()
    ).all()
    return [submission_response(submission, learner_name) for submission, learner_name in rows]


@router.put(
    "/courses/{course_id}/lessons/{lesson_id}/assignment/submissions/{submission_id}",
    response_model=AssignmentSubmissionResponse,
)
def grade_assignment_submission(
    course_id: uuid.UUID,
    lesson_id: uuid.UUID,
    submission_id: uuid.UUID,
    grade: AssignmentGrade,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> AssignmentSubmissionResponse:
    _course, lesson = owned_assignment_context(course_id, lesson_id, current_user, db)
    assignment = db.query(LessonAssignment).filter(LessonAssignment.lesson_id == lesson.id).first()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if grade.score > assignment.max_score:
        raise HTTPException(status_code=422, detail="Score cannot exceed the assignment maximum")
    row = db.query(AssignmentSubmission, User.full_name).join(
        User, User.id == AssignmentSubmission.user_id
    ).filter(
        AssignmentSubmission.id == submission_id,
        AssignmentSubmission.assignment_id == assignment.id,
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission, learner_name = row
    submission.status = "graded"
    submission.score = grade.score
    submission.feedback = grade.feedback.strip() if grade.feedback else None
    submission.graded_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(submission)
    return submission_response(submission, learner_name)
