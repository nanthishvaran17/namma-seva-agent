import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Namma Seva Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "namma-seva-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    # Default to async sqlite for seamless local development without external dependencies
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BACKEND_ROOT}/namma_seva.db"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    # File Storage
    UPLOAD_DIR: str = str(BACKEND_ROOT / "storage" / "uploads")
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    # AI & Integrations Configuration
    LLM_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "namma_seva_verify_token_2026"

    # Knowledge Base Path
    PLAYBOOKS_DIR: str = str(PROJECT_ROOT / "knowledge" / "playbooks")
    SCHEMAS_DIR: str = str(PROJECT_ROOT / "knowledge" / "schemas")


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
