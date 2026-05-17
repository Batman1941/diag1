from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.models.session import SessionStatus


class SessionCreate(BaseModel):
    consent_terms: bool
    consent_health_data: bool
    consent_ai: bool
    anonymization_level: Literal["full", "medical"] = "full"
    client_id: str | None = None


class SessionOut(BaseModel):
    id: UUID
    status: SessionStatus
    created_at: datetime


class ReportOut(BaseModel):
    id: UUID
    status: SessionStatus
    report_markdown: str | None = None
    error_message: str | None = None
    prompt_sent: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_model_requested: str | None = None
    ai_region: str | None = None
    ai_country: str | None = None


class FinalizeOut(BaseModel):
    id: UUID
    status: SessionStatus


class ProgressOut(BaseModel):
    id: UUID
    status: SessionStatus
    progress: int
    stage: str
    updated_at: datetime | None = None


class ConsentRecord(BaseModel):
    id: UUID
    created_at: datetime
    status: SessionStatus
    consent_terms: bool
    consent_health_data: bool
    consent_ai: bool
    anonymization_level: Literal["full", "medical"]
    client_id: str | None = None
