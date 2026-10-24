import os
from pathlib import Path
from typing import List, Set
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# Insecure default strings that must never be used in non-development environments
INSECURE_DEFAULT_SECRETS: Set[str] = {
    "namma-seva-super-secret-key-change-in-production-2026",
    "namma-seva-prod-secret-change-me-2026",
    "change-this-in-production-to-a-secure-random-string",
    "replace-with-a-secure-random-secret-key-for-jwt-signing"
}

INSECURE_DEFAULT_VERIFY_TOKENS: Set[str] = {
    "namma_seva_verify_token_2026",
    "your_whatsapp_verify_token_here"
}

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Namma Seva Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"  # Fail-closed default: non-dev unless explicitly set

    # Security
    SECRET_KEY: str = ""  # Must be set via env/secret manager
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Operating Modes
    DEMO_MODE: bool = False  # Fail-closed default: mock extraction blocked unless explicitly enabled

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
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    CALLMEBOT_APIKEY: str = ""

    # Knowledge Base Path
    PLAYBOOKS_DIR: str = str(PROJECT_ROOT / "knowledge" / "playbooks")
    SCHEMAS_DIR: str = str(PROJECT_ROOT / "knowledge" / "schemas")

    @model_validator(mode="after")
    def validate_production_secrets(self) -> 'Settings':
        env_clean = (self.ENVIRONMENT or "production").strip().lower()
        is_dev = env_clean in {"development", "dev", "test", "testing"}
        
        if is_dev:
            # Provide isolated local-only fallback if developers don't set keys
            if not self.SECRET_KEY:
                self.SECRET_KEY = "dev-insecure-key-never-use-in-production-min32chars"
            if not self.WHATSAPP_VERIFY_TOKEN:
                self.WHATSAPP_VERIFY_TOKEN = "dev_verify_token_local"
            return self

        # Non-development (production/staging or unset): strict fail-closed enforcement
        if not self.SECRET_KEY or self.SECRET_KEY in INSECURE_DEFAULT_SECRETS or len(self.SECRET_KEY) < 32:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: ENVIRONMENT is non-development ('production'), "
                "but SECRET_KEY is missing, insecure, or under 32 characters. Startup aborted."
            )
        if self.DEMO_MODE:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: DEMO_MODE cannot be enabled in "
                "production environments. Startup aborted."
            )
        if self.WHATSAPP_TOKEN and (
            not self.WHATSAPP_VERIFY_TOKEN or self.WHATSAPP_VERIFY_TOKEN in INSECURE_DEFAULT_VERIFY_TOKENS
        ):
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: WHATSAPP_VERIFY_TOKEN must be set to a "
                "custom secure token in non-development environments. Startup aborted."
            )
        return self


settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
