from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Diag1"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/diag1"

    ai_provider: str = "vertex"  # auto | vertex | gemini

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_api_url: str = "https://generativelanguage.googleapis.com/v1beta"

    vertex_project_id: str | None = None
    vertex_location: str = "europe-west3"
    vertex_model: str = "gemini-2.5-flash"

    ai_timeout_seconds: int = 120
    session_ttl_hours: int = 24

    cors_origins: str = "http://localhost:9517,http://localhost:9080"

    # UWAGA: w produkcji ZAWSZE nadpisz zmienną środowiskową ADMIN_PASSWORD.
    # Poniższa wartość to celowy placeholder — nie jest realnym hasłem.
    admin_password: str = "CHANGE_ME_SET_ADMIN_PASSWORD_ENV"
    frontend_access_password: str | None = None
    frontend_access_cookie_secret: str | None = None
    frontend_access_session_ttl_hours: int = 12


@lru_cache
def get_settings() -> Settings:
    return Settings()
