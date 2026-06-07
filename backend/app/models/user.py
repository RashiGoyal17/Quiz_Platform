import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.attempt import Attempt
    from app.models.question_bank import QuestionBank
    from app.models.quiz import Quiz
    from app.models.refresh_token import RefreshToken


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.STUDENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    question_banks: Mapped[list["QuestionBank"]] = relationship(back_populates="creator")
    quizzes: Mapped[list["Quiz"]] = relationship(back_populates="creator")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="student")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
