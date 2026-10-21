"""API v1 package."""

from .health import router as health_router
from .retina import router as retina_router
from .chest_xray import router as chest_xray_router

__all__ = ["health_router", "retina_router", "chest_xray_router"]
