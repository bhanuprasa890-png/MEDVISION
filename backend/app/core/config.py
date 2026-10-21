"""Application configuration and environment settings."""

import json
from pathlib import Path
from typing import List, Optional, Union
from pydantic import ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict



_BACKEND_DIR: Path = Path(__file__).resolve().parents[2]
_PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings schema backed by environment variables."""

    # Project metadata
    PROJECT_NAME: str = "MedVision AI — Explainable Medical Imaging Research Assistant"
    VERSION: str = "0.1.0-alpha"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    @field_validator("DEBUG", mode="after")
    @classmethod
    def validate_debug_mode(cls, v: bool, info: ValidationInfo) -> bool:
        """Ensure debug mode is strictly disabled when ENVIRONMENT is set to production or staging."""
        env = info.data.get("ENVIRONMENT", "development")
        if isinstance(env, str) and env.lower() in ("production", "staging") and v is True:
            raise ValueError(
                f"DEBUG mode cannot be enabled when ENVIRONMENT is '{env}'. "
                f"Please set DEBUG=False in {env} configuration."
            )
        return v

    # Security & CORS: Strictly allow explicit local frontend development origin only
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        raw_list: List[str] = []
        if isinstance(v, str) and not v.startswith("["):
            raw_list = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    raw_list = [str(item).strip() for item in parsed]
            except Exception:
                pass
        elif isinstance(v, list):
            raw_list = [str(item).strip() for item in v]
        else:
            raw_list = ["http://localhost:5173", "http://127.0.0.1:5173"]

        # Security: Prohibit wildcard '*' origins when credentials are enabled
        filtered = [origin for origin in raw_list if origin != "*" and not origin.startswith("http://*") and not origin.startswith("https://*")]
        return filtered if filtered else ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Database: Deterministically resolve relative SQLite path to repository root
    DATABASE_URL: str = "sqlite:///./medvision.db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_database_url(cls, v: Union[str, Path]) -> str:
        """Resolve relative SQLite database paths against canonical PROJECT_ROOT."""
        if not isinstance(v, str):
            return str(v)
        v_stripped = v.strip()
        if v_stripped.startswith("sqlite:///") and not v_stripped.startswith("sqlite:///:memory:"):
            path_part = v_stripped[len("sqlite:///"):]
            p = Path(path_part)
            if not p.is_absolute():
                resolved = (_PROJECT_ROOT / p).resolve()
                return f"sqlite:///{resolved.as_posix()}"
        return v_stripped

    # RetinaGuard Checkpoint Configuration
    RETINA_CHECKPOINT_PATH: Optional[str] = None

    @property
    def PROJECT_ROOT(self) -> Path:
        """Resolve absolute path to project repository root."""
        return _PROJECT_ROOT

    @property
    def BACKEND_DIR(self) -> Path:
        """Resolve absolute path to backend directory."""
        return _BACKEND_DIR

    # File Upload Security Restrictions
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
    ]

    ALLOWED_FILE_EXTENSIONS: List[str] = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    ]

    # MedAssist Health-Education Chatbot Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_API_BASE: Optional[str] = None
    MEDASSIST_TIMEOUT_SECONDS: float = 30.0
    MEDASSIST_MAX_INPUT_LENGTH: int = 1000
    MEDASSIST_MAX_HISTORY_TURNS: int = 20
    MEDASSIST_MAX_RESPONSE_TOKENS: int = 2048
    MEDASSIST_MAX_RETRIES: int = 2
    MEDASSIST_RETRY_INITIAL_DELAY: float = 1.0
    MEDASSIST_RETRY_MAX_DELAY: float = 8.0
    MEDASSIST_RETRY_JITTER: bool = True
    MEDASSIST_OVERALL_TIMEOUT_SECONDS: float = 60.0
    MEDASSIST_ENABLE_FALLBACK: bool = True

    # Rate Limiting & Abuse Prevention
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CHAT_PER_MINUTE: int = 30
    RATE_LIMIT_INFERENCE_PER_MINUTE: int = 20
    RATE_LIMIT_GENERAL_PER_MINUTE: int = 120
    TRUSTED_PROXIES: List[str] = ["127.0.0.1", "::1", "testclient"]
    REDIS_URL: Optional[str] = None
    RATE_LIMIT_STRICT_FAIL_CLOSED: bool = False

    # Authentication & API Key Authorization (Optional for local demo, required for staging/prod)
    API_SECRET_KEY: Optional[str] = None

    # Maximum Payload Size Limits (defense-in-depth against body buffer exhaustion)
    MAX_JSON_PAYLOAD_BYTES: int = 1_048_576  # 1 MB
    MAX_CONTENT_LENGTH_BYTES: int = 15_728_640  # 15 MB for image uploads

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        """Strictly enforce production and staging security requirements at bootstrap."""
        env_lower = self.ENVIRONMENT.lower()
        if env_lower in ("production", "staging"):
            if self.DEBUG:
                raise ValueError(f"DEBUG mode cannot be enabled when ENVIRONMENT is '{self.ENVIRONMENT}'.")
            if not self.API_SECRET_KEY or len(self.API_SECRET_KEY.strip()) < 16:
                raise ValueError(
                    f"{self.ENVIRONMENT.capitalize()} deployment requires a secure API_SECRET_KEY of at least 16 characters. "
                    f"Please configure a valid API_SECRET_KEY in your {self.ENVIRONMENT} environment."
                )
            for origin in self.BACKEND_CORS_ORIGINS:
                if origin == "*" or origin.startswith("http://*") or origin.startswith("https://*"):
                    raise ValueError(f"Wildcard CORS origins are strictly prohibited in {self.ENVIRONMENT}.")
        return self



    model_config = SettingsConfigDict(
        env_file=(
            str(_PROJECT_ROOT / ".env"),
            str(_BACKEND_DIR / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
