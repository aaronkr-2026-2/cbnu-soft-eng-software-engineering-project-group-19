from uuid import UUID

from pydantic import BaseModel, Field


class LessonAnalyticsResponse(BaseModel):
    lesson_id: UUID
    title: str
    position: int
    completed_learners: int
    next_lesson_learners: int


class CourseAnalyticsResponse(BaseModel):
    course_id: UUID
    course_title: str
    enrollment_count: int
    completed_learners: int
    completion_rate: float
    started_learners: int = 0
    lessons: list[LessonAnalyticsResponse] = Field(default_factory=list)
    average_rating: float | None
    review_count: int
    final_exam_attempts: int
    final_exam_passes: int
    final_exam_pass_rate: float
