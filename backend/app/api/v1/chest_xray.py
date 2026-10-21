"""Chest X-Ray (CXR) radiograph analysis API router."""

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.chest_xray import (
    ChestXrayAnalysisResponse,
    ChestXrayModelStatusResponse,
    ChestXrayPredictResponse,
)
from app.schemas.common import ErrorDetailResponse
from app.services.chest_xray_service import (
    get_chest_xray_service,
    predict_chest_xray_image,
    process_chest_xray_image,
)

router = APIRouter(prefix="/chest-xray", tags=["Chest Radiography"])


@router.post(
    "/analyze",
    response_model=ChestXrayAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Chest X-Ray Radiograph (Development Placeholder)",
    description=(
        "Receives a chest radiograph image (JPEG, PNG, WebP), performs in-memory format "
        "and integrity validation, generates an anonymous audit session, and returns a development placeholder. "
        "NOTICE: No medical predictions are produced by this placeholder."
    ),
    responses={
        400: {"model": ErrorDetailResponse, "description": "Invalid or corrupted image"},
        401: {"model": ErrorDetailResponse, "description": "Unauthorized: missing or invalid API key"},
        413: {"model": ErrorDetailResponse, "description": "File size exceeds upload limit"},
        415: {"model": ErrorDetailResponse, "description": "Unsupported media format"},
    },
)
async def analyze_chest_xray_image(
    file: UploadFile = File(..., description="Chest radiograph binary stream"),
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_api_key),
) -> ChestXrayAnalysisResponse:
    """Endpoint for chest X-Ray image upload and placeholder session creation."""
    return await process_chest_xray_image(file=file, db=db)


@router.post(
    "/predict",
    response_model=ChestXrayPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Thoracic Pathologies with Grad-CAM Explainability",
    description=(
        "Upload a posteroanterior (PA) or anteroposterior (AP) chest radiograph (JPEG, PNG, WebP) "
        "to evaluate 18 multi-label thoracic pathologies using DenseNet-121 (TorchXRayVision benchmark), "
        "calibrated operating thresholds, and aligned Grad-CAM visual heatmaps.\n\n"
        "RESEARCH USE ONLY: Prototype educational AI model, strictly not for clinical diagnosis."
    ),
    responses={
        400: {"model": ErrorDetailResponse, "description": "Invalid, corrupted, or unreadable image"},
        401: {"model": ErrorDetailResponse, "description": "Unauthorized: missing or invalid API key"},
        413: {"model": ErrorDetailResponse, "description": "File size exceeds upload limit (10MB)"},
        415: {"model": ErrorDetailResponse, "description": "Unsupported media format"},
        503: {"model": ErrorDetailResponse, "description": "Model service unavailable or checkpoint not loaded"},
    },
)
async def predict_chest_xray(
    file: UploadFile = File(..., description="Chest radiograph image binary stream"),
    include_gradcam: bool = Query(
        True,
        description="Whether to generate and return base64 Grad-CAM visual heatmap overlay",
    ),
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_api_key),
) -> ChestXrayPredictResponse:

    """Classify chest radiograph and generate Grad-CAM attribution."""
    return await predict_chest_xray_image(file=file, db=db, include_gradcam=include_gradcam)


@router.get(
    "/model-status",
    response_model=ChestXrayModelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Chest X-Ray DenseNet-121 Model Readiness and Hardware Status",
    description="Returns current status of loaded DenseNet-121 weights, device (CPU/GPU), and supported 18 thoracic pathologies.",
)
async def get_model_status() -> ChestXrayModelStatusResponse:
    """Check readiness of Chest X-Ray model weights and inference pipeline."""
    service = get_chest_xray_service()
    return service.get_status()
