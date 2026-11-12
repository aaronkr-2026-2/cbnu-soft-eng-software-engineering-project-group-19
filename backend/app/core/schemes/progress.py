from datetime import datetime

from pydantic import BaseModel, Field


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


class VideoWatchReport(BaseModel):
    position_seconds: float = Field(ge=0)
    duration_seconds: float = Field(gt=0, le=86400)
    item_index: int = Field(default=0, ge=0, le=499)
    item_count: int = Field(default=1, ge=1, le=500)
    playback_rate: float = Field(default=1, ge=0.25, le=2)
    ended: bool = False


class VideoWatchResponse(BaseModel):
    watched_seconds: float
    duration_seconds: float
    furthest_position_seconds: float = 0
    completion_percent: float
    can_complete: bool
    item_count: int = 1
