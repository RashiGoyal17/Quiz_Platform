import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


# ── Student analytics ─────────────────────────────────────────────────────────

class StudentAnalyticsResponse(BaseModel):
    student_id: uuid.UUID
    total_attempts: int
    submitted_count: int
    timed_out_count: int
    abandoned_count: int
    in_progress_count: int
    average_score: Decimal | None
    best_score: Decimal | None
    average_percentage: Decimal | None
    best_percentage: Decimal | None


class AttemptHistoryItem(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str
    attempt_number: int
    status: str
    score: Decimal | None
    started_at: datetime
    submitted_at: datetime | None


class StudentHistoryResponse(BaseModel):
    items: list[AttemptHistoryItem]
    total: int
    limit: int
    offset: int


# ── Quiz analytics ────────────────────────────────────────────────────────────

class QuizAntiCheatAnalytics(BaseModel):
    total_tab_switches: int
    average_tab_switches_per_attempt: Decimal | None
    attempts_with_proctoring_events: int
    most_common_proctoring_event: str | None


class QuizAnalyticsResponse(BaseModel):
    quiz_id: uuid.UUID
    quiz_title: str
    total_attempts: int
    in_progress_count: int
    submitted_count: int
    timed_out_count: int
    abandoned_count: int
    completion_rate: Decimal
    abandonment_rate: Decimal
    timeout_rate: Decimal
    average_score: Decimal | None
    anti_cheat: QuizAntiCheatAnalytics


# ── Question analytics ────────────────────────────────────────────────────────

class QuestionAnalyticsItem(BaseModel):
    question_id: uuid.UUID
    question_text_snapshot: str
    total_seen: int
    answered_count: int
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    correct_pct: Decimal | None
    incorrect_pct: Decimal | None
    unanswered_pct: Decimal | None
    difficulty_rank: int | None
    insufficient_data: bool


class QuizQuestionAnalyticsResponse(BaseModel):
    quiz_id: uuid.UUID
    total_finalized_attempts: int
    min_attempts_for_ranking: int
    questions: list[QuestionAnalyticsItem]


# ── Admin dashboard ───────────────────────────────────────────────────────────

class RecentActivityItem(BaseModel):
    attempt_id: uuid.UUID
    student_id: uuid.UUID
    student_username: str
    quiz_id: uuid.UUID
    quiz_title: str
    status: str
    score: Decimal | None
    started_at: datetime
    submitted_at: datetime | None


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_students: int
    total_admins: int
    active_users: int
    total_quizzes: int
    published_quizzes: int
    total_attempts: int
    in_progress_attempts: int
    submitted_attempts: int
    timed_out_attempts: int
    abandoned_attempts: int
    total_tab_switches: int
    average_tab_switches_per_attempt: Decimal | None
    total_proctoring_events: int
    recent_attempts: list[RecentActivityItem]
