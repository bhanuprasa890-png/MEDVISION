import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, Optional, Union
import uuid

from fastapi import Header, HTTPException, status

from app.core.config import settings


def generate_session_id() -> str:
    """Generate an anonymous, secure UUID v4 string for tracking research sessions."""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent directory traversal and injection.

    - Normalizes path separators (both Windows '\\' and POSIX '/')
    - Strips path prefixes and traversal patterns (e.g., '../', '..\\')
    - Strips leading dots, spaces, and hidden file prefixes
    - Replaces unsafe characters with underscores
    - Collapses directory traversal leftover sequences
    - Truncates name length to a reasonable maximum
    """
    if not filename:
        return f"unnamed_image_{uuid.uuid4().hex[:8]}"

    # Normalize backslashes to forward slashes to handle cross-platform uploads
    normalized = filename.replace("\\", "/")
    # Extract base filename ignoring any directory paths
    base_name = normalized.split("/")[-1].strip()

    # Strip leading dots or whitespace to avoid hidden files or '..'
    base_name = base_name.lstrip(". ")

    # Replace all non-alphanumeric (except dot, underscore, hyphen) with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)

    # Collapse multiple consecutive dots or traversal patterns
    sanitized = re.sub(r"\.{2,}", "_", sanitized)

    # Strip trailing dots or spaces
    sanitized = sanitized.strip(". ")

    # Ensure non-empty and not only underscores/hyphens after stripping
    if not sanitized or sanitized.replace("_", "").replace("-", "") == "":
        return f"unnamed_image_{uuid.uuid4().hex[:8]}"

    # Ensure max length while preserving extension
    if len(sanitized) > 120:
        name_part, ext = os.path.splitext(sanitized)
        sanitized = name_part[: 120 - len(ext)] + ext

    return sanitized


def calculate_sha256(data: bytes) -> str:
    """Compute cryptographic SHA-256 digest of binary payload.

    Provides an audit trace and enables deduplication without saving raw image files.
    """
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


TOKEN_DEFAULT_EXPIRY_SECONDS = 3600  # 1 hour


def _b64encode_str(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode_str(s: str) -> bytes:
    """Decode URL-safe base64 string with restored padding."""
    rem = len(s) % 4
    if rem:
        s += "=" * (4 - rem)
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def create_access_token(
    subject: str,
    expires_in_seconds: int = TOKEN_DEFAULT_EXPIRY_SECONDS,
    secret_key: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate an HMAC-SHA256 signed bearer access token with expiration timestamp.

    Format: header.payload.signature (compact, URL-safe base64).
    """
    secret = (secret_key or settings.API_SECRET_KEY or "").strip()
    if not secret:
        raise ValueError("Cannot create access token without a configured API_SECRET_KEY.")

    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_in_seconds,
        "iss": "medvision-auth-gateway",
    }
    if extra_claims:
        payload.update(extra_claims)

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    header_b64 = _b64encode_str(header_bytes)
    payload_b64 = _b64encode_str(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64encode_str(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_access_token(
    token: str,
    secret_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify an HMAC-SHA256 signed bearer token, enforcing signature and expiration.

    Returns the decoded payload dict if valid.
    Raises HTTPException(401) if invalid, expired, or malformed.
    """
    secret = (secret_key or settings.API_SECRET_KEY or "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Authentication key must be configured.",
        )

    parts = token.strip().split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed authentication token.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = _b64encode_str(expected_sig)

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )

    try:
        payload_bytes = _b64decode_str(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Corrupted token payload.",
            headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
        )

    # Validate expiration
    exp = payload.get("exp")
    if exp is not None:
        try:
            exp_ts = float(exp)
            if time.time() > exp_ts:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has expired.",
                    headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token has expired"'},
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token expiration format.",
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )

    return payload


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> bool:
    """Validate server-side API authorization key or signed bearer session token.

    If settings.API_SECRET_KEY is not set or empty:
    - In local development mode: authentication is bypassed for local research.
    - In production or staging mode: raises HTTP 500 configuration error (prevents silent bypass).

    If settings.API_SECRET_KEY is configured:
    - Signed bearer tokens (3 dot-separated segments) are validated cryptographically with expiration checks.
    - Static API secret keys (via 'X-API-Key' or 'Authorization: Bearer <key>') are compared in constant time.
    """
    secret = settings.API_SECRET_KEY
    env_lower = settings.ENVIRONMENT.lower()
    is_protected_env = env_lower in ("production", "staging")

    if not secret or not secret.strip():
        if is_protected_env:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Server configuration error: Authentication key must be configured in {env_lower} mode.",
            )
        # Authentication not enforced (local development mode)
        return True

    expected_secret = secret.strip()
    provided_key: Optional[str] = None
    is_bearer_token = False

    if x_api_key and x_api_key.strip():
        provided_key = x_api_key.strip()
    elif authorization and authorization.strip():
        auth_val = authorization.strip()
        if auth_val.lower().startswith("bearer "):
            provided_key = auth_val[7:].strip()
            is_bearer_token = True
        else:
            provided_key = auth_val

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If the client provided a compact signed token (header.payload.signature)
    if is_bearer_token and provided_key.count(".") == 2:
        # verify_access_token will raise HTTP 401 if expired or signature is invalid
        verify_access_token(provided_key, secret_key=expected_secret)
        return True

    # Otherwise validate as a static shared API key
    if not hmac.compare_digest(provided_key, expected_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return True


def harden_file_permissions(filepath: Union[str, Path]) -> None:
    """Restrict file permissions to owner read/write (0o600) on POSIX platforms."""
    if os.name != "nt":
        try:
            p = Path(filepath)
            if p.exists():
                os.chmod(p, 0o600)
        except Exception:
            pass

