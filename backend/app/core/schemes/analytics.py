from uuid import UUID

from pydantic import BaseModel


class CourseAnalyticsResponse(BaseModel):
    course_id: UUID
    course_title: str
    enrollment_count: int
    completed_learners: int
    completion_rate: float
    average_rating: float | None
    review_count: int
    final_exam_attempts: int
    final_exam_passes: int
    final_exam_pass_rate: float
