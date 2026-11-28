import uuid
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, union
from sqlalchemy.orm import Session

from app.core.dependencies import require_author
from app.core.schemes.analytics import CourseAnalyticsResponse, LessonAnalyticsResponse
from app.database import get_db
from app.models import (
    AssignmentSubmission,
    Course,
    CourseReview,
    Enrollment,
    FinalExamAttempt,
    Lesson,
    LessonAssignment,
    LessonProgress,
    Quiz,
    QuizAttempt,
    User,
    VideoWatchProgress,
)

router = APIRouter(prefix="/courses/{course_id}/analytics", tags=["Course Analytics"])


@router.get("", response_model=CourseAnalyticsResponse)
def get_course_analytics(
    course_id: uuid.UUID,
    current_user: User = Depends(require_author),
    db: Session = Depends(get_db),
) -> CourseAnalyticsResponse:
    course = (
        db.query(Course).filter(Course.id == course_id, Course.owner_id == current_user.id).first()
    )
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    enrolled = select(Enrollment.user_id).where(Enrollment.course_id == course_id)
    enrollment_count = db.scalar(select(func.count()).select_from(enrolled.subquery())) or 0
    lessons = db.execute(
        select(Lesson.id, Lesson.title, Lesson.position)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.position, Lesson.created_at)
    ).all()
    completed_by_learner: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    lesson_completions: Counter[uuid.UUID] = Counter()
    next_lesson_counts: Counter[uuid.UUID] = Counter()
    completed_learners = 0
    started_learners = 0
    if lessons and enrollment_count:
        ordered_ids = [lesson.id for lesson in lessons]
        lesson_ids = set(ordered_ids)
        completion_rows = db.execute(
            select(LessonProgress.user_id, LessonProgress.lesson_id)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .where(Lesson.course_id == course_id, LessonProgress.user_id.in_(enrolled))
        )
        for learner_id, lesson_id in completion_rows:
            if lesson_id not in lesson_ids:
                continue
            completed_by_learner[learner_id].add(lesson_id)
            lesson_completions[lesson_id] += 1

        activity_users = union(
            select(VideoWatchProgress.user_id)
            .join(Lesson, Lesson.id == VideoWatchProgress.lesson_id)
            .where(
                Lesson.course_id == course_id,
                (VideoWatchProgress.watched_seconds > 0)
                | (VideoWatchProgress.last_position_seconds > 0),
            ),
            select(QuizAttempt.user_id)
            .join(Quiz, Quiz.id == QuizAttempt.quiz_id)
            .join(Lesson, Lesson.id == Quiz.lesson_id)
            .where(Lesson.course_id == course_id),
            select(AssignmentSubmission.user_id)
            .join(LessonAssignment, LessonAssignment.id == AssignmentSubmission.assignment_id)
            .join(Lesson, Lesson.id == LessonAssignment.lesson_id)
            .where(Lesson.course_id == course_id),
        ).subquery()
        active_learners = set(completed_by_learner)
        active_learners.update(
            db.scalars(
                select(activity_users.c.user_id).where(activity_users.c.user_id.in_(enrolled))
            )
        )
        started_learners = len(active_learners)
        for learner_id in active_learners:
            completed = completed_by_learner.get(learner_id, set())
            if len(completed) == len(ordered_ids):
                completed_learners += 1
            else:
                first_incomplete = next(
                    lesson_id for lesson_id in ordered_ids if lesson_id not in completed
                )
                next_lesson_counts[first_incomplete] += 1

    review_count, average_rating = (
        db.query(func.count(CourseReview.id), func.avg(CourseReview.rating))
        .filter(CourseReview.course_id == course_id)
        .one()
    )
    exam_attempts, exam_passes = (
        db.query(
            func.count(FinalExamAttempt.id),
            func.count(FinalExamAttempt.id).filter(FinalExamAttempt.passed.is_(True)),
        )
        .filter(FinalExamAttempt.course_id == course_id)
        .one()
    )
    exam_attempts = exam_attempts or 0
    exam_passes = exam_passes or 0

    return CourseAnalyticsResponse(
        course_id=course.id,
        course_title=course.title,
        enrollment_count=enrollment_count,
        completed_learners=completed_learners,
        completion_rate=round(completed_learners / enrollment_count * 100, 1)
        if enrollment_count
        else 0.0,
        started_learners=started_learners,
        lessons=[
            LessonAnalyticsResponse(
                lesson_id=lesson.id,
                title=lesson.title,
                position=lesson.position,
                completed_learners=lesson_completions[lesson.id],
                next_lesson_learners=next_lesson_counts[lesson.id],
            )
            for lesson in lessons
        ],
        average_rating=round(float(average_rating), 1) if average_rating is not None else None,
        review_count=review_count or 0,
        final_exam_attempts=exam_attempts,
        final_exam_passes=exam_passes,
        final_exam_pass_rate=round(exam_passes / exam_attempts * 100, 1) if exam_attempts else 0.0,
    )
