"""Main entry point for MedVision AI FastAPI application."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import settings
from app.core.rate_limiter import RateLimitMiddleware
from app.core.security import harden_file_permissions
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger("medvision.main")

is_production = settings.ENVIRONMENT.lower() == "production"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: sets up DB tables on startup and cleans up on shutdown."""
    # Ensure database tables exist upon application startup
    Base.metadata.create_all(bind=engine)
    if settings.DATABASE_URL.startswith("sqlite:///") and not settings.DATABASE_URL.startswith("sqlite:///:memory:"):
        db_path = settings.DATABASE_URL[len("sqlite:///"):]
        harden_file_permissions(db_path)
    yield
    # Graceful shutdown: release database connection pool resources
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Research assistant backend for explainable medical imaging. "
        "Strictly separated architecture with in-memory validation, "
        "anonymous audit session persistence, and honest pipeline placeholders."
    ),
    openapi_url=None if is_production else f"{settings.API_V1_STR}/openapi.json",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce standard HTTP security headers on all responses, plus HSTS and CSP in production."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

    # Enforce HSTS and strict CSP for HTTPS, production, and staging environments
    is_protected_env = settings.ENVIRONMENT.lower() in ("production", "staging")
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    if is_protected_env or is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

    return response


@app.middleware("http")
async def enforce_payload_size_limits(request: Request, call_next):
    """Early defensive check on Content-Length to prevent memory exhaustion DoS."""
    content_length_str = request.headers.get("content-length")
    if content_length_str:
        try:
            content_length = int(content_length_str)
            path = request.url.path
            max_bytes = None
            if path.startswith(f"{settings.API_V1_STR}/chat/"):
                max_bytes = settings.MAX_JSON_PAYLOAD_BYTES
            elif path.startswith(f"{settings.API_V1_STR}/retina/") or path.startswith(f"{settings.API_V1_STR}/chest-xray/"):
                max_bytes = settings.MAX_CONTENT_LENGTH_BYTES

            if max_bytes is not None and content_length > max_bytes:
                return JSONResponse(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    content={"detail": f"Request payload ({content_length} bytes) exceeds maximum limit of {max_bytes} bytes."},
                )

        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid Content-Length header."},
            )
    return await call_next(request)


# Enforce per-client-IP sliding-window rate limiting
app.add_middleware(RateLimitMiddleware)

# Strict CORS: Only allow explicit local frontend origin
# Prohibit wildcard '*' origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Register routes
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalize FastAPI validation errors into human-readable strings matching ErrorDetailResponse."""
    error_messages = []
    for err in exc.errors():
        loc_parts = [str(l) for l in err.get("loc", []) if l != "body"]
        loc = " -> ".join(loc_parts)
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{loc}: {msg}" if loc else msg)
    detail_str = "; ".join(error_messages) or "Validation error"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": detail_str},
    )


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    """Catch unhandled server errors and return a safe, generic 500 error without leaking stack traces."""
    logger.error(
        "Unhandled server error on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


@app.get("/", tags=["Root"])
async def root():
    """Root landing endpoint pointing researchers to documentation and health check."""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": None if is_production else "/docs",
        "health_check": "/api/health",
        "disclaimer": "RESEARCH USE ONLY: Not for clinical or diagnostic use.",
    }
