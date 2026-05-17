import enum
from datetime import datetime
from typing import Literal
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SessionStatus(str, enum.Enum):
    created = "created"
    processing = "processing"
    completed = "completed"
    deleted = "deleted"
    failed = "failed"


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.created)

    consent_terms: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_health_data: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_ai: Mapped[bool] = mapped_column(Boolean, nullable=False)

    anonymization_level: Mapped[Literal["full", "medical"]] = mapped_column(
        String(16),
        default="full",
        nullable=False,
    )

    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    client_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
