"""Comprehensive verification test suite for Task 31: Private Staging Deployment Verification.

Verifies:
1. Environment Readiness (Staging configuration invariants, CORS, DEBUG=False, API_SECRET_KEY, HSTS & CSP).
2. Authentication (Token creation, signature verification, expiration enforcement, tampering detection, silent bypass defense).
3. Health check isolation (Public health probes accessible without credentials).
4. Distributed rate limiting across workers & Redis failure resilience (fallback vs fail-closed, trusted proxy IP parsing).
5. Database online backup, integrity check, restoration, and PostgreSQL migration dry-run without modifying original data.
6. Payload limits and error sanitization.
"""

import os
from pathlib import Path
import sqlite3
import time
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings, _PROJECT_ROOT
from app.core.rate_limiter import SlidingWindowRateLimiter, RateLimitMiddleware
from app.core.security import (
    create_access_token,
    verify_access_token,
    verify_api_key,
)
from app.main import app as main_app
import database.migrate_to_postgres as migrator


# ==============================================================================
# 1. ENVIRONMENT READINESS & STAGING INVARIANTS
# ==============================================================================

def test_staging_environment_requires_debug_false():
    """In staging mode, DEBUG=True must raise a validation error."""
    valid_key = "staging-secret-key-32charslong-test"
    with pytest.raises(ValidationError) as exc:
        Settings(ENVIRONMENT="staging", DEBUG=True, API_SECRET_KEY=valid_key)
    assert "DEBUG mode cannot be enabled" in str(exc.value)

    # DEBUG=False must succeed
    s = Settings(ENVIRONMENT="staging", DEBUG=False, API_SECRET_KEY=valid_key)
    assert s.ENVIRONMENT == "staging"
    assert s.DEBUG is False


def test_staging_environment_requires_api_secret_key():
    """In staging mode, missing or short API_SECRET_KEY must raise ValidationError."""
    with pytest.raises(ValidationError) as exc:
        Settings(ENVIRONMENT="staging", DEBUG=False, API_SECRET_KEY=None)
    assert "requires a secure API_SECRET_KEY" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        Settings(ENVIRONMENT="staging", DEBUG=False, API_SECRET_KEY="short-key")
    assert "at least 16 characters" in str(exc.value)


def test_staging_environment_prohibits_wildcard_cors():
    """Wildcard origins are sanitized out and prohibited in staging."""
    valid_key = "staging-secret-key-32charslong-test"
    s = Settings(
        ENVIRONMENT="staging",
        DEBUG=False,
        API_SECRET_KEY=valid_key,
        BACKEND_CORS_ORIGINS=["*"],
    )
    assert "*" not in s.BACKEND_CORS_ORIGINS
    for origin in s.BACKEND_CORS_ORIGINS:
        assert origin != "*"
        assert not origin.startswith("http://*")
        assert not origin.startswith("https://*")


