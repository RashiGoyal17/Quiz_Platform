import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import AttemptStatus

if TYPE_CHECKING:
    from app.models.attempt_answer import AttemptAnswer
    from app.models.attempt_question import AttemptQuestion
    from app.models.proctoring_event import ProctoringEvent
    from app.models.quiz import Quiz
    from app.models.tab_switch_log import TabSwitchLog
    from app.models.user import User


class Attempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("student_id", "quiz_id", "attempt_number", name="uq_attempt_student_quiz_number"),
        Index("ix_attempts_student_id", "student_id"),
        Index("ix_attempts_quiz_id", "quiz_id"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="RESTRICT"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[AttemptStatus] = mapped_column(
        SQLEnum(AttemptStatus), nullable=False, default=AttemptStatus.IN_PROGRESS
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    tab_switch_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    student: Mapped["User"] = relationship(back_populates="attempts")
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
    attempt_questions: Mapped[list["AttemptQuestion"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
    answers: Mapped[list["AttemptAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
    tab_switch_logs: Mapped[list["TabSwitchLog"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
    proctoring_events: Mapped[list["ProctoringEvent"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
