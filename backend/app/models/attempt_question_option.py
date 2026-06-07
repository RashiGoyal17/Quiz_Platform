import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attempt_question import AttemptQuestion
    from app.models.question_option import QuestionOption


class AttemptQuestionOption(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attempt_question_options"
    __table_args__ = (
        UniqueConstraint("attempt_question_id", "option_id", name="uq_attempt_question_option"),
        UniqueConstraint("attempt_question_id", "position", name="uq_attempt_question_option_position"),
    )

    attempt_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempt_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_options.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    option_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    attempt_question: Mapped["AttemptQuestion"] = relationship(back_populates="options")
    original_option: Mapped["QuestionOption"] = relationship()
