import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attempt_question import AttemptQuestion
    from app.models.question_bank import QuestionBank
    from app.models.question_option import QuestionOption
    from app.models.quiz_question import QuizQuestion


class Question(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "questions"

    question_bank_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_banks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=1, nullable=False)
    negative_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)

    question_bank: Mapped["QuestionBank"] = relationship(back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )
    quiz_questions: Mapped[list["QuizQuestion"]] = relationship(back_populates="question")
    attempt_questions: Mapped[list["AttemptQuestion"]] = relationship(back_populates="question")