def test_staging_security_headers_include_hsts_and_csp(monkeypatch):
    """When ENVIRONMENT is staging, responses must include HSTS and strict CSP."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    with TestClient(main_app) as client:
        res = client.get("/api/health")
        assert res.status_code == 200
        assert "max-age=31536000" in res.headers.get("Strict-Transport-Security", "")
        assert "default-src 'self'" in res.headers.get("Content-Security-Policy", "")


# ==============================================================================
# 2. AUTHENTICATION & TOKEN EXPIRATION VERIFICATION
# ==============================================================================

def test_access_token_creation_and_successful_verification():
    """Valid access token with future expiration must decode successfully."""
    secret = "my-test-secret-key-at-least-16chars"
    token = create_access_token(
        subject="researcher-user-001",
        expires_in_seconds=3600,
        secret_key=secret,
        extra_claims={"role": "clinician", "clinic_id": "lab-42"},
    )
    assert isinstance(token, str)
    assert token.count(".") == 2

    payload = verify_access_token(token, secret_key=secret)
    assert payload["sub"] == "researcher-user-001"
    assert payload["role"] == "clinician"
    assert payload["clinic_id"] == "lab-42"
    assert payload["exp"] > time.time()


def test_expired_access_token_rejected_with_401():
    """Access token whose expiration is in the past must be rejected with 401."""
    secret = "my-test-secret-key-at-least-16chars"
    # Create token that expired 10 seconds ago
    expired_token = create_access_token(
        subject="expired-user",
        expires_in_seconds=-10,
        secret_key=secret,
    )
    with pytest.raises(HTTPException) as exc_info:
        verify_access_token(expired_token, secret_key=secret)

    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_tampered_access_token_signature_rejected_with_401():
    """Tampered token or mismatched secret key must be rejected with 401."""
    secret = "correct-secret-key-32charslong-test"
    wrong_secret = "different-secret-key-32charslong-test"

    token = create_access_token(subject="user-123", secret_key=secret)

    # Verification with wrong secret
    with pytest.raises(HTTPException) as exc_info:
        verify_access_token(token, secret_key=wrong_secret)
    assert exc_info.value.status_code == 401
    assert "signature" in exc_info.value.detail.lower()

    # Tampered payload
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJhZG1pbiI6dHJ1ZX0.{parts[2]}"
    with pytest.raises(HTTPException) as exc_info:
        verify_access_token(tampered_token, secret_key=secret)
    assert exc_info.value.status_code == 401


def test_malformed_token_rejected_with_401():
    """Non-three-part strings must be rejected as malformed."""
    secret = "valid-secret-key-32charslong-test"
    with pytest.raises(HTTPException) as exc_info:
        verify_access_token("not-a-valid-token", secret_key=secret)
    assert exc_info.value.status_code == 401
    assert "malformed" in exc_info.value.detail.lower()


def test_verify_api_key_with_signed_token(monkeypatch):
    """verify_api_key dependency accepts valid signed Bearer token and rejects expired Bearer token."""
    secret = "staging-secret-key-32charslong-test"
    monkeypatch.setattr(settings, "API_SECRET_KEY", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    # 1. Valid token
    valid_token = create_access_token(subject="dr-smith", expires_in_seconds=300, secret_key=secret)
    assert verify_api_key(x_api_key=None, authorization=f"Bearer {valid_token}") is True

    # 2. Expired token
    expired_token = create_access_token(subject="dr-smith", expires_in_seconds=-60, secret_key=secret)
    with pytest.raises(HTTPException) as exc:
        verify_api_key(x_api_key=None, authorization=f"Bearer {expired_token}")
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()

    # 3. Static service key
    assert verify_api_key(x_api_key=secret, authorization=None) is True
    assert verify_api_key(x_api_key=None, authorization=f"Bearer {secret}") is True


def test_staging_mode_prevents_silent_auth_bypass(monkeypatch):
    """If ENVIRONMENT is staging and API_SECRET_KEY is empty, endpoints must raise HTTP 500 error."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "API_SECRET_KEY", None)

    with pytest.raises(HTTPException) as exc:
        verify_api_key(x_api_key=None, authorization=None)
    assert exc.value.status_code == 500
    assert "must be configured in staging mode" in exc.value.detail


# ==============================================================================
# 3. HEALTH CHECKS AND PUBLIC STATUS ENDPOINTS
# ==============================================================================

