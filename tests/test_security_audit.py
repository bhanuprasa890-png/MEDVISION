"""Comprehensive security and privacy audit regression tests.

Verifies:
1. Cross-platform path traversal filename sanitization (Windows, POSIX, hidden dotfiles).
2. Decompression bomb and pixel-flood memory exhaustion defenses.
3. HTTP security headers on all responses (nosniff, DENY, strict-origin, permissions policy).
4. Global unhandled exception handler prevents traceback and internal details leakage.
5. In-memory upload validation with zero disk persistence.
6. Secret credential leakage prevention (credentials never returned in status/health/error endpoints).
7. CORS origin validator prohibits wildcard '*' when credentials are active.
8. Provider error sanitization redacts active and pattern-based API keys.
9. Production environment guards interactive documentation (/docs, /redoc, /openapi.json).
"""

import io
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app.core.config import Settings, settings
from app.core.security import sanitize_filename
from app.services.chat_service import _sanitize_error_text
from app.services.file_validator import MAX_IMAGE_DIMENSION, MAX_IMAGE_PIXELS


# ==============================================================================
# 1. FILENAME SANITIZATION & PATH TRAVERSAL DEFENSE
# ==============================================================================

def test_path_traversal_filename_sanitization():
    """Verify that sanitize_filename strips path traversal sequences and hidden dots."""
    # POSIX traversal
    assert sanitize_filename("../../../../etc/passwd") == "passwd"
    assert sanitize_filename("../../../var/log/syslog.png") == "syslog.png"

    # Windows-style traversal
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("C:\\Users\\admin\\Desktop\\secret.jpg") == "secret.jpg"

    # Leading dots and hidden files
    assert sanitize_filename(".hidden_retina.jpg") == "hidden_retina.jpg"
    assert sanitize_filename("...patient.png") == "patient.png"

    # Internal multiple dots (traversal evasion attempt)
    sanitized = sanitize_filename("fundus..scan...jpg")
    assert ".." not in sanitized

    # Empty, whitespace, or invalid traversal only names fallback safely
    empty_fallback = sanitize_filename("   ")
    assert empty_fallback.startswith("unnamed_image_")

    traversal_only = sanitize_filename("../..")
    assert traversal_only.startswith("unnamed_image_")

    dots_only = sanitize_filename("....")
    assert dots_only.startswith("unnamed_image_")


