import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field

from app.models.enums import ProctoringEventType


# ── Request schemas ───────────────────────────────────────────────────────────

class StartAttemptRequest(BaseModel):
    quiz_id: uuid.UUID


class SaveAnswerRequest(BaseModel):
    attempt_question_id: uuid.UUID
    selected_option_id: uuid.UUID | None = Field(
        default=None,
        description="UUID of the AttemptQuestionOption snapshot. Null to clear.",
    )


class ProctoringEventRequest(BaseModel):
    event_type: Annotated[
        ProctoringEventType,
        Field(
            description=(
                "Proctoring event type. Only WINDOW_BLUR, COPY_PASTE, and FULLSCREEN_EXIT "
                "are accepted from client submissions. TAB_SWITCH must use /tab-switch. "
                "AI detection types (FACE_NOT_DETECTED, MULTIPLE_FACES, PHONE_DETECTED, "
                "AUDIO_DETECTED) are reserved for server-side use."
            ),
            examples=["window_blur"],
        ),
    ]
    metadata: Annotated[
        dict[str, Any] | None,
        Field(
            default=None,
            description=(
                "Optional event-specific context. Stored as-is and visible in admin audit. "
                "Content is untrusted student input — render with escaping."
            ),
            examples=[{"duration_ms": 1400}],
        ),
    ] = None


# ── Option snapshots (no is_correct — hidden during active attempt) ───────────

class AttemptOptionResponse(BaseModel):
    id: uuid.UUID
    option_text_snapshot: str
    position: int


class AttemptOptionResultResponse(BaseModel):
    id: uuid.UUID
    option_text_snapshot: str
    is_correct_snapshot: bool
    position: int


# ── Question snapshots ────────────────────────────────────────────────────────

class AttemptQuestionResponse(BaseModel):
    id: uuid.UUID
    question_text_snapshot: str
    position: int
    marks: Decimal
    negative_marks: Decimal
    options: list[AttemptOptionResponse]
    selected_option_id: uuid.UUID | None


class AttemptQuestionResultResponse(BaseModel):
    id: uuid.UUID
    question_text_snapshot: str
    position: int
    marks: Decimal
    negative_marks: Decimal
    options: list[AttemptOptionResultResponse]
    selected_option_id: uuid.UUID | None
    is_correct: bool | None
    marks_awarded: Decimal | None


# ── Top-level responses ───────────────────────────────────────────────────────

class AnswerResponse(BaseModel):
    id: uuid.UUID
    attempt_question_id: uuid.UUID
    selected_option_id: uuid.UUID | None
    answered_at: datetime | None


class AttemptResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    student_id: uuid.UUID
    attempt_number: int
    status: str
    started_at: datetime
    time_limit_minutes: int
    questions: list[AttemptQuestionResponse]


class AttemptResultResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    student_id: uuid.UUID
    attempt_number: int
    status: str
    started_at: datetime
    submitted_at: datetime | None
    score: Decimal
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    percentage: Decimal
    questions: list[AttemptQuestionResultResponse]


# ── Anti-cheat / audit schemas ────────────────────────────────────────────────

class TabSwitchResponse(BaseModel):
    attempt_id: uuid.UUID
    tab_switch_count: int
    max_tab_switches: int | None
    limit_exceeded: bool
    attempt_status: str


class TabSwitchLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    switched_at: datetime


class ProctoringEventResponse(BaseModel):
    # event_metadata on the ORM maps to metadata in the API contract
    model_config = {"from_attributes": True, "populate_by_name": True}

    id: uuid.UUID
    attempt_id: uuid.UUID
    event_type: str
    occurred_at: datetime
    metadata: dict[str, Any] | None = Field(None, validation_alias="event_metadata")


class AttemptAdminResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    quiz_id: uuid.UUID
    student_id: uuid.UUID
    attempt_number: int
    status: str
    started_at: datetime
    submitted_at: datetime | None
    score: Decimal | None
    tab_switch_count: int
    ip_address: str | None
    created_at: datetime


class AttemptAuditResponse(BaseModel):
    attempt: AttemptAdminResponse
    tab_switch_logs: list[TabSwitchLogResponse]
    proctoring_events: list[ProctoringEventResponse]