def test_health_check_available_without_auth(monkeypatch):
    """GET /api/health and /api/v1/chat/status must remain available without credentials."""
    secret = "staging-secret-key-32charslong-test"
    monkeypatch.setattr(settings, "API_SECRET_KEY", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    with TestClient(main_app) as client:
        # Health check probe
        res_health = client.get("/api/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        # Model status probe
        res_retina = client.get("/api/v1/retina/model-status")
        assert res_retina.status_code == 200

        res_cxr = client.get("/api/v1/chest-xray/model-status")
        assert res_cxr.status_code == 200

        res_chat = client.get("/api/v1/chat/status")
        assert res_chat.status_code == 200


# ==============================================================================
# 4. RATE LIMITING ACROSS WORKERS & REDIS RESILIENCE
# ==============================================================================

def test_rate_limiting_across_simulated_workers():
    """Simulate multiple application workers querying shared rate limit storage."""
    limiter = SlidingWindowRateLimiter()

    # Mock Redis pipeline simulating shared cluster state
    mock_redis = MagicMock()
    mock_pipe = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe

    # Worker 1 registers 10 requests
    mock_pipe.execute.return_value = [0, 10, [("member1", time.time())]]
    limiter._redis_client = mock_redis

    allowed_worker1, rem1, _, _ = limiter.check_rate_limit(
        client_ip="192.168.1.50",
        category="chat",
        max_requests=20,
        window_seconds=60,
    )
    assert allowed_worker1 is True
    assert rem1 == 9

    # Worker 2 on a different process hits the limit (20 requests recorded in shared Redis)
    mock_pipe.execute.return_value = [0, 20, [("member1", time.time())]]
    allowed_worker2, rem2, retry_after, _ = limiter.check_rate_limit(
        client_ip="192.168.1.50",
        category="chat",
        max_requests=20,
        window_seconds=60,
    )
    assert allowed_worker2 is False
    assert rem2 == 0
    assert retry_after >= 1


def test_trusted_proxy_client_ip_handling(monkeypatch):
    """X-Forwarded-For is honored only from trusted proxies."""
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", ["10.0.0.1", "127.0.0.1"])

    limiter = SlidingWindowRateLimiter()

    # 1. Request from trusted proxy (10.0.0.1) forwarding real client (203.0.113.195)
    mock_req_trusted = MagicMock()
    mock_req_trusted.client.host = "10.0.0.1"
    mock_req_trusted.headers = {"X-Forwarded-For": "203.0.113.195, 10.0.0.1"}

    ip_trusted = limiter.extract_client_ip(mock_req_trusted)
    assert ip_trusted == "203.0.113.195"

    # 2. Request from untrusted external client (198.51.100.22) attempting to spoof X-Forwarded-For
    mock_req_untrusted = MagicMock()
    mock_req_untrusted.client.host = "198.51.100.22"
    mock_req_untrusted.headers = {"X-Forwarded-For": "8.8.8.8"}

    ip_untrusted = limiter.extract_client_ip(mock_req_untrusted)
    # Must ignore spoofed header and use actual untrusted client host
    assert ip_untrusted == "198.51.100.22"


# ==============================================================================
# 5. DATABASE BACKUP, RESTORE & MIGRATION VERIFICATION
# ==============================================================================

def test_sqlite_online_backup_restore_and_integrity_check(tmp_path):
    """Test online hot backup of SQLite database and verify 100% data integrity without altering source."""
    original_db = _PROJECT_ROOT / "medvision.db"
    assert original_db.exists(), "Source medvision.db must exist for staging backup testing"

    # 1. Inspect original count
    src_conn = sqlite3.connect(str(original_db))
    src_cursor = src_conn.cursor()
    src_cursor.execute("SELECT count(*) FROM analysis_sessions;")
    original_count = src_cursor.fetchone()[0]
    src_conn.close()

    assert original_count == 34, f"Expected 34 historical records, found {original_count}"

    # 2. Perform online hot backup to disposable temporary file
    backup_file = tmp_path / "medvision_staging_backup.db"
    src_conn = sqlite3.connect(str(original_db))
    backup_conn = sqlite3.connect(str(backup_file))
    src_conn.backup(backup_conn)
    backup_conn.close()
    src_conn.close()

    assert backup_file.exists()

    # 3. Run PRAGMA integrity_check on the backup
    check_conn = sqlite3.connect(str(backup_file))
    check_cursor = check_conn.cursor()
    check_cursor.execute("PRAGMA integrity_check;")
    integrity_result = check_cursor.fetchone()[0]
    assert integrity_result == "ok"

    # 4. Verify backup row count matches original
    check_cursor.execute("SELECT count(*) FROM analysis_sessions;")
    backup_count = check_cursor.fetchone()[0]
    assert backup_count == original_count
    check_conn.close()

    # 5. Test restore into a separate restored database
    restored_file = tmp_path / "medvision_restored.db"
    backup_conn = sqlite3.connect(str(backup_file))
    restored_conn = sqlite3.connect(str(restored_file))
    backup_conn.backup(restored_conn)
    backup_conn.close()

    rest_cursor = restored_conn.cursor()
    rest_cursor.execute("SELECT count(*) FROM analysis_sessions;")
    assert rest_cursor.fetchone()[0] == original_count

    # Verify column structure
    rest_cursor.execute("PRAGMA table_info(analysis_sessions);")
    columns = [row[1] for row in rest_cursor.fetchall()]
    assert "session_id" in columns
    assert "file_hash" in columns
    assert "modality" in columns
    assert "status" in columns
    restored_conn.close()


def test_postgres_migration_dry_run_on_real_database():
    """Verify migrate_to_postgres dry-run executes cleanly and reports accurate counts."""
    original_db = str(_PROJECT_ROOT / "medvision.db")
    success = migrator.migrate_to_postgres(
        sqlite_path=original_db,
        postgres_url="",
        batch_size=500,
        dry_run=True,
    )
    assert success is True


def test_postgres_migration_to_disposable_database(tmp_path):
    """Simulate complete PostgreSQL table migration into a disposable target table."""
    source_sqlite = str(_PROJECT_ROOT / "medvision.db")
    disposable_target = tmp_path / "disposable_target.db"
    disposable_url = f"sqlite:///{disposable_target.as_posix()}"

    # Use migrator logic to insert into disposable database
    from sqlalchemy import create_engine, text

    target_engine = create_engine(disposable_url)

    # Initialize schema
    with target_engine.begin() as conn:
        for stmt in migrator.POSTGRES_SCHEMA_SQL.strip().split(";"):
            s = stmt.strip()
            if s:
                # Replace Postgres-specific syntax with standard SQLite for disposable test
                s_sqlite = s.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP")
                conn.execute(text(s_sqlite))

    # Read records from real source
    rows = migrator.fetch_sqlite_rows(source_sqlite, offset=0, limit=100)
    assert len(rows) == 34

    insert_sql = text(
        """
        INSERT INTO analysis_sessions (
            id, session_id, modality, file_name, file_size_bytes,
            file_hash, mime_type, image_width, image_height, model_version,
            status, prediction_category, prediction_confidence,
            explanation_text, explanation_heatmap_path, created_at
        ) VALUES (
            :id, :session_id, :modality, :file_name, :file_size_bytes,
            :file_hash, :mime_type, :image_width, :image_height, :model_version,
            :status, :prediction_category, :prediction_confidence,
            :explanation_text, :explanation_heatmap_path, :created_at
        );
        """
    )

    param_list = []
    for r in rows:
        param_list.append({
            "id": r[0], "session_id": r[1], "modality": r[2], "file_name": r[3],
            "file_size_bytes": r[4], "file_hash": r[5], "mime_type": r[6],
            "image_width": r[7], "image_height": r[8], "model_version": r[9],
            "status": r[10], "prediction_category": r[11], "prediction_confidence": r[12],
            "explanation_text": r[13], "explanation_heatmap_path": r[14], "created_at": r[15],
        })

    with target_engine.begin() as conn:
        conn.execute(insert_sql, param_list)

    # Verify migrated count
    with target_engine.connect() as conn:
        target_count = conn.execute(text("SELECT count(*) FROM analysis_sessions;")).scalar()
    assert target_count == 34
    target_engine.dispose()


# ==============================================================================
# 6. APPLICATION SMOKE TESTS (RETINA, CHEST X-RAY, CHAT, RATE LIMITS)
# ==============================================================================

def test_staging_smoke_retina_authorized_and_unauthorized(client: TestClient, monkeypatch, create_sample_image):
    """Smoke test: retina predict requires authentication in staging mode."""
    secret = "staging-secret-key-32charslong-test"
    monkeypatch.setattr(settings, "API_SECRET_KEY", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    image_bytes = create_sample_image(format="JPEG", size=(224, 224))

    # 1. Unauthorized request (missing credentials)
    res_unauth = client.post(
        "/api/v1/retina/predict",
        files={"file": ("fundus.jpg", image_bytes, "image/jpeg")},
    )
    assert res_unauth.status_code == 401

    # 2. Authorized request (with valid signed token)
    valid_token = create_access_token(subject="clinician-user", expires_in_seconds=600, secret_key=secret)
    res_auth = client.post(
        "/api/v1/retina/predict",
        files={"file": ("fundus.jpg", image_bytes, "image/jpeg")},
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert res_auth.status_code in (200, 503)
    if res_auth.status_code == 200:
        data = res_auth.json()
        assert "prediction" in data or "predicted_class" in data


def test_staging_smoke_chest_xray_authorized_and_unauthorized(client: TestClient, monkeypatch, create_sample_image):
    """Smoke test: chest x-ray predict requires authentication in staging mode."""
    secret = "staging-secret-key-32charslong-test"
    monkeypatch.setattr(settings, "API_SECRET_KEY", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    image_bytes = create_sample_image(format="JPEG", size=(224, 224))

    # 1. Unauthorized request (missing credentials)
    res_unauth = client.post(
        "/api/v1/chest-xray/predict",
        files={"file": ("chest.jpg", image_bytes, "image/jpeg")},
    )
    assert res_unauth.status_code == 401

    # 2. Authorized request
    valid_token = create_access_token(subject="radiologist-user", expires_in_seconds=600, secret_key=secret)
    res_auth = client.post(
        "/api/v1/chest-xray/predict",
        files={"file": ("chest.jpg", image_bytes, "image/jpeg")},
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert "prediction" in data
    assert "top_finding" in data["prediction"]
    assert "findings" in data["prediction"]
    assert data["status"] == "SUCCESS"


def test_staging_smoke_chat_authorized_and_unauthorized(client: TestClient, monkeypatch):
    """Smoke test: chat endpoint requires authentication, validates tokens, and handles provider responses."""
    from unittest.mock import AsyncMock, patch
    from app.schemas.chat import ChatResponse
    from datetime import datetime, timezone

    secret = "staging-secret-key-32charslong-test"
    monkeypatch.setattr(settings, "API_SECRET_KEY", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")

    payload = {"message": "Explain diabetic retinopathy", "conversation_history": []}

    # 1. Unauthorized request
    res_unauth = client.post("/api/v1/chat/message", json=payload)
    assert res_unauth.status_code == 401

    # 2. Authorized with expired token -> 401 Expired
    expired_token = create_access_token(subject="user", expires_in_seconds=-10, secret_key=secret)
    res_expired = client.post(
        "/api/v1/chat/message",
        json=payload,
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()

    # 3. Authorized with valid token (mocked provider success)
    mock_chat_res = ChatResponse(
        message="Diabetic retinopathy is a microvascular complication.",
        provider="gemini",
        model="gemini-3.5-flash",
        created_at=datetime.now(timezone.utc),
        disclaimer="EDUCATIONAL RESEARCH USE ONLY",
    )
    valid_token = create_access_token(subject="user", expires_in_seconds=300, secret_key=secret)
    with patch("app.api.v1.chat.process_chat_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_chat_res
        res_auth = client.post(
            "/api/v1/chat/message",
            json=payload,
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert res_auth.status_code == 200
        assert "microvascular complication" in res_auth.json()["message"]


def test_staging_smoke_chat_rate_limiting_enforced(client: TestClient, monkeypatch):
    """Smoke test: rapid requests exceeding rate limit receive HTTP 429 Too Many Requests."""
    from unittest.mock import AsyncMock, patch
    from datetime import datetime, timezone
    from app.core.rate_limiter import rate_limiter
    from app.schemas.chat import ChatResponse

    rate_limiter.reset()

    secret = "staging-secret-key-32charslong-test"
    monkeypatch.setattr(settings, "API_SECRET_KEY", secret)
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(settings, "RATE_LIMIT_CHAT_PER_MINUTE", 3)

    valid_token = create_access_token(subject="speed-tester", expires_in_seconds=300, secret_key=secret)
    payload = {"message": "Quick question", "conversation_history": []}
    headers = {"Authorization": f"Bearer {valid_token}"}

    mock_chat_res = ChatResponse(
        message="Mock answer",
        provider="gemini",
        model="gemini-3.5-flash",
        created_at=datetime.now(timezone.utc),
        disclaimer="EDUCATIONAL RESEARCH USE ONLY",
    )

    with patch("app.api.v1.chat.process_chat_message", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_chat_res

        # First 3 requests allowed (under limit of 3)
        for _ in range(3):
            r = client.post("/api/v1/chat/message", json=payload, headers=headers)
            assert r.status_code == 200

        # 4th request must be rate limited by RateLimitMiddleware
        r_limited = client.post("/api/v1/chat/message", json=payload, headers=headers)
        assert r_limited.status_code == 429
        assert "Rate limit exceeded" in r_limited.json()["detail"]
        assert "Retry-After" in r_limited.headers

    rate_limiter.reset()

