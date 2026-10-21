"""Health check endpoint router."""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.common import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Returns the operating status, service identity, and current timestamp.",
)
async def get_health() -> HealthCheckResponse:
    """Check health status of backend service."""
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc),
        environment=settings.ENVIRONMENT,
    )
