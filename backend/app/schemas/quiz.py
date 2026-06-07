import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

# ── Shared config ─────────────────────────────────────────────────────────────

_FROM_ORM = {"from_attributes": True}


# ── Option schemas ────────────────────────────────────────────────────────────

class OptionCreate(BaseModel):
    text: Annotated[str, Field(min_length=1, max_length=2000, examples=["Paris"])]
    is_correct: bool


class OptionResponse(BaseModel):
    model_config = _FROM_ORM

    id: uuid.UUID
    text: str
    is_correct: bool
    position: int


# ── Question Bank schemas ─────────────────────────────────────────────────────

class QuestionBankCreate(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=255, examples=["Geography Bank"])]
    description: Annotated[str | None, Field(default=None, examples=["World geography questions"])]


class QuestionBankUpdate(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=1, max_length=255)] = None
    description: str | None = None


class QuestionBankResponse(BaseModel):
    model_config = _FROM_ORM

    id: uuid.UUID
    name: str
    description: str | None
    creator_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ── Question schemas ──────────────────────────────────────────────────────────

class QuestionCreate(BaseModel):
    text: Annotated[str, Field(min_length=1, examples=["What is the capital of France?"])]
    explanation: Annotated[str | None, Field(default=None, examples=["Paris has been the capital since 987 AD."])]
    marks: Annotated[Decimal, Field(gt=0, examples=[2])] = Decimal("1")
    negative_marks: Annotated[Decimal, Field(ge=0, examples=[0.5])] = Decimal("0.00")
    options: Annotated[
        list[OptionCreate],
        Field(min_length=4, max_length=4, examples=[[
            {"text": "Paris", "is_correct": True},
            {"text": "London", "is_correct": False},
            {"text": "Berlin", "is_correct": False},
            {"text": "Madrid", "is_correct": False},
        ]]),
    ]

    @field_validator("options")
    @classmethod
    def exactly_one_correct(cls, v: list[OptionCreate]) -> list[OptionCreate]:
        correct = sum(1 for opt in v if opt.is_correct)
        if correct != 1:
            raise ValueError("Exactly one option must be marked as correct")
        return v


class QuestionUpdate(BaseModel):
    text: str | None = None
    explanation: str | None = None
    marks: Annotated[Decimal | None, Field(gt=0)] = None
    negative_marks: Annotated[Decimal | None, Field(ge=0)] = None
    options: list[OptionCreate] | None = None

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[OptionCreate] | None) -> list[OptionCreate] | None:
        if v is None:
            return v
        if len(v) != 4:
            raise ValueError("Exactly 4 options required")
        correct = sum(1 for opt in v if opt.is_correct)
        if correct != 1:
            raise ValueError("Exactly one option must be marked as correct")
        return v


class QuestionResponse(BaseModel):
    model_config = _FROM_ORM

    id: uuid.UUID
    question_bank_id: uuid.UUID
    text: str
    explanation: str | None
    marks: Decimal
    negative_marks: Decimal
    options: list[OptionResponse]
    created_at: datetime
    updated_at: datetime


# ── Quiz schemas ──────────────────────────────────────────────────────────────

class QuizCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=255, examples=["Midterm Geography"])]
    description: str | None = None
    duration_minutes: Annotated[int, Field(gt=0, examples=[60])]
    start_time: datetime | None = None
    end_time: datetime | None = None
    shuffle_questions: bool = False
    shuffle_options: bool = False
    max_attempts: Annotated[int, Field(ge=1, examples=[1])] = 1
    proctoring_enabled: bool = False
    max_tab_switches: Annotated[int | None, Field(ge=0, default=None)] = None

    @model_validator(mode="after")
    def end_after_start(self) -> "QuizCreate":
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class QuizUpdate(BaseModel):
    title: Annotated[str | None, Field(min_length=1, max_length=255)] = None
    description: str | None = None
    duration_minutes: Annotated[int | None, Field(gt=0)] = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    max_attempts: Annotated[int | None, Field(ge=1)] = None
    proctoring_enabled: bool | None = None
    max_tab_switches: Annotated[int | None, Field(ge=0)] = None


class QuizResponse(BaseModel):
    model_config = _FROM_ORM

    id: uuid.UUID
    creator_id: uuid.UUID
    title: str
    description: str | None
    duration_minutes: int
    start_time: datetime | None
    end_time: datetime | None
    is_published: bool
    shuffle_questions: bool
    shuffle_options: bool
    max_attempts: int
    proctoring_enabled: bool
    max_tab_switches: int | None
    created_at: datetime
    updated_at: datetime


class QuizAvailableResponse(BaseModel):
    model_config = _FROM_ORM

    id: uuid.UUID
    title: Annotated[str, Field(examples=["Midterm Geography"])]
    description: Annotated[str | None, Field(examples=["Covers chapters 1-5 of the textbook"])]
    duration_minutes: Annotated[int, Field(examples=[60])]
    start_time: Annotated[datetime | None, Field(examples=["2026-06-10T09:00:00Z"])]
    end_time: Annotated[datetime | None, Field(examples=["2026-06-10T11:00:00Z"])]
    max_attempts: Annotated[int, Field(examples=[1])]
    proctoring_enabled: Annotated[bool, Field(examples=[True])]


# ── Quiz Question schemas ─────────────────────────────────────────────────────

class AddQuestionToQuiz(BaseModel):
    question_id: uuid.UUID
    position: Annotated[int, Field(ge=0, examples=[0])]
    marks_override: Annotated[Decimal | None, Field(ge=0, default=None)] = None


class QuizQuestionResponse(BaseModel):
    model_config = _FROM_ORM

    quiz_id: uuid.UUID
    question_id: uuid.UUID
    position: int
    marks_override: Decimal | None
    question: QuestionResponse
