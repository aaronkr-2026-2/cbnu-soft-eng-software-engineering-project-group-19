from datetime import datetime

from pydantic import BaseModel


class LessonProgressResponse(BaseModel):
    course_id: str
    lesson_id: str
    completed_at: datetime


class CourseProgressResponse(BaseModel):
    course_id: str
    total_lessons: int
    completed_lessons: int
    progress_percent: float
    completed_lesson_ids: list[str]
