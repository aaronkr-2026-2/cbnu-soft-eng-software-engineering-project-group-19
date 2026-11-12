from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LessonAssignmentUpsert(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    instructions: str = Field(min_length=1, max_length=10000)
    max_score: int = Field(default=100, ge=1, le=1000)

    @field_validator("title", "instructions")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank")
        return value


class AssignmentSubmissionCreate(BaseModel):
    answer: str = Field(min_length=1, max_length=20000)

    @field_validator("answer")
    @classmethod
    def strip_answer(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Answer cannot be blank")
        return value


class AssignmentGrade(BaseModel):
    score: int = Field(ge=0, le=1000)
    feedback: str | None = Field(default=None, max_length=5000)


class AssignmentSubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    answer: str
    status: str
    score: int | None = None
    feedback: str | None = None
    submitted_at: datetime
    graded_at: datetime | None = None
    learner_name: str | None = None


class LessonAssignmentResponse(BaseModel):
    id: str
    lesson_id: str
    title: str
    instructions: str
    max_score: int
    my_submission: AssignmentSubmissionResponse | None = None
