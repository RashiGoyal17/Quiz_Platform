from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.attempt import Attempt
    from app.models.question_bank import QuestionBank
    from app.models.quiz import Quiz
    from app.models.user import User


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    question_banks: Mapped[list["QuestionBank"]] = relationship(back_populates="organization")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="organization")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="organization")
