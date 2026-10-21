"""Pydantic schemas for request and response validation."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Schema for health-check endpoint."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["MedVision AI Backend"])
    version: str = Field(..., examples=["0.1.0-alpha"])
    timestamp: datetime
    environment: str = Field(..., examples=["development"])


class ImageMetadataSchema(BaseModel):
    """Extracted in-memory technical metadata for the uploaded image."""

    file_name: str = Field(..., description="Sanitized original filename")
    file_size_bytes: int = Field(..., description="Image size in bytes")
    mime_type: str = Field(..., description="Detected MIME content type")
    image_width: Optional[int] = Field(None, description="Width in pixels")
    image_height: Optional[int] = Field(None, description="Height in pixels")
    file_hash: str = Field(..., description="In-memory SHA-256 cryptographic digest")


class AnalysisPlaceholderResponse(BaseModel):
    """Honest development placeholder response for medical imaging analysis.

    Notice: 'prediction' and 'explanation' fields are explicitly typed as None
    and marked unavailable until an authentic clinical deep learning pipeline is linked.
    """

    session_id: str = Field(..., description="Anonymous UUID token for this session")
    modality: str = Field(..., description="Imaging modality ('retina' or 'chest_xray')")
    status: str = Field(
        default="DEVELOPMENT_PLACEHOLDER",
        description="Current pipeline state",
    )
    message: str = Field(
        ...,
        description="Explanatory status message clarifying no clinical inference occurred",
    )
    model_version: str = Field(..., description="Development model pipeline identifier")
    metadata: ImageMetadataSchema = Field(..., description="Technical image attributes")
    prediction: Optional[Any] = Field(
        default=None,
        description="Real AI prediction output (Strictly null in placeholder phase)",
    )
    explanation: Optional[Any] = Field(
        default=None,
        description="Explainability heatmap or feature attribution (Strictly null)",
    )
    disclaimer: str = Field(
        default="RESEARCH ONLY: Not for clinical or diagnostic use. Never use placeholder responses for patient decisions.",
        description="Mandatory medical research disclaimer",
    )
    created_at: datetime = Field(..., description="UTC creation timestamp")


class ErrorDetailResponse(BaseModel):
    """Structured error message schema."""

    detail: str = Field(..., description="Human-readable explanation of the validation or processing failure")
