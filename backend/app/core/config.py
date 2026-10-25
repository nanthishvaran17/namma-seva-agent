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
    DOC_ENCRYPTION_KEY: str = ""  # Dedicated 256-bit key for sensitive documents at rest
    FIELD_ENCRYPTION_KEY: str = ""  # Dedicated 256-bit key for field-level encryption (PII)
    BLIND_INDEX_KEY: str = ""  # Dedicated 256-bit key for phone number blind indexing
    DELETION_PEPPER: str = ""  # Dedicated 256-bit pepper for HMAC-SHA256 deletion receipts
    CURRENT_DOC_KEY_VERSION: str = "1"
    CURRENT_FIELD_KEY_VERSION: str = "1"
    CURRENT_BLIND_INDEX_KEY_VERSION: str = "1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Operating Modes
    DEMO_MODE: bool = False  # Fail-closed default: mock extraction blocked unless explicitly enabled
    ALLOW_LEGACY_FLE: bool = False  # Fail-closed default: legacy FLE (no AAD) rejected unless explicitly enabled during migration window

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

    # Rate Limiting & Proxy Configuration
    RATE_LIMIT_ENABLED: bool = True
    TRUSTED_PROXIES: List[str] = []  # e.g. ["127.0.0.1", "10.0.0.0/8"]. If empty, X-Forwarded-For is never trusted.
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_CHAT_PER_MINUTE: int = 20
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 10
    RATE_LIMIT_WEBHOOK_PER_MINUTE: int = 300  # Generous limit for high-volume authenticated Meta webhook events

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
            if not self.DOC_ENCRYPTION_KEY:
                self.DOC_ENCRYPTION_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            if not self.FIELD_ENCRYPTION_KEY:
                self.FIELD_ENCRYPTION_KEY = "field-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
            if not self.BLIND_INDEX_KEY:
                self.BLIND_INDEX_KEY = "blind-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
            if not self.DELETION_PEPPER:
                self.DELETION_PEPPER = "pepper-sec-0123456789abcdef0123456789abcdef0123456789abcdef"
            if not self.WHATSAPP_VERIFY_TOKEN:
                self.WHATSAPP_VERIFY_TOKEN = "dev_verify_token_local"
            if not self.WHATSAPP_APP_SECRET:
                self.WHATSAPP_APP_SECRET = "dev_whatsapp_app_secret_16chars_min"
            return self

        # Non-development (production/staging or unset): strict fail-closed enforcement
        keys_map = {
            "SECRET_KEY": self.SECRET_KEY,
            "DOC_ENCRYPTION_KEY": self.DOC_ENCRYPTION_KEY,
            "FIELD_ENCRYPTION_KEY": self.FIELD_ENCRYPTION_KEY,
            "BLIND_INDEX_KEY": self.BLIND_INDEX_KEY,
            "DELETION_PEPPER": self.DELETION_PEPPER,
        }
        for name, val in keys_map.items():
            if not val or len(val) < 32 or val in INSECURE_DEFAULT_SECRETS:
                raise ValueError(
                    f"CRITICAL SECURITY CONFIGURATION ERROR: ENVIRONMENT is non-development ('production'), "
                    f"but {name} is missing, insecure, or under 32 characters. Startup aborted."
                )

        # Strict 5-way pairwise key separation verification
        names = list(keys_map.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if keys_map[names[i]] == keys_map[names[j]]:
                    raise ValueError(
                        f"CRITICAL SECURITY CONFIGURATION ERROR: Key separation violation. "
                        f"{names[i]} cannot equal {names[j]}. All 5 security keys must be strictly distinct. Startup aborted."
                    )
        if not self.WHATSAPP_APP_SECRET or len(self.WHATSAPP_APP_SECRET) < 16:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: ENVIRONMENT is non-development ('production'), "
                "but WHATSAPP_APP_SECRET is missing or insecure (must be at least 16 characters). "
                "Meta webhook signature verification requires an application secret in production. Startup aborted."
            )
        if self.DEMO_MODE:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: DEMO_MODE cannot be enabled in "
                "production environments. Startup aborted."
            )
        if self.ALLOW_LEGACY_FLE:
            raise ValueError(
                "CRITICAL SECURITY CONFIGURATION ERROR: ALLOW_LEGACY_FLE cannot be enabled in "
                "production environments. It is only permitted during the migration window in "
                "dev/test. Startup aborted."
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
