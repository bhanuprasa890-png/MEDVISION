"""API Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.retina import router as retina_router
from app.api.v1.chest_xray import router as chest_xray_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()

# Global health check under /api/health
api_router.include_router(health_router, prefix="/api")

# Modality & assistant routes under /api/v1/...
api_router.include_router(retina_router, prefix="/api/v1")
api_router.include_router(chest_xray_router, prefix="/api/v1")
api_router.include_router(chat_router, prefix="/api/v1")

# Route alias under /api/... (supports /api/retina/predict)
api_router.include_router(retina_router, prefix="/api", include_in_schema=False)
