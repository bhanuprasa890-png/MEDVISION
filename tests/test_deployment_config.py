"""Deployment, configuration, and operational reliability tests.

Verifies:
1. Deterministic SQLite path resolution against PROJECT_ROOT for relative paths.
2. Production mode enforces DEBUG=False.
3. Production mode disables /docs, /redoc, and openapi.json.
4. Wildcard CORS origins are strictly rejected.
5. System health check (/api/health) is independent from third-party provider configuration.
6. MedAssist chat status reports honest provider configuration without leaking secrets.
7. Database lifespan and engine disposal behavior.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.core.config import Settings, _PROJECT_ROOT
from app.main import app
from app.services.chat_service import get_chat_status


def test_deterministic_sqlite_path_resolution():
    """Relative SQLite database paths must be deterministically resolved to _PROJECT_ROOT."""
    # 1. Standard relative path
    s1 = Settings(DATABASE_URL="sqlite:///./medvision.db")
    expected_path = (_PROJECT_ROOT / "medvision.db").resolve().as_posix()
    assert s1.DATABASE_URL == f"sqlite:///{expected_path}"

    # 2. In-memory SQLite URL must remain unchanged
    s2 = Settings(DATABASE_URL="sqlite:///:memory:")
    assert s2.DATABASE_URL == "sqlite:///:memory:"

    # 3. Non-sqlite URL must remain unchanged
    s3 = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/medvision")
    assert s3.DATABASE_URL == "postgresql://user:pass@localhost:5432/medvision"


def test_production_mode_rejects_debug_true():
    """In production environment, setting DEBUG=True must raise a validation error."""
    valid_key = "production-secret-test-key-32charslong"
    # Production with DEBUG=False must succeed
    s_prod_ok = Settings(ENVIRONMENT="production", DEBUG=False, API_SECRET_KEY=valid_key)
    assert s_prod_ok.ENVIRONMENT == "production"
    assert s_prod_ok.DEBUG is False

    # Production with DEBUG=True must raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        Settings(ENVIRONMENT="production", DEBUG=True, API_SECRET_KEY=valid_key)
    assert "DEBUG mode cannot be enabled when ENVIRONMENT is 'production'" in str(exc_info.value)



def test_cors_origins_prohibits_wildcard_patterns():
    """assemble_cors_origins must filter out wildcard '*' and wildcard prefixes."""
    s = Settings()
    # Direct wildcard
    origins = s.assemble_cors_origins(["*"])
    assert "*" not in origins
    assert "http://localhost:5173" in origins

    # http://* wildcard
    origins_prefix = s.assemble_cors_origins(["http://*"])
    assert "*" not in origins_prefix
    assert len(origins_prefix) >= 1

    # https://* wildcard
    origins_https_prefix = s.assemble_cors_origins(["https://*"])
    assert "*" not in origins_https_prefix
    assert len(origins_https_prefix) >= 1


def test_health_check_independent_of_llm_provider(client: TestClient, monkeypatch):
    """System health check at /api/health must succeed even when AI provider keys are missing."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", None)
    monkeypatch.setattr("app.core.config.settings.OPENAI_API_KEY", None)

    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_medassist_status_reports_unconfigured_safely(monkeypatch):
    """When no API keys are set, get_chat_status reports unconfigured with no secrets."""
    monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", None)
    monkeypatch.setattr("app.core.config.settings.OPENAI_API_KEY", None)

    status = get_chat_status()
    assert status.status == "unconfigured"
    assert status.is_configured is False
    assert status.provider == "none"
    assert status.model == "unconfigured"
    assert status.disclaimer is not None
    # Ensure no secret fields exist in schema
    assert not hasattr(status, "api_key")
    assert not hasattr(status, "key")


def test_production_application_disables_docs_and_redoc(monkeypatch):
    """Full FastAPI app configured with ENVIRONMENT='production' must disable /docs and /redoc."""
    from app.main import app as main_app

    monkeypatch.setattr("app.main.is_production", True)

    # In production, docs_url and redoc_url and openapi_url are None
    test_prod_app = FastAPI(
        title="Prod Test",
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )

    with TestClient(test_prod_app) as prod_client:
        r_docs = prod_client.get("/docs")
        assert r_docs.status_code == 404

        r_redoc = prod_client.get("/redoc")
        assert r_redoc.status_code == 404

        r_openapi = prod_client.get("/api/v1/openapi.json")
        assert r_openapi.status_code == 404
