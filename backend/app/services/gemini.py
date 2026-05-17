import os
import json
from pathlib import Path
from typing import Any

import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
import requests

from app.core.config import get_settings

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompt.txt"


def _load_system_prompt() -> str:
    """Load system prompt from prompt.txt file."""
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8").strip()
    return "Porównaj wyniki badań A i B, wskaż trendy zmian w formacie Markdown."


DISCLAIMER = "**Powyższa analiza jest generowana automatycznie i służy celom edukacyjnym. Skonsultuj wyniki z lekarzem.**"
DISCLAIMER_PHRASE = "skonsultuj wyniki z lekarzem"
REQUIRED_SECTIONS: tuple[tuple[str, str], ...] = (
    ("Tabela porównawcza", "Brak wystarczających danych do zestawienia tabeli porównawczej."),
    ("Kluczowe zmiany", "- Brak jednoznacznych zmian do wyróżnienia na podstawie dostarczonych danych."),
    ("Uwagi", "- Brak dodatkowych uwag."),
    ("Podpowiedź dla lekarza", "- Jakie elementy wyniku wymagają dodatkowej weryfikacji klinicznej?"),
)


def _ensure_required_sections(report: str) -> str:
    cleaned = report.strip()
    if not cleaned:
        cleaned = ""

    lower = cleaned.lower()
    missing_blocks: list[str] = []
    for section_name, fallback_content in REQUIRED_SECTIONS:
        if section_name.lower() not in lower:
            missing_blocks.append(f"## {section_name}\n{fallback_content}")

    if not missing_blocks:
        return cleaned

    separator = "\n\n" if cleaned else ""
    missing_joined = "\n\n".join(missing_blocks)
    return f"{cleaned}{separator}{missing_joined}".strip()


def _ensure_disclaimer(report: str) -> str:
    cleaned = _ensure_required_sections(report).strip()
    if DISCLAIMER_PHRASE in cleaned.lower():
        return cleaned
    return f"{cleaned}\n\n{DISCLAIMER}".strip()


def _extract_text_from_response(data: dict[str, Any]) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""

    # Some responses contain multiple parts or non-text parts first.
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        texts: list[str] = []
        for part in parts:
            piece = (part.get("text") or "").strip()
            if piece:
                texts.append(piece)
        if texts:
            return "\n".join(texts).strip()
    return ""


def _build_prompt(text_a: str, text_b: str, medical_context: str = "") -> str:
    system_prompt = _load_system_prompt()
    return (
        f"{system_prompt}\n\nDANE WEJŚCIOWE:\n"
        f"[Tekst z Badania A]\n{text_a}\n\n"
        f"[Tekst z Badania B]\n{text_b}\n"
        f"{medical_context}"
    )


def _extract_model_version(data: dict[str, Any]) -> str | None:
    version = (data.get("modelVersion") or data.get("model_version") or "").strip()
    return version or None


