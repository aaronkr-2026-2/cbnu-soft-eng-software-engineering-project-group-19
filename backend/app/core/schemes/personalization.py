from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CourseRecommendation(BaseModel):
    course_id: UUID
    title: str
    description: str | None
    language: str
    level: str
    match_score: int
    reasons: list[str]


class RecommendationResponse(BaseModel):
    preferred_language: str
    estimated_level: str
    average_quiz_score: float | None
    ai_powered: bool = False
    recommendations: list[CourseRecommendation]


class LearningPlanGenerate(BaseModel):
    course_id: UUID
    weekly_study_days: int = Field(default=5, ge=1, le=7)
    session_minutes: int = Field(default=30, ge=10, le=240)


class LearningPlanItem(BaseModel):
    session_number: int
    week_number: int
    study_day: int
    lesson_id: UUID
    lesson_title: str
    session_minutes: int
    quiz_available: bool
    guidance: str


class LearningPlanResponse(BaseModel):
    id: UUID
    course_id: UUID
    course_title: str
    weekly_study_days: int
    session_minutes: int
    estimated_weeks: int
    completed_lessons: int
    total_lessons: int
    plan_items: list[LearningPlanItem]
    generated_at: datetime
