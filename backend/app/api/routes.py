import asyncio
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.db.session import get_db
from app.models.session import AnalysisSession, SessionStatus
from app.schemas.session import (
    ConsentRecord,
    FinalizeOut,
    ProgressOut,
    ReportOut,
    SessionCreate,
    SessionOut,
)
from app.services.anonymize import anonymize_text
from app.services.gemini import generate_report
from app.services.pdf import extract_text_from_pdf
from app.services.progress import progress_store

router = APIRouter(prefix="/api")
ALLOWED_ANONYMIZATION_LEVELS = {"full", "medical"}
ACCESS_COOKIE_NAME = "diag1_access"


class AccessLoginRequest(BaseModel):
    password: str


def _access_feature_enabled(settings: Any) -> bool:
    return bool((settings.frontend_access_password or "").strip())


def _access_cookie_secret(settings: Any) -> bytes:
    secret = (
        settings.frontend_access_cookie_secret
        or settings.admin_password
        or "CHANGE_ME_SET_FRONTEND_ACCESS_COOKIE_SECRET"
    )
    return str(secret).encode("utf-8")


def _encode_access_token(payload: str, settings: Any) -> str:
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8").rstrip("=")
    signature = hmac.new(
        _access_cookie_secret(settings),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def _decode_access_token(token: str, settings: Any) -> dict | None:
    try:
        payload_b64, signature = token.rsplit(".", 1)
    except ValueError:
        return None

    expected = hmac.new(
        _access_cookie_secret(settings),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None

    padding = "=" * ((4 - len(payload_b64) % 4) % 4)
    raw = base64.urlsafe_b64decode(f"{payload_b64}{padding}".encode("utf-8"))
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return None
    return data


def _is_access_token_valid(token: str | None, settings: Any) -> bool:
    if not _access_feature_enabled(settings):
        return True
    if not token:
        return False

    data = _decode_access_token(token, settings)
    if not data:
        return False
    try:
        expires_at = int(data.get("exp", 0))
    except (TypeError, ValueError):
        return False
    return expires_at >= int(time.time())


def _generate_access_token(settings: Any) -> str:
    now = int(time.time())
    expires_at = now + max(1, settings.frontend_access_session_ttl_hours) * 3600
    payload = json.dumps(
        {"exp": expires_at, "nonce": secrets.token_urlsafe(16), "iat": now},
        separators=(",", ":"),
        sort_keys=True,
    )
    return _encode_access_token(payload, settings)


def _require_frontend_access(
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE_NAME),
) -> None:
    settings = get_settings()
    if not _is_access_token_valid(access_token, settings):
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/access/status")
def access_status(_: None = Depends(_require_frontend_access)):
    return {"authenticated": True}


@router.post("/access/login")
def access_login(payload: AccessLoginRequest, response: Response):
    settings = get_settings()
    if not _access_feature_enabled(settings):
        return {"authenticated": True}
    if payload.password != (settings.frontend_access_password or ""):
        raise HTTPException(status_code=401, detail="Unauthorized")

    ttl_seconds = max(1, settings.frontend_access_session_ttl_hours) * 3600
    token = _generate_access_token(settings)
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=ttl_seconds,
    )
    return {"authenticated": True}


@router.get("/healthz")
@router.get("/health")
def healthz():
    return {"status": "ok"}