def _call_gemini(prompt: str) -> tuple[str, str, str | None]:
    settings = get_settings()
    api_key = (settings.gemini_api_key or "").strip()
    if not api_key:
        raise RuntimeError(
            "Brak konfiguracji GEMINI_API_KEY. Ustaw w .env: GEMINI_API_KEY=<Twoj_klucz_Gemini_API>."
        )

    url = f"{settings.gemini_api_url}/models/{settings.gemini_model}:generateContent"
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
    }
    response = requests.post(
        url,
        params={"key": api_key},
        json=payload,
        timeout=settings.ai_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    text = _extract_text_from_response(data)
    if not text:
        raise RuntimeError("Gemini zwrócił pustą odpowiedź.")
    return text, settings.gemini_model, _extract_model_version(data)


def _vertex_access_token() -> str:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    if not credentials.valid:
        credentials.refresh(GoogleAuthRequest())
    token = credentials.token
    if not token:
        raise RuntimeError("Nie udało się pobrać tokenu dostępowego Vertex AI.")
    return token


def _resolve_vertex_project_id() -> str:
    settings = get_settings()
    configured = (settings.vertex_project_id or "").strip()
    if configured:
        return configured

    for env_name in ("GOOGLE_CLOUD_PROJECT", "GCLOUD_PROJECT", "GCP_PROJECT"):
        value = os.getenv(env_name, "").strip()
        if value:
            return value

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if credentials_path:
        try:
            with open(credentials_path, encoding="utf-8") as f:
                payload = json.load(f)
            project_id = str(payload.get("project_id", "")).strip()
            if project_id:
                return project_id
        except Exception:
            # Fallback to ADC detection below.
            pass

    try:
        _, discovered_project = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    except Exception:  # pragma: no cover - depends on runtime auth setup
        discovered_project = None

    if discovered_project:
        return discovered_project

    raise RuntimeError(
        "Brak projektu Google Cloud dla Vertex AI. Ustaw VERTEX_PROJECT_ID (lub GOOGLE_CLOUD_PROJECT), "
        "albo skonfiguruj ADC: `gcloud auth application-default login` i `gcloud config set project <PROJECT_ID>`."
    )


def _vertex_project_available() -> bool:
    try:
        _resolve_vertex_project_id()
        return True
    except Exception:
        return False


def _call_vertex(prompt: str) -> tuple[str, str, str | None]:
    settings = get_settings()
    project_id = _resolve_vertex_project_id()

    generation_config: dict[str, Any] = {
        "temperature": 0.2,
        "maxOutputTokens": 8192,
    }
    # Gemini 2.5 can spend output budget on "thinking" and return no text.
    # Disable thinking budget to prioritize deterministic text output.
    if settings.vertex_model.startswith("gemini-2.5"):
        generation_config["thinkingConfig"] = {"thinkingBudget": 0}

    url = (
        f"https://{settings.vertex_location}-aiplatform.googleapis.com/v1/projects/"
        f"{project_id}/locations/{settings.vertex_location}/publishers/google/models/"
        f"{settings.vertex_model}:generateContent"
    )
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {_vertex_access_token()}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=settings.ai_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    text = _extract_text_from_response(data)
    if not text:
        finish_reason = ((data.get("candidates") or [{}])[0].get("finishReason") or "unknown")
        thoughts_tokens = (data.get("usageMetadata") or {}).get("thoughtsTokenCount")
        raise RuntimeError(
            "Vertex AI zwrócił pustą odpowiedź "
            f"(finishReason={finish_reason}, thoughtsTokenCount={thoughts_tokens})."
        )
    return text, settings.vertex_model, _extract_model_version(data)


def _provider_sequence() -> list[str]:
    settings = get_settings()
    provider = settings.ai_provider.lower().strip()
    if provider == "vertex":
        return ["vertex"]
    if provider == "gemini":
        return ["gemini"]
    if provider == "auto":
        candidates: list[str] = []
        if _vertex_project_available():
            candidates.append("vertex")
        if settings.gemini_api_key:
            candidates.append("gemini")
        return candidates
    raise RuntimeError("AI_PROVIDER musi mieć wartość: auto, vertex albo gemini.")


def _vertex_region_to_country(region: str) -> str | None:
    mapping = {
        "europe-central2": "Polska",
        "europe-west1": "Belgia",
        "europe-west2": "Wielka Brytania",
        "europe-west3": "Niemcy",
        "europe-west4": "Niderlandy",
        "europe-west6": "Szwajcaria",
        "europe-west8": "Włochy",
        "europe-west9": "Francja",
        "europe-west10": "Niemcy",
        "europe-west12": "Włochy",
        "us-central1": "Stany Zjednoczone",
        "us-east1": "Stany Zjednoczone",
        "us-east4": "Stany Zjednoczone",
        "us-west1": "Stany Zjednoczone",
        "us-west4": "Stany Zjednoczone",
    }
    return mapping.get(region)


def _region_country_for_provider(provider: str) -> tuple[str | None, str | None]:
    settings = get_settings()
    if provider == "vertex":
        region = settings.vertex_location
        return region, _vertex_region_to_country(region)
    if provider == "gemini":
        # Gemini Developer API does not guarantee fixed processing country for each request.
        return "global", "Nieokreślony (Gemini API global)"
    return None, None


def generate_report(text_a: str, text_b: str, medical_context: str = "") -> dict[str, str | None]:
    """Always attempts Google AI providers and returns AI-generated report."""
    prompt = _build_prompt(text_a, text_b, medical_context=medical_context)
    providers = _provider_sequence()
    if not providers:
        raise RuntimeError(
            "Brak aktywnej konfiguracji AI. Ustaw w pliku .env: "
            "AI_PROVIDER=vertex oraz VERTEX_PROJECT_ID=<PROJECT_ID> "
            "(lub skonfiguruj ADC: `gcloud auth application-default login` + `gcloud config set project <PROJECT_ID>`). "
            "Alternatywnie: AI_PROVIDER=gemini oraz GEMINI_API_KEY=<Twoj_klucz_Gemini_API>."
        )

    errors: list[str] = []
    for provider in providers:
        try:
            if provider == "vertex":
                ai_text, requested_model, model_version = _call_vertex(prompt)
            else:
                ai_text, requested_model, model_version = _call_gemini(prompt)
            executed_model = model_version or requested_model
            region, country = _region_country_for_provider(provider)
            return {
                "report": _ensure_disclaimer(ai_text),
                "prompt_sent": prompt,
                "ai_provider": provider,
                "ai_model": executed_model,
                "ai_model_requested": requested_model,
                "ai_region": region,
                "ai_country": country,
            }
        except Exception as exc:
            errors.append(f"{provider}: {exc}")

    raise RuntimeError("Wszystkie próby wywołania AI nie powiodły się: " + " | ".join(errors))
