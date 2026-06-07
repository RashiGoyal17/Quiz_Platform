import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attempt import Attempt
    from app.models.attempt_answer import AttemptAnswer
    from app.models.attempt_question_option import AttemptQuestionOption
    from app.models.question import Question


class AttemptQuestion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attempt_questions"
    __table_args__ = (
        UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
        UniqueConstraint("attempt_id", "position", name="uq_attempt_question_position"),
    )

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    question_text_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    negative_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    attempt: Mapped["Attempt"] = relationship(back_populates="attempt_questions")
    question: Mapped["Question"] = relationship(back_populates="attempt_questions")
    options: Mapped[list["AttemptQuestionOption"]] = relationship(
        back_populates="attempt_question", cascade="all, delete-orphan"
    )
    answer: Mapped["AttemptAnswer | None"] = relationship(
        back_populates="attempt_question", uselist=False
    )