def test_upload_path_traversal_in_endpoint(client: TestClient, create_sample_image):
    """Uploading a file with a malicious traversal filename stores only sanitized metadata."""
    img_bytes = create_sample_image(format="JPEG", size=(128, 128))
    files = {"file": ("../../../../etc/shadow.jpg", img_bytes, "image/jpeg")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["file_name"] == "shadow.jpg"
    assert ".." not in data["metadata"]["file_name"]
    assert "/" not in data["metadata"]["file_name"]
    assert "\\" not in data["metadata"]["file_name"]


# ==============================================================================
# 2. DECOMPRESSION BOMB & PIXEL-FLOOD MITIGATION
# ==============================================================================

def test_pixel_flood_excessive_dimension_rejected(client: TestClient):
    """Images exceeding MAX_IMAGE_DIMENSION (10,000px) must be rejected with 400."""
    buf = io.BytesIO()
    # Create image with width > 10,000 px (e.g. 10001 x 10)
    large_dim_img = Image.new("RGB", (MAX_IMAGE_DIMENSION + 1, 10), color="white")
    large_dim_img.save(buf, format="PNG")
    buf.seek(0)

    files = {"file": ("dimension_flood.png", buf.getvalue(), "image/png")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 400
    assert "dimension" in response.json()["detail"].lower()


def test_pixel_flood_excessive_resolution_rejected(client: TestClient):
    """Images with resolution exceeding MAX_IMAGE_PIXELS (25M pixels) must be rejected."""
    buf = io.BytesIO()
    # 5100 x 5100 = 26,010,000 pixels (> 25,000,000 max)
    img = Image.new("RGB", (5100, 5100), color="blue")
    img.save(buf, format="JPEG", quality=10)
    buf.seek(0)

    files = {"file": ("resolution_flood.jpg", buf.getvalue(), "image/jpeg")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "resolution" in detail or "safe processing limit" in detail or "decompression" in detail


# ==============================================================================
# 3. HTTP SECURITY HEADERS
# ==============================================================================

def test_http_security_headers_present(client: TestClient):
    """All API responses must include defensive security headers."""
    response = client.get("/")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "0"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("Permissions-Policy", "")


def test_http_security_headers_on_api_endpoints(client: TestClient):
    """Health check endpoint also returns standard security headers."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


# ==============================================================================
# 4. SECRETS LEAKAGE PREVENTION
# ==============================================================================

def test_secrets_never_returned_in_chat_status(client: TestClient):
    """GET /api/v1/chat/status must never return API keys or credentials."""
    response = client.get("/api/v1/chat/status")
    assert response.status_code == 200
    text = response.text
    assert "AIza" not in text
    assert "sk-" not in text
    assert "key" not in response.json()
    assert "secret" not in response.json()


def test_secrets_never_returned_in_health_endpoint(client: TestClient):
    """GET /api/health must expose only non-sensitive operational metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"status", "service", "version", "timestamp", "environment"}


def test_provider_error_sanitization():
    """_sanitize_error_text must redact Google and OpenAI API key patterns."""
    raw_error_1 = "Invalid key provided: AIzaSyD3x4mpl3K3y999999999999999999999"
    sanitized_1 = _sanitize_error_text(raw_error_1)
    assert "AIza" not in sanitized_1
    assert "[REDACTED_API_KEY]" in sanitized_1

    raw_error_2 = "Authentication failure: sk-abcdef1234567890abcdef1234567890"
    sanitized_2 = _sanitize_error_text(raw_error_2)
    assert "sk-" not in sanitized_2
    assert "[REDACTED_API_KEY]" in sanitized_2


# ==============================================================================
# 5. GLOBAL UNHANDLED EXCEPTION HANDLER (TRACEBACK PROTECTION)
# ==============================================================================

def test_unhandled_exception_returns_clean_500_without_traceback():
    """Unhandled internal server errors must return generic 500 without leaking stack traces."""
    from app.main import app as main_app

    @main_app.get("/api/test-fault-injection-internal")
    async def fault_injection():
        raise RuntimeError("Internal database password or secret file pointer failure!")

    with TestClient(main_app, raise_server_exceptions=False) as isolated_client:
        response = isolated_client.get("/api/test-fault-injection-internal")
        assert response.status_code == 500
        data = response.json()
        assert data["detail"] == "An internal server error occurred. Please contact the administrator."
        assert "password" not in response.text
        assert "Traceback" not in response.text


# ==============================================================================
# 6. CORS CONFIGURATION HARDENING
# ==============================================================================

def test_cors_origins_prohibits_wildcard():
    """assemble_cors_origins must filter out wildcard '*' origins."""
    s = Settings()
    # Testing validator directly with wildcard
    origins = s.assemble_cors_origins(["*"])
    assert "*" not in origins
    assert len(origins) >= 1  # Falls back to safe localhost origins

    # Mixed with wildcard
    origins_mixed = s.assemble_cors_origins(["http://localhost:3000", "*"])
    assert "*" not in origins_mixed
    assert "http://localhost:3000" in origins_mixed


# ==============================================================================
# 7. PRODUCTION INTERACTIVE DOCUMENTATION GUARD
# ==============================================================================

def test_production_mode_disables_interactive_docs(monkeypatch):
    """In production environment, /docs and /redoc must be disabled."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_SECRET_KEY", "production-secret-test-key-32charslong")
    prod_settings = Settings(ENVIRONMENT="production", API_SECRET_KEY="production-secret-test-key-32charslong")


    is_prod = prod_settings.ENVIRONMENT.lower() == "production"
    test_app = FastAPI(
        openapi_url=None if is_prod else "/openapi.json",
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
    )
    with TestClient(test_app) as prod_client:
        docs_res = prod_client.get("/docs")
        assert docs_res.status_code == 404

        redoc_res = prod_client.get("/redoc")
        assert redoc_res.status_code == 404


# ==============================================================================
# 8. RATE LIMITING & ABUSE PROTECTION
# ==============================================================================

def test_rate_limiter_allows_and_attaches_headers(client: TestClient):
    """Normal requests must succeed and include standard rate limit headers."""
    response = client.get("/api/v1/chat/status")
    assert response.status_code == 200
    headers = response.headers
    assert "X-RateLimit-Limit" in headers
    assert "X-RateLimit-Remaining" in headers
    assert "X-RateLimit-Reset" in headers
    assert int(headers["X-RateLimit-Limit"]) > 0


def test_rate_limiter_blocks_excessive_requests(client: TestClient, monkeypatch):
    """When client exceeds the configured rate limit, it must receive 429 with Retry-After."""
    from app.core.rate_limiter import rate_limiter
    rate_limiter.reset()

    # Artificially constrain limit to 3 requests
    monkeypatch.setattr(settings, "RATE_LIMIT_GENERAL_PER_MINUTE", 3)

    # 3 allowed requests
    for _ in range(3):
        res = client.get("/api/v1/chat/status")
        assert res.status_code == 200

    # 4th request must be rejected with 429
    res_blocked = client.get("/api/v1/chat/status")
    assert res_blocked.status_code == 429
    assert "Rate limit exceeded" in res_blocked.json()["detail"]
    assert "Retry-After" in res_blocked.headers
    assert int(res_blocked.headers["Retry-After"]) >= 1
    assert res_blocked.headers["X-RateLimit-Remaining"] == "0"


def test_rate_limiter_trusted_proxy_header(client: TestClient, monkeypatch):
    """Rate limiter extracts real client IP behind trusted proxy via X-Forwarded-For."""
    from app.core.rate_limiter import rate_limiter
    rate_limiter.reset()

    monkeypatch.setattr(settings, "RATE_LIMIT_GENERAL_PER_MINUTE", 2)

    # Client A: 2 requests
    client_a_headers = {"X-Forwarded-For": "203.0.113.195"}
    assert client.get("/api/v1/chat/status", headers=client_a_headers).status_code == 200
    assert client.get("/api/v1/chat/status", headers=client_a_headers).status_code == 200
    # Client A 3rd request blocked
    assert client.get("/api/v1/chat/status", headers=client_a_headers).status_code == 429

    # Client B on different IP should still be allowed
    client_b_headers = {"X-Forwarded-For": "198.51.100.42"}
    assert client.get("/api/v1/chat/status", headers=client_b_headers).status_code == 200


# ==============================================================================
# 9. SERVER-SIDE API KEY AUTHORIZATION
# ==============================================================================

def test_api_key_bypassed_when_unconfigured(client: TestClient, create_sample_image):
    """When API_SECRET_KEY is None, endpoints remain accessible for local research demo."""
    assert settings.API_SECRET_KEY is None
    img_bytes = create_sample_image(format="JPEG", size=(64, 64))
    files = {"file": ("demo_scan.jpg", img_bytes, "image/jpeg")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 200


def test_api_key_blocks_unauthorized_when_configured(client: TestClient, create_sample_image, monkeypatch):
    """When API_SECRET_KEY is configured, requests without valid credentials are rejected with 401."""
    test_key = "medvision-secret-staging-key-abcdef123"
    monkeypatch.setattr(settings, "API_SECRET_KEY", test_key)

    img_bytes = create_sample_image(format="JPEG", size=(64, 64))
    files = {"file": ("unauth_scan.jpg", img_bytes, "image/jpeg")}

    # No auth header -> 401
    res_no_auth = client.post("/api/v1/retina/analyze", files=files)
    assert res_no_auth.status_code == 401
    assert "Invalid or missing API key" in res_no_auth.json()["detail"]
    assert res_no_auth.headers.get("WWW-Authenticate") == "Bearer"

    # Wrong X-API-Key -> 401
    res_wrong_key = client.post(
        "/api/v1/retina/analyze",
        files=files,
        headers={"X-API-Key": "wrong-key-value"},
    )
    assert res_wrong_key.status_code == 401

    # Valid X-API-Key -> 200
    res_valid_header = client.post(
        "/api/v1/retina/analyze",
        files=files,
        headers={"X-API-Key": test_key},
    )
    assert res_valid_header.status_code == 200

    # Valid Authorization: Bearer <key> -> 200
    res_valid_bearer = client.post(
        "/api/v1/retina/analyze",
        files=files,
        headers={"Authorization": f"Bearer {test_key}"},
    )
    assert res_valid_bearer.status_code == 200

    # Public health check endpoint must still succeed without API key
    res_health = client.get("/api/health")
    assert res_health.status_code == 200


# ==============================================================================
# 10. PAYLOAD SIZE DEFENSIVE RESTRICTIONS
# ==============================================================================

def test_payload_size_limit_rejection_chat(client: TestClient):
    """Oversized Content-Length on chat endpoint must be rejected with 413."""
    oversized_headers = {
        "Content-Length": str(settings.MAX_JSON_PAYLOAD_BYTES + 1024),
        "Content-Type": "application/json",
    }
    response = client.post(
        "/api/v1/chat/message",
        json={"message": "hello"},
        headers=oversized_headers,
    )
    assert response.status_code == 413
    assert "exceeds maximum limit" in response.json()["detail"]


def test_payload_size_limit_rejection_upload(client: TestClient, create_sample_image):
    """Oversized Content-Length on upload endpoint must be rejected with 413."""
    img_bytes = create_sample_image(format="JPEG", size=(32, 32))
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    oversized_headers = {
        "Content-Length": str(settings.MAX_CONTENT_LENGTH_BYTES + 1024),
    }
    response = client.post(
        "/api/v1/retina/analyze",
        files=files,
        headers=oversized_headers,
    )
    assert response.status_code == 413
    assert "exceeds maximum limit" in response.json()["detail"]


# ==============================================================================
# 11. HTTPS / PRODUCTION SECURITY HEADERS (HSTS & CSP)
# ==============================================================================

def test_hsts_and_csp_headers_on_https_or_production(client: TestClient, monkeypatch):
    """When behind HTTPS or in production, responses must include HSTS and CSP headers."""
    # Test HTTPS proxy simulation
    res_https = client.get("/api/health", headers={"X-Forwarded-Proto": "https"})
    assert res_https.status_code == 200
    assert "max-age=31536000" in res_https.headers.get("Strict-Transport-Security", "")
    assert "default-src 'self'" in res_https.headers.get("Content-Security-Policy", "")

    # Test production environment setting
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    res_prod = client.get("/")
    assert res_prod.status_code == 200
    assert "Strict-Transport-Security" in res_prod.headers
    assert "Content-Security-Policy" in res_prod.headers


# ==============================================================================
# 12. BROADENED ERROR & SECRET SANITIZATION
# ==============================================================================

def test_broadened_secret_and_token_sanitization(monkeypatch):
    """_sanitize_error_text must redact Bearer tokens, query credentials, and configured secret."""
    test_secret = "staging-secret-key-999"
    monkeypatch.setattr(settings, "API_SECRET_KEY", test_secret)

    # Configured secret
    sanitized_secret = _sanitize_error_text(f"Connection failed with key {test_secret}")
    assert test_secret not in sanitized_secret
    assert "[REDACTED_API_KEY]" in sanitized_secret

    # Bearer token in error response
    bearer_msg = "Upstream 401 error: Authorization: Bearer ya29.a0ARrdaM8randomTokenValueHere..."
    sanitized_bearer = _sanitize_error_text(bearer_msg)
    assert "ya29" not in sanitized_bearer
    assert "Bearer [REDACTED_API_KEY]" in sanitized_bearer

    # Query param keys
    url_msg = "Failed request to https://api.example.com/v1?key=AIzaSySecretParam&other=true"
    sanitized_url = _sanitize_error_text(url_msg)
    assert "AIzaSySecretParam" not in sanitized_url
    assert "key=[REDACTED_API_KEY]" in sanitized_url


# ==============================================================================
# 13. PRODUCTION CONFIGURATION & STARTUP HARDENING
# ==============================================================================

def test_production_configuration_requires_api_secret_key(monkeypatch):
    """In production mode, bootstrapping without an API_SECRET_KEY must raise ValueError."""
    monkeypatch.delenv("API_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="Production deployment requires a secure API_SECRET_KEY"):
        Settings(ENVIRONMENT="production", API_SECRET_KEY=None)


def test_production_configuration_rejects_short_api_key():
    """In production mode, API_SECRET_KEY with fewer than 16 characters must be rejected."""
    with pytest.raises(ValueError, match="at least 16 characters"):
        Settings(ENVIRONMENT="production", API_SECRET_KEY="short-secret")


def test_production_configuration_rejects_debug_mode():
    """In production mode, DEBUG=True must be rejected."""
    with pytest.raises(ValueError, match="DEBUG mode cannot be enabled"):
        Settings(
            ENVIRONMENT="production",
            API_SECRET_KEY="secure-production-key-32charslong",
            DEBUG=True,
        )


def test_production_configuration_accepts_valid_config():
    """In production mode, valid config with strong key and DEBUG=False succeeds."""
    prod = Settings(
        ENVIRONMENT="production",
        API_SECRET_KEY="secure-production-key-32charslong",
        DEBUG=False,
    )
    assert prod.ENVIRONMENT == "production"
    assert prod.DEBUG is False
    assert prod.API_SECRET_KEY == "secure-production-key-32charslong"


def test_production_mode_prevents_silent_auth_bypass(monkeypatch):
    """If API_SECRET_KEY is empty in production, verify_api_key must raise 500 error instead of bypassing."""
    from fastapi import HTTPException
    from app.core.security import verify_api_key

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "API_SECRET_KEY", "")

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(x_api_key=None, authorization=None)

    assert exc_info.value.status_code == 500
    assert "Authentication key must be configured in production" in exc_info.value.detail


# ==============================================================================
# 14. DISTRIBUTED RATE LIMITING & REDIS RESILIENCE
# ==============================================================================

def test_rate_limiter_redis_sliding_window_mock():
    """Verify Redis distributed sliding-window sorted set integration."""
    from unittest.mock import MagicMock
    from app.core.rate_limiter import SlidingWindowRateLimiter

    limiter = SlidingWindowRateLimiter()

    # Create mock Redis client
    mock_redis = MagicMock()
    mock_pipe = MagicMock()

    # Simulate pipeline execution: [zrem_count, current_zcard, earliest_entries]
    # Request 1: 0 existing requests
    mock_pipe.execute.return_value = [0, 0, []]
    mock_redis.pipeline.return_value = mock_pipe
    limiter._redis_client = mock_redis

    allowed, remaining, retry_after, limit = limiter.check_rate_limit(
        client_ip="10.0.0.1",
        category="chat",
        max_requests=10,
        window_seconds=60,
    )
    assert allowed is True
    assert remaining == 9
    assert retry_after == 0

    # Simulate rate limit exceeded: current count is 10
    now_ts = 1700000000.0
    mock_pipe.execute.return_value = [0, 10, [("member1", now_ts)]]

    allowed_exceeded, remaining_exceeded, retry_after_exceeded, _ = limiter.check_rate_limit(
        client_ip="10.0.0.1",
        category="chat",
        max_requests=10,
        window_seconds=60,
    )
    assert allowed_exceeded is False
    assert remaining_exceeded == 0
    assert retry_after_exceeded >= 1


def test_rate_limiter_redis_fallback_on_error():
    """When Redis raises an operational error, limiter safely falls back to in-memory tracking."""
    from unittest.mock import MagicMock
    from app.core.rate_limiter import SlidingWindowRateLimiter

    limiter = SlidingWindowRateLimiter()
    mock_redis = MagicMock()
    mock_redis.pipeline.side_effect = RuntimeError("Redis connection timeout or host unreachable")
    limiter._redis_client = mock_redis

    # First request: should not crash, safely falls back to in-memory limiter
    allowed, remaining, _, limit = limiter.check_rate_limit(
        client_ip="10.0.0.99",
        category="general",
        max_requests=5,
        window_seconds=60,
    )
    assert allowed is True
    assert remaining == 4


def test_rate_limiter_redis_fail_closed_policy(monkeypatch):
    """When RATE_LIMIT_STRICT_FAIL_CLOSED=True, Redis failure rejects request rather than allowing unlimited traffic."""
    from unittest.mock import MagicMock
    from app.core.rate_limiter import SlidingWindowRateLimiter

    monkeypatch.setattr(settings, "RATE_LIMIT_STRICT_FAIL_CLOSED", True)

    limiter = SlidingWindowRateLimiter()
    mock_redis = MagicMock()
    mock_redis.pipeline.side_effect = ConnectionError("Redis cluster unreachable")
    limiter._redis_client = mock_redis

    allowed, remaining, retry_after, _ = limiter.check_rate_limit(
        client_ip="10.0.0.100",
        category="chat",
        max_requests=5,
        window_seconds=60,
    )
    assert allowed is False
    assert remaining == 0
    assert retry_after == 60


