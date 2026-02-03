"""
ClaimIQ — Core Configuration
Reads from .env. Change DATABASE_URL for production — zero code changes needed.
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of cwd
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = "development"
    app_secret_key: str = "dev-secret-change-in-production"
    app_cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "sqlite+aiosqlite:///./claimiq.db"

    # Storage
    storage_backend: str = "local"
    storage_local_path: str = "./uploads"
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""
    r2_public_url: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # OCR
    tesseract_cmd: str = "tesseract"
    ocr_confidence_threshold: float = 0.80
    google_vision_api_key: str = ""
    google_vision_monthly_limit: int = 800

    # File handling
    max_file_size_mb: int = 10
    allowed_extensions: str = "pdf,jpg,jpeg,png,tiff,tif"
    session_ttl_hours: int = 24

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",")]

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",")}

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def mock_mode(self) -> bool:
        """If no Gemini key is set, run in mock mode (returns dummy data)."""
        return not self.gemini_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
