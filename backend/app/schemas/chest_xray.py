"""Schemas specific to chest radiography (CXR) analysis and model inference."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.common import AnalysisPlaceholderResponse, ImageMetadataSchema


class ChestXrayAnalysisResponse(AnalysisPlaceholderResponse):
    """Chest X-Ray analysis response model (Development Placeholder for /analyze)."""

    pass


class ChestXrayPathologyScore(BaseModel):
    """Score and threshold detection status for a specific thoracic finding."""

    name: str = Field(..., description="Pathology finding name (e.g. 'Pneumonia', 'Cardiomegaly')")
    score: float = Field(..., ge=0.0, le=1.0, description="Uncalibrated sigmoid output score")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Calibrated operating decision threshold")
    detected: bool = Field(..., description="Whether model score exceeds the operating threshold")


class ChestXrayPredictionDetail(BaseModel):
    """Detailed model prediction for multi-label chest radiograph analysis."""

    top_finding: str = Field(..., description="Highest-scoring predicted thoracic finding")
    top_score: float = Field(..., ge=0.0, le=1.0, description="Sigmoid score for top predicted finding")
    findings: Dict[str, float] = Field(
        ...,
        description="Sigmoid score distribution across all 18 evaluated thoracic pathologies",
    )
    findings_above_threshold: List[ChestXrayPathologyScore] = Field(
        default_factory=list,
        description="Thoracic findings whose model score exceeds their calibrated operating threshold",
    )
    all_class_scores: Dict[str, float] = Field(
        ...,
        description="Uncalibrated score distribution (alias for findings)",
    )
    calibration_notice: str = Field(
        default=(
            "Model scores represent uncalibrated sigmoid output activations from a research prototype "
            "and are not calibrated clinical probabilities or diagnostic directives."
        ),
        description="Scientific qualification of confidence metric",
    )
    clinical_description: str = Field(
        ...,
        description="Clinical educational context regarding the top predicted thoracic finding",
    )


class ChestXraySalientRegionSummary(BaseModel):
    """Technical summary of peak attention in Grad-CAM attribution."""

    peak_y: int = Field(..., description="Y-coordinate (pixel) of maximum activation")
    peak_x: int = Field(..., description="X-coordinate (pixel) of maximum activation")
    peak_intensity: float = Field(..., description="Normalized peak heatmap intensity (1.0 max)")
    mean_intensity: float = Field(..., description="Mean normalized intensity across image")
    active_area_ratio: float = Field(..., description="Fraction of image with intensity > 0.5")


class ChestXrayGradCAMExplanation(BaseModel):
    """Grad-CAM visual interpretability payload for thoracic radiographs."""

    target_pathology: str = Field(..., description="Thoracic finding explained by Grad-CAM")
    target_pathology_index: int = Field(..., description="Index of target pathology explained")
    logit_score: float = Field(..., description="Raw logit score before sigmoid")
    target_layer: str = Field(default="denseblock4", description="Convolutional block hooked")
    resolution: List[int] = Field(default=[224, 224], description="Heatmap resolution [H, W]")
    heatmap_overlay_base64: str = Field(
        ...,
        description="Base64-encoded PNG data URI of radiograph with blended Jet heatmap overlay",
    )
    raw_heatmap_base64: str = Field(
        ...,
        description="Base64-encoded PNG data URI of colorized Jet heatmap",
    )
    salient_region_summary: ChestXraySalientRegionSummary = Field(
        ...,
        description="Coordinates and metrics of peak attention regions",
    )
    interpretability_note: str = Field(
        ...,
        description="Medical qualification explaining that heatmaps indicate model attention, not confirmed pathology",
    )


class ChestXrayPredictResponse(BaseModel):
    """Complete prediction and visual explainability response schema for chest X-ray."""

    session_id: str = Field(..., description="Anonymous UUID token for this session")
    modality: str = Field(default="chest_xray", description="Imaging modality")
    status: str = Field(default="SUCCESS", description="Pipeline execution state")
    model_version: str = Field(..., description="Model architecture and version")
    metadata: ImageMetadataSchema = Field(..., description="In-memory image attributes")
    prediction: ChestXrayPredictionDetail = Field(
        ...,
        description="Model multi-label findings and scores",
    )
    explanation: Optional[ChestXrayGradCAMExplanation] = Field(
        default=None,
        description="Optional Grad-CAM visual heatmap interpretation",
    )
    disclaimer: str = Field(
        default=(
            "RESEARCH ONLY: Not for clinical or diagnostic use. "
            "Chest radiograph evaluation requires review by a licensed radiologist or pulmonologist."
        ),
        description="Mandatory medical research disclaimer",
    )
    created_at: datetime = Field(..., description="UTC creation timestamp")


class ChestXrayModelStatusResponse(BaseModel):
    """Readiness and architecture status of Chest X-ray deep learning pipeline."""

    model_name: str = Field(..., description="Model architecture name (e.g. DenseNet-121)")
    model_version: str = Field(..., description="Checkpoint and library version")
    status: str = Field(..., description="Operational status ('LOADED' or 'UNAVAILABLE')")
    device: str = Field(..., description="Compute device ('cpu' or 'cuda')")
    checkpoint_hash: str = Field(..., description="SHA-256 cryptographic digest of weights")
    weights_path: str = Field(..., description="Local or cached checkpoint path")
    pathologies_count: int = Field(..., description="Number of evaluated multi-label thoracic pathologies")
    pathologies: List[str] = Field(..., description="List of evaluated thoracic pathologies")
    disclaimer: str = Field(
        default="RESEARCH ONLY: Experimental AI model for chest radiograph analysis. Not for clinical diagnosis.",
        description="Medical research disclaimer",
    )