@router.post("/sessions", response_model=SessionOut)
def create_session(
    payload: SessionCreate,
    _access_check: None = Depends(_require_frontend_access),
    db: Session = Depends(get_db),
):
    _purge_expired_sessions(db)
    if not (payload.consent_terms and payload.consent_health_data and payload.consent_ai):
        raise HTTPException(status_code=400, detail="All consents are required.")

    session = AnalysisSession(
        consent_terms=payload.consent_terms,
        consent_health_data=payload.consent_health_data,
        consent_ai=payload.consent_ai,
        anonymization_level=_normalize_anonymization_level(payload.anonymization_level),
        client_id=payload.client_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    progress_store.start(session.id)
    return SessionOut(id=session.id, status=session.status, created_at=session.created_at)


def _parse_session_id(session_id: str) -> UUID:
    try:
        return UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid session id") from exc


def _normalize_anonymization_level(level: str | None) -> str:
    if level in ALLOWED_ANONYMIZATION_LEVELS:
        return level
    return "full"


@router.get("/sessions/{session_id}", response_model=ReportOut)
def get_session(
    session_id: str,
    _access_check: None = Depends(_require_frontend_access),
    db: Session = Depends(get_db),
):
    _purge_expired_sessions(db)
    session = db.get(AnalysisSession, _parse_session_id(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ReportOut(
        id=session.id,
        status=session.status,
        report_markdown=session.report_markdown,
        error_message=session.error_message,
    )


@router.get("/sessions/{session_id}/progress", response_model=ProgressOut)
def get_session_progress(
    session_id: str,
    _access_check: None = Depends(_require_frontend_access),
    db: Session = Depends(get_db),
):
    _purge_expired_sessions(db)
    parsed_id = _parse_session_id(session_id)
    session = db.get(AnalysisSession, parsed_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = progress_store.get(session.id)
    if state:
        status_map = {
            "created": SessionStatus.created,
            "processing": SessionStatus.processing,
            "completed": SessionStatus.completed,
            "failed": SessionStatus.failed,
            "deleted": SessionStatus.deleted,
        }
        return ProgressOut(
            id=session.id,
            status=status_map.get(state["status"], session.status),
            progress=state["progress"],
            stage=state["stage"],
            updated_at=state.get("updated_at"),
        )

    default_stage = {
        SessionStatus.created: "Sesja utworzona",
        SessionStatus.processing: "Trwa przetwarzanie",
        SessionStatus.completed: "Analiza zakończona",
        SessionStatus.failed: session.error_message or "Analiza nieudana",
        SessionStatus.deleted: "Sesja zakończona",
    }[session.status]
    default_progress = 100 if session.status in {SessionStatus.completed, SessionStatus.failed, SessionStatus.deleted} else 0
    return ProgressOut(
        id=session.id,
        status=session.status,
        progress=default_progress,
        stage=default_stage,
    )


@router.post("/sessions/{session_id}/compare", response_model=ReportOut)
async def compare_reports(
    session_id: str,
    _access_check: None = Depends(_require_frontend_access),
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    patient_age: str | None = Form(None),
    patient_gender: str | None = Form(None),
    patient_weight: str | None = Form(None),
    db: Session = Depends(get_db),
):
    _purge_expired_sessions(db)
    session = db.get(AnalysisSession, _parse_session_id(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == SessionStatus.deleted:
        raise HTTPException(status_code=400, detail="Session already finalized")

    if file_a.content_type != "application/pdf" or file_b.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    session.status = SessionStatus.processing
    db.commit()
    progress_store.update(session.id, progress=5, stage="Odczyt przesłanych plików PDF")
    ai_provider = None
    ai_model = None
    ai_model_requested = None
    ai_region = None
    ai_country = None

    try:
        bytes_a, bytes_b = await asyncio.gather(file_a.read(), file_b.read())
        progress_store.update(session.id, progress=15, stage="Ekstrakcja tekstu z badań (A i B równolegle)")
        text_a, text_b = await asyncio.gather(
            run_in_threadpool(extract_text_from_pdf, bytes_a),
            run_in_threadpool(extract_text_from_pdf, bytes_b),
        )

        # Anonymize based on session's anonymization level
        progress_store.update(session.id, progress=55, stage="Anonimizacja danych")
        anonymization_mode = _normalize_anonymization_level(session.anonymization_level)
        anonymized_a, anonymized_b = await asyncio.gather(
            run_in_threadpool(anonymize_text, text_a, anonymization_mode),
            run_in_threadpool(anonymize_text, text_b, anonymization_mode),
        )

        # Prepare additional medical context for AI model in "medical" mode
        progress_store.update(session.id, progress=65, stage="Przygotowanie kontekstu medycznego")
        medical_context = ""
        if anonymization_mode == "medical":
            medical_info = []
            if patient_age:
                medical_info.append(f"Wiek: {patient_age} lat")
            if patient_gender:
                medical_info.append(f"Płeć: {patient_gender}")
            if patient_weight:
                medical_info.append(f"Waga: {patient_weight} kg")
            if medical_info:
                medical_context = "\n\nDane pacjenta: " + ", ".join(medical_info)

        progress_store.update(session.id, progress=75, stage="Wysyłanie zapytania do modelu AI")
        result = await run_in_threadpool(generate_report, anonymized_a, anonymized_b, medical_context)
        progress_store.update(session.id, progress=95, stage="Składanie raportu końcowego")
        session.report_markdown = result["report"]
        prompt_sent = result["prompt_sent"]
        ai_provider = result.get("ai_provider")
        ai_model = result.get("ai_model")
        ai_model_requested = result.get("ai_model_requested")
        ai_region = result.get("ai_region")
        ai_country = result.get("ai_country")
        session.status = SessionStatus.completed
        session.error_message = None
        progress_store.complete(session.id)
    except Exception as exc:  # pragma: no cover - still logged via response
        session.status = SessionStatus.failed
        session.error_message = str(exc)
        progress_store.fail(session.id, stage=f"Błąd: {exc}")
        prompt_sent = None
    finally:
        db.commit()
        db.refresh(session)

    return ReportOut(
        id=session.id,
        status=session.status,
        report_markdown=session.report_markdown,
        error_message=session.error_message,
        prompt_sent=prompt_sent,
        ai_provider=ai_provider,
        ai_model=ai_model,
        ai_model_requested=ai_model_requested,
        ai_region=ai_region,
        ai_country=ai_country,
    )


@router.post("/sessions/{session_id}/finalize", response_model=FinalizeOut)
def finalize_session(
    session_id: str,
    _access_check: None = Depends(_require_frontend_access),
    db: Session = Depends(get_db),
):
    _purge_expired_sessions(db)
    session = db.get(AnalysisSession, _parse_session_id(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = SessionStatus.deleted
    session.report_markdown = None
    session.error_message = None
    session.client_id = None
    progress_store.update(session.id, progress=100, stage="Sesja zakończona przez użytkownika", status="deleted")
    progress_store.clear(session.id)
    db.commit()
    return FinalizeOut(id=session.id, status=session.status)


class AdminAuthRequest(BaseModel):
    password: str


@router.post("/admin/consents", response_model=list[ConsentRecord])
def get_all_consents(
    auth: AdminAuthRequest,
    _access_check: None = Depends(_require_frontend_access),
    db: Session = Depends(get_db),
):
    _purge_expired_sessions(db)
    settings = get_settings()
    if auth.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")

    sessions = db.query(AnalysisSession).order_by(AnalysisSession.created_at.desc()).all()
    return [
        ConsentRecord(
            id=session.id,
            created_at=session.created_at,
            status=session.status,
            consent_terms=session.consent_terms,
            consent_health_data=session.consent_health_data,
            consent_ai=session.consent_ai,
            anonymization_level=_normalize_anonymization_level(session.anonymization_level),
            client_id=session.client_id,
        )
        for session in sessions
    ]


def _purge_expired_sessions(db: Session) -> None:
    settings = get_settings()
    ttl_hours = max(settings.session_ttl_hours, 1)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

    stale_sessions = (
        db.query(AnalysisSession)
        .filter(
            AnalysisSession.created_at < cutoff,
            AnalysisSession.status.in_(
                (
                    SessionStatus.created,
                    SessionStatus.processing,
                    SessionStatus.completed,
                    SessionStatus.failed,
                )
            ),
        )
        .all()
    )

    if not stale_sessions:
        return

    for session in stale_sessions:
        session.status = SessionStatus.deleted
        session.report_markdown = None
        session.error_message = None
        session.client_id = None
        progress_store.clear(session.id)
    db.commit()
