from pydantic import BaseModel, Field


class LessonCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1)
    position: int = Field(ge=1)


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    position: int | None = Field(default=None, ge=1)


class LessonResponse(BaseModel):
    id: str
    course_id: str
    title: str
    content: str
    position: int
