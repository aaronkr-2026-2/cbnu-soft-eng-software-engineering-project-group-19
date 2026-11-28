from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CourseReviewUpsert(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class CourseReviewResponse(BaseModel):
    id: UUID
    reviewer_name: str
    rating: int
    comment: str | None
    created_at: datetime


class MyCourseReviewResponse(BaseModel):
    id: UUID
    rating: int
    comment: str | None
    updated_at: datetime
