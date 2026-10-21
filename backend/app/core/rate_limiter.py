"""Sliding-window rate limiter with in-memory and Redis distributed backends.

Provides defensive abuse protection and resource exhaustion mitigation:
- High-cost LLM endpoints (MedAssist chat)
- High-compute ML inference endpoints (RetinaGuard & Chest X-Ray)
- General API routes

Architecture:
- Single-instance / Local Demo / Staging: In-memory sliding window using Python deque with thread safety.
- Multi-worker / Multi-container Cluster: Distributed sliding window backed by Redis (sorted sets).
- Resilient Error Handling: If Redis connection fails, gracefully falls back to in-memory sliding window
  (or fails closed if RATE_LIMIT_STRICT_FAIL_CLOSED=True) to prevent unconstrained abuse.
"""

from collections import defaultdict, deque
import logging
import math
import threading
import time
from typing import Dict, List, Optional, Tuple
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger("medvision.rate_limiter")


class SlidingWindowRateLimiter:
    """Thread-safe rate limiter supporting both in-memory and distributed Redis backends."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # In-memory storage: category -> ip -> deque of request timestamps (epoch seconds)
        self._history: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self._redis_client = None
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection if REDIS_URL is configured."""
        redis_url = getattr(settings, "REDIS_URL", None)
        if redis_url and redis_url.strip():
            try:
                import redis
                client = redis.from_url(
                    redis_url.strip(),
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                )
                client.ping()
                self._redis_client = client
                logger.info("Connected to Redis distributed rate limiter at %s", redis_url)
            except Exception as e:
                logger.warning(
                    "Redis rate limiter connection failed (%s). Falling back to in-memory limiter.",
                    e,
                )
                self._redis_client = None
        else:
            self._redis_client = None

    def get_active_backend(self) -> str:
        """Return the active rate limiting backend: 'redis' or 'memory'."""
        return "redis" if self._redis_client is not None else "memory"

    def reset(self) -> None:
        """Clear all rate limiting history (primarily for tests)."""
        with self._lock:
            self._history.clear()
        if self._redis_client:
            try:
                keys = self._redis_client.keys("medvision:ratelimit:*")
                if keys:
                    self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning("Failed to reset Redis rate limit keys: %s", e)

    def get_category_and_limit(self, path: str) -> Tuple[str, int, int]:
        """Determine rate limit category, max requests, and window in seconds for a path."""
        # Inference endpoints: PyTorch GPU/CPU intensive
        if path.startswith("/api/v1/retina/predict") or path.startswith("/api/v1/chest-xray/predict") or \
           path.startswith("/api/v1/retina/analyze") or path.startswith("/api/v1/chest-xray/analyze"):
            return "inference", settings.RATE_LIMIT_INFERENCE_PER_MINUTE, 60

        # Chat message endpoint: external LLM quota & token usage intensive
        if path.startswith("/api/v1/chat/message"):
            return "chat", settings.RATE_LIMIT_CHAT_PER_MINUTE, 60

        # General API endpoints
        return "general", settings.RATE_LIMIT_GENERAL_PER_MINUTE, 60

    def extract_client_ip(self, request: Request) -> str:
        """Extract the effective client IP address, honoring configured trusted proxies."""
        client_host = request.client.host if request.client else "127.0.0.1"

        trusted_proxies = getattr(settings, "TRUSTED_PROXIES", ["127.0.0.1", "::1", "testclient"])

        if client_host in trusted_proxies:
            # Check X-Forwarded-For header
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                # X-Forwarded-For can be a comma-separated list: "client, proxy1, proxy2"
                ips = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
                if ips:
                    return ips[0]

            # Check X-Real-IP
            x_real_ip = request.headers.get("X-Real-IP")
            if x_real_ip and x_real_ip.strip():
                return x_real_ip.strip()

        return client_host

    def _check_memory(
        self,
        client_ip: str,
        category: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int, int]:
        """Check rate limit using in-memory sliding window deque."""
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._history[category][client_ip]

            # Purge timestamps outside the sliding window
            while timestamps and timestamps[0] < window_start:
                timestamps.popleft()

            count = len(timestamps)
            if count >= max_requests:
                # Earliest timestamp in current window determines retry-after
                earliest = timestamps[0]
                retry_after = max(1, math.ceil(earliest + window_seconds - now))
                return False, 0, retry_after, max_requests

            # Record this request
            timestamps.append(now)
            remaining = max(0, max_requests - len(timestamps))
            return True, remaining, 0, max_requests

    def _check_redis(
        self,
        client_ip: str,
        category: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int, int]:
        """Check rate limit across multiple workers using Redis sorted sets."""
        key = f"medvision:ratelimit:{category}:{client_ip}"
        now = time.time()
        clear_before = now - window_seconds

        pipe = self._redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, clear_before)
        pipe.zcard(key)
        pipe.zrange(key, 0, 0, withscores=True)
        results = pipe.execute()

        current_count = results[1]
        earliest_entries = results[2]

        if current_count >= max_requests:
            earliest_time = float(earliest_entries[0][1]) if earliest_entries else now
            retry_after = max(1, math.ceil(earliest_time + window_seconds - now))
            return False, 0, retry_after, max_requests

        # Add current timestamp with unique member ID
        pipe2 = self._redis_client.pipeline()
        member = f"{now}:{uuid.uuid4().hex[:8]}"
        pipe2.zadd(key, {member: now})
        pipe2.expire(key, window_seconds * 2)
        pipe2.execute()

        remaining = max(0, max_requests - (current_count + 1))
        return True, remaining, 0, max_requests

    def check_rate_limit(
        self,
        client_ip: str,
        category: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int, int]:
        """Check and record request against sliding window limit.

        Returns:
            (is_allowed, remaining_requests, retry_after_seconds, max_requests)
        """
        if self._redis_client:
            try:
                return self._check_redis(client_ip, category, max_requests, window_seconds)
            except Exception as exc:
                logger.error(
                    "Redis rate limit check failed (%s). Active policy: %s",
                    exc,
                    "FAIL_CLOSED" if getattr(settings, "RATE_LIMIT_STRICT_FAIL_CLOSED", False) else "FALLBACK_MEMORY",
                )
                if getattr(settings, "RATE_LIMIT_STRICT_FAIL_CLOSED", False):
                    # Fail closed: reject request rather than allowing unlimited traffic
                    return False, 0, 60, max_requests
                # Resilient fallback to thread-safe in-memory sliding window
                return self._check_memory(client_ip, category, max_requests, window_seconds)

        return self._check_memory(client_ip, category, max_requests, window_seconds)


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware to enforce per-IP rate limiting."""

    async def dispatch(self, request: Request, call_next):
        # Skip if rate limiting is globally disabled
        if not getattr(settings, "RATE_LIMIT_ENABLED", True):
            return await call_next(request)

        # Skip non-API paths, static files, docs, health check, and OPTIONS preflight
        path = request.url.path
        if request.method == "OPTIONS" or path == "/api/health" or path == "/" or not path.startswith("/api/"):
            return await call_next(request)

        client_ip = rate_limiter.extract_client_ip(request)
        category, limit, window = rate_limiter.get_category_and_limit(path)

        allowed, remaining, retry_after, max_requests = rate_limiter.check_rate_limit(
            client_ip=client_ip,
            category=category,
            max_requests=limit,
            window_seconds=window,
        )

        if not allowed:
            headers = {
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(retry_after),
            }
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Please retry after {retry_after} seconds."},
                headers=headers,
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(window)
        return response
