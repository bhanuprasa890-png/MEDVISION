from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.common import ErrorDetailResponse
from app.schemas.retina import (
    RetinaAnalysisResponse,
    RetinaModelStatusResponse,
    RetinaPredictResponse,
)
from app.services.retina_service import (
    get_retina_service,
    predict_retina_image,
    process_retina_image,
)

router = APIRouter(prefix="/retina", tags=["Retinal Imaging"])


@router.post(
    "/analyze",
    response_model=RetinaAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Retinal Fundus Image (Development Placeholder)",
    description=(
        "Receives a retinal fundus image (JPEG, PNG, WebP), performs in-memory format "
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
async def analyze_retina_image(
    file: UploadFile = File(..., description="Retinal fundus image binary stream"),
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_api_key),
) -> RetinaAnalysisResponse:
    """Endpoint for retinal fundus image upload and placeholder session creation."""
    return await process_retina_image(file=file, db=db)


@router.post(
    "/predict",
    response_model=RetinaPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict Diabetic Retinopathy Severity with Grad-CAM Explainability",
    description=(
        "Upload a retinal fundus photograph (JPEG, PNG, WebP) to obtain a 5-class Diabetic "
        "Retinopathy severity prediction (0: No DR to 4: Proliferative DR), raw uncalibrated "
        "softmax score distribution, and aligned Grad-CAM visual attention heatmaps.\n\n"
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
async def predict_retina(
    file: UploadFile = File(..., description="Retinal fundus image binary stream"),
    include_gradcam: bool = Query(
        True,
        description="Whether to generate and return base64 Grad-CAM visual heatmap overlay",
    ),
    db: Session = Depends(get_db),
    _auth: bool = Depends(verify_api_key),
) -> RetinaPredictResponse:

    """Classify retinal fundus image and generate Grad-CAM attribution."""
    return await predict_retina_image(file=file, db=db, include_gradcam=include_gradcam)


@router.get(
    "/model-status",
    response_model=RetinaModelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="RetinaGuard Model Readiness and Hardware Status",
    description="Returns current status of the loaded RetinaResNet18 weights, device (CPU/GPU), and Grad-CAM support.",
)
async def get_model_status() -> RetinaModelStatusResponse:
    """Check readiness of RetinaGuard model weights and inference pipeline."""
    service = get_retina_service()
    return service.get_status()
