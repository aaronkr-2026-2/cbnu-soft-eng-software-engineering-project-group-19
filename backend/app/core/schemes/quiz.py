from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class QuizQuestionCreate(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    choices: list[str] = Field(min_length=2, max_length=8)
    correct_index: int = Field(ge=0)
    points: int = Field(default=1, ge=1, le=100)

    @model_validator(mode="after")
    def correct_index_is_valid(self):
        if self.correct_index >= len(self.choices):
            raise ValueError("correct_index must point to an available choice")
        if any(not choice.strip() for choice in self.choices):
            raise ValueError("choices cannot be empty")
        return self


class QuizCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    passing_score: int = Field(default=60, ge=0, le=100)
    questions: list[QuizQuestionCreate] = Field(min_length=1, max_length=50)


class QuizUpdate(QuizCreate):
    """A complete replacement for an instructor-managed quiz."""


class QuizQuestionResponse(BaseModel):
    id: UUID
    prompt: str
    choices: list[str]
    points: int
    position: int


class QuizResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    title: str
    passing_score: int
    questions: list[QuizQuestionResponse]


class QuizManageQuestionResponse(QuizQuestionResponse):
    correct_index: int


class QuizManageResponse(BaseModel):
    id: UUID
    lesson_id: UUID
    title: str
    passing_score: int
    questions: list[QuizManageQuestionResponse]


class QuizAnswerSubmit(BaseModel):
    question_id: UUID
    selected_index: int = Field(ge=0)


class QuizAttemptCreate(BaseModel):
    answers: list[QuizAnswerSubmit] = Field(min_length=1, max_length=50)


class QuizAttemptResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    correct_count: int
    total_questions: int
    earned_points: int
    total_points: int
    score_percent: float
    passed: bool
    submitted_at: datetime


class FinalExamQuestionResponse(BaseModel):
    id: UUID
    lesson_title: str
    prompt: str
    choices: list[str]
    position: int


class FinalExamResponse(BaseModel):
    course_id: UUID
    title: str
    passing_score: int
    questions: list[FinalExamQuestionResponse]
    latest_score: float | None = None
    passed: bool = False


class FinalExamAttemptCreate(BaseModel):
    answers: list[QuizAnswerSubmit] = Field(min_length=1, max_length=250)


class FinalExamAttemptResponse(BaseModel):
    id: UUID
    course_id: UUID
    correct_count: int
    total_questions: int
    score_percent: float
    passed: bool
    submitted_at: datetime
