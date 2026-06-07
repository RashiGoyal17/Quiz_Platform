import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin
from app.models.enums import ProctoringEventType

if TYPE_CHECKING:
    from app.models.attempt import Attempt


class ProctoringEvent(Base, UUIDMixin):
    __tablename__ = "proctoring_events"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[ProctoringEventType] = mapped_column(
        SQLEnum(ProctoringEventType), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    attempt: Mapped["Attempt"] = relationship(back_populates="proctoring_events")
