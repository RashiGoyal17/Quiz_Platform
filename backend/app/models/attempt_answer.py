import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attempt import Attempt
    from app.models.attempt_question import AttemptQuestion
    from app.models.attempt_question_option import AttemptQuestionOption


class AttemptAnswer(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attempt_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempt_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempt_question_options.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    marks_awarded: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt: Mapped["Attempt"] = relationship(back_populates="answers")
    attempt_question: Mapped["AttemptQuestion"] = relationship(back_populates="answer")
    selected_option: Mapped["AttemptQuestionOption | None"] = relationship()
