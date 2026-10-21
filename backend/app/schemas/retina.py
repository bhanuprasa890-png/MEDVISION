"""Schemas specific to retinal imaging analysis."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import AnalysisPlaceholderResponse, ImageMetadataSchema


class RetinaAnalysisResponse(AnalysisPlaceholderResponse):
    """Retinal fundus image analysis response model (Development Placeholder)."""

    pass


class RetinaClassScore(BaseModel):
    """Score breakdown for a specific DR severity class."""

    class_id: int = Field(..., description="Class integer ID (0 to 4)")
    class_name: str = Field(..., description="Clinical diagnostic category")
    score: float = Field(..., description="Uncalibrated softmax model score in [0.0, 1.0]")


class RetinaPredictionDetail(BaseModel):
    """Detailed model prediction for diabetic retinopathy grading."""

    predicted_class: int = Field(..., ge=0, le=4, description="Predicted class index (0-4)")
    class_label: str = Field(..., description="Dataset diagnosis name")
    severity_level: str = Field(..., description="Clinical DR severity grade")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw softmax activation score for the top predicted class",
    )
    calibration_notice: str = Field(
        default="Model scores represent uncalibrated softmax outputs and are not calibrated clinical probabilities.",
        description="Scientific qualification of confidence metric",
    )
    all_class_scores: Dict[str, float] = Field(
        ...,
        description="Uncalibrated softmax score distribution across all 5 classes",
    )
    clinical_description: str = Field(..., description="Clinical guidance on grading category")


class SalientRegionSummary(BaseModel):
    """Technical summary of peak attention in Grad-CAM attribution."""

    peak_y: int = Field(..., description="Y-coordinate (pixel) of maximum activation")
    peak_x: int = Field(..., description="X-coordinate (pixel) of maximum activation")
    peak_intensity: float = Field(..., description="Normalized peak heatmap intensity (1.0 max)")
    mean_intensity: float = Field(..., description="Mean normalized intensity across image")
    active_area_ratio: float = Field(..., description="Fraction of image with intensity > 0.5")


class RetinaGradCAMExplanation(BaseModel):
    """Grad-CAM visual interpretability payload."""

    target_class: int = Field(..., description="Class integer explained by Grad-CAM")
    target_class_label: str = Field(..., description="Class name explained")
    logit_score: float = Field(..., description="Raw logit score before softmax")
    target_layer: str = Field(default="layer4", description="Convolutional layer hooked")
    resolution: List[int] = Field(default=[224, 224], description="Heatmap resolution [H, W]")
    heatmap_overlay_base64: str = Field(
        ...,
        description="Base64-encoded PNG data URI of fundus image with blended Jet heatmap",
    )
    raw_heatmap_base64: str = Field(
        ...,
        description="Base64-encoded PNG data URI of colorized Jet heatmap",
    )
    salient_region_summary: SalientRegionSummary = Field(
        ...,
        description="Coordinates and metrics of peak attention regions",
    )
    interpretability_note: str = Field(
        ...,
        description="Medical qualification explaining that heatmaps indicate model attention, not confirmed pathology",
    )


class RetinaPredictResponse(BaseModel):
    """Complete prediction and visual explainability response schema."""

    session_id: str = Field(..., description="Anonymous UUID token for this session")
    modality: str = Field(default="retina", description="Imaging modality")
    status: str = Field(default="SUCCESS", description="Pipeline execution state")
    model_version: str = Field(..., description="Model architecture and version")
    metadata: ImageMetadataSchema = Field(..., description="In-memory image attributes")
    prediction: RetinaPredictionDetail = Field(..., description="AI prediction and score breakdown")
    explanation: Optional[RetinaGradCAMExplanation] = Field(
        default=None,
        description="Grad-CAM visual heatmap overlay and attention summary",
    )
    disclaimer: str = Field(
        default=(
            "RESEARCH PROTOTYPE ONLY: This system is an experimental AI research model for "
            "investigating diabetic retinopathy patterns. It is NOT certified as a medical device "
            "and MUST NOT be used for real patient diagnosis or clinical decision-making."
        ),
        description="Mandatory medical research disclaimer",
    )
    created_at: datetime = Field(..., description="UTC creation timestamp")


class RetinaModelStatusResponse(BaseModel):
    """Readiness and model health check schema."""

    status: str = Field(..., description="Service status ('ready' or 'unloaded')")
    is_loaded: bool = Field(..., description="Whether model weights are loaded in memory")
    model_version: str = Field(..., description="Model version string")
    checkpoint_path: Optional[str] = Field(None, description="Path to loaded .pt checkpoint")
    checkpoint_filename: Optional[str] = Field(None, description="Actual loaded checkpoint filename (e.g. retinaguard_v2.pt)")
    checkpoint_epoch: Optional[int] = Field(None, description="Training epoch recorded in the loaded checkpoint metadata")
    checkpoint_val_macro_f1: Optional[float] = Field(None, description="Validation Macro F1 metric recorded in checkpoint metadata")
    selection_source: Optional[str] = Field(None, description="Checkpoint selection mechanism ('v2_preferred', 'baseline_fallback', 'override')")
    device: str = Field(..., description="Execution device ('cpu' or 'cuda')")
    num_classes: int = Field(default=5, description="Number of output classes")
    classes: Dict[str, str] = Field(..., description="Mapping of class IDs to clinical diagnoses")
    gradcam_supported: bool = Field(default=True, description="Whether Grad-CAM visual heatmaps are supported")
    status_message: Optional[str] = Field(None, description="Diagnostic status message or readiness explanation")
