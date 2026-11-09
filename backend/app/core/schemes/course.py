from app.core.schemes.review import CourseReviewResponse
from pydantic import BaseModel, Field
from typing import Literal


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    category: str = Field(default="General", min_length=2, max_length=100)
    price_uzs: int = Field(default=0, ge=0, le=1_000_000_000)
    language: Literal["uz", "en", "ru", "ko"] = "uz"
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, min_length=2, max_length=100)
    price_uzs: int | None = Field(default=None, ge=0, le=1_000_000_000)
    language: Literal["uz", "en", "ru", "ko"] | None = None
    level: Literal["beginner", "intermediate", "advanced"] | None = None


class CourseResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    price_uzs: int
    language: str
    level: str
    is_published: bool
    owner_id: str
    banner_url: str | None = None


class CourseCatalogResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    price_uzs: int
    language: str
    level: str
    is_published: bool
    display_language: str = "uz"
    translated: bool = False
    banner_url: str | None = None


class CourseOutlineLesson(BaseModel):
    title: str
    position: int
    banner_url: str | None = None


class CourseOutlineResponse(BaseModel):
    id: str
    title: str
    description: str | None
    category: str
    price_uzs: int
    language: str
    level: str
    display_language: str = "uz"
    translated: bool = False
    banner_url: str | None = None
    lessons: list[CourseOutlineLesson]
    average_rating: float | None = None
    review_count: int = 0
    reviews: list[CourseReviewResponse] = Field(default_factory=list)
