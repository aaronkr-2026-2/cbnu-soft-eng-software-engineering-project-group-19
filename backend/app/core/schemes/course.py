from app.core.schemes.review import CourseReviewResponse
from pydantic import BaseModel, Field, Field
from typing import Literal


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    language: Literal["uz", "en", "ru", "ko"] = "uz"
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    language: Literal["uz", "en", "ru", "ko"] | None = None
    level: Literal["beginner", "intermediate", "advanced"] | None = None


class CourseResponse(BaseModel):
    id: str
    title: str
    description: str | None
    language: str
    level: str
    is_published: bool
    owner_id: str


class CourseCatalogResponse(BaseModel):
    id: str
    title: str
    description: str | None
    language: str
    level: str
    is_published: bool


class CourseOutlineLesson(BaseModel):
    title: str
    position: int


class CourseOutlineResponse(BaseModel):
    id: str
    title: str
    description: str | None
    language: str
    level: str
    lessons: list[CourseOutlineLesson]
    average_rating: float | None = None
    review_count: int = 0
    reviews: list[CourseReviewResponse] = Field(default_factory=list)
