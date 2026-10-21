"""Retinal fundus image service.

Handles:
1. Triggering in-memory validation.
2. Generating an anonymous session ID.
3. Persisting session metadata to SQLAlchemy without persisting image bytes.
4. Constructing an honest development placeholder response.
"""

from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_session_id
from app.db.models import AnalysisSession
from app.schemas.retina import RetinaAnalysisResponse
from app.services.file_validator import validate_and_extract_image_metadata


async def process_retina_image(
    file: UploadFile,
    db: Session,
) -> RetinaAnalysisResponse:
    """Validate retinal image, record audit metadata, and return a development placeholder."""
    # 1. In-memory validation
    metadata, _ = await validate_and_extract_image_metadata(file)

    # 2. Generate anonymous session identifier
    session_id = generate_session_id()
    now = datetime.now(timezone.utc)
    model_version = "retina_v0.1_dev_placeholder"

    # 3. Persist audit session to SQLite
    session_record = AnalysisSession(
        session_id=session_id,
        modality="retina",
        file_name=metadata.file_name,
        file_size_bytes=metadata.file_size_bytes,
        file_hash=metadata.file_hash,
        mime_type=metadata.mime_type,
        image_width=metadata.image_width,
        image_height=metadata.image_height,
        model_version=model_version,
        status="DEVELOPMENT_PLACEHOLDER",
        prediction_category=None,
        prediction_confidence=None,
        explanation_text=None,
        explanation_heatmap_path=None,
        created_at=now,
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    # 4. Return explicit development placeholder response
    return RetinaAnalysisResponse(
        session_id=session_id,
        modality="retina",
        status="DEVELOPMENT_PLACEHOLDER",
        message=(
            "Retina model pipeline is not implemented yet. "
            "Image was successfully validated, technical metadata recorded, and session registered. "
            "No medical prediction was generated."
        ),
        model_version=model_version,
        metadata=metadata,
        prediction=None,
        explanation=None,
        disclaimer=(
            "RESEARCH ONLY: Not for clinical or diagnostic use. "
            "Never make clinical decisions based on placeholder responses."
        ),
        created_at=now,
    )


# ==============================================================================
# RETINAGUARD REAL MODEL INFERENCE & GRAD-CAM SERVICE
# ==============================================================================

import io
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
from PIL import Image
import torch

from ai_models.retina.gradcam import RetinaGradCAM
from ai_models.retina.model import DR_CLASS_NAMES, RetinaResNet18
from ai_models.retina.preprocessing import RetinaImagePreprocessor
from app.core.config import settings
from app.schemas.retina import (
    RetinaGradCAMExplanation,
    RetinaModelStatusResponse,
    RetinaPredictResponse,
    RetinaPredictionDetail,
    SalientRegionSummary,
)

logger = logging.getLogger("medvision.retina.service")

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DR_SEVERITY_LEVELS: Dict[int, str] = {
    0: "None",
    1: "Mild",
    2: "Moderate",
    3: "Severe",
    4: "Proliferative",
}

DR_CLINICAL_DESCRIPTIONS: Dict[int, str] = {
    0: "No Diabetic Retinopathy: Normal retinal fundus appearance with no detected microaneurysms or lesions.",
    1: "Mild Non-Proliferative DR: Microaneurysms only. Earliest recognizable stage of diabetic retinopathy.",
    2: "Moderate Non-Proliferative DR: More than just microaneurysms; intraretinal hemorrhages and cotton wool spots may be present.",
    3: "Severe Non-Proliferative DR: Extensive intraretinal hemorrhages (4-2-1 rule), venous beading, or prominent IRMA.",
    4: "Proliferative Diabetic Retinopathy: Advanced disease with pathological neovascularization and vitreous hemorrhage risks.",
}


def resolve_retina_checkpoint(
    override_path: Optional[Union[Path, str]] = None,
    allow_fallback: bool = True,
    project_root: Optional[Path] = None,
) -> Tuple[Optional[Path], str, Optional[str]]:
    """Resolve the RetinaGuard checkpoint path according to the selection hierarchy.

    Selection hierarchy:
    1. User-configured override: If `override_path` or `settings.RETINA_CHECKPOINT_PATH`
       is provided, validate that it exists. If it exists, select it. If it does NOT exist,
       return an explicit error immediately rather than silently falling back.
    2. Primary preferred checkpoint: `ai_models/retina/weights/retinaguard_v2.pt`.
       If it exists, select it.
    3. Explicit baseline fallback: `ai_models/retina/weights/best_model.pt`.
       Selected only when V2 is absent and `allow_fallback` is True.
    4. Readiness error: If no valid checkpoint exists, return None and an explicit error reason.

    All relative paths are resolved from `project_root` (repository root), never from the cwd.

    Returns:
        Tuple of (resolved_path, selection_source, error_reason).
    """
    root = (project_root or PROJECT_ROOT).resolve()

    # 1. User-configured override
    candidate_override = override_path if override_path is not None else settings.RETINA_CHECKPOINT_PATH
    if candidate_override:
        p = Path(candidate_override)
        resolved_override = p if p.is_absolute() else (root / p).resolve()
        if resolved_override.is_file():
            return resolved_override, "override", None
        else:
            return None, "override_invalid", f"Configured checkpoint override not found at: {resolved_override}"

    # 2. Preferred V2 Checkpoint
    v2_path = (root / "ai_models" / "retina" / "weights" / "retinaguard_v2.pt").resolve()
    if v2_path.is_file():
        return v2_path, "v2_preferred", None

    # 3. Explicit baseline fallback
    if allow_fallback:
        baseline_path = (root / "ai_models" / "retina" / "weights" / "best_model.pt").resolve()
        if baseline_path.is_file():
            return baseline_path, "baseline_fallback", None

    # 4. Neither exists
    weights_dir = root / "ai_models" / "retina" / "weights"
    return None, "none", f"No valid RetinaGuard checkpoint found in {weights_dir}. Neither retinaguard_v2.pt nor best_model.pt exists."


def determine_model_version_and_metadata(
    checkpoint_path: Path,
    meta: Dict[str, Any],
) -> Tuple[str, Optional[int], Optional[float]]:
    """Determine trustworthy model version string and metadata from verified checkpoint contents.

    Requirements:
    - Use `retinaguard_v2_epoch8` ONLY when the loaded checkpoint is verified as the V2 Epoch 8 checkpoint.
    - Do not hardcode a version that could misidentify another checkpoint.
    - Accurately report epoch and validation metric metadata.
    """
    epoch = meta.get("epoch")
    val_macro_f1 = meta.get("val_macro_f1")
    filename = checkpoint_path.name.lower()

    # Verify if this is the V2 checkpoint
    is_v2 = "retinaguard_v2" in filename
    if is_v2 and epoch == 8:
        model_version = "retinaguard_v2_epoch8"
    elif is_v2 and epoch is not None:
        model_version = f"retinaguard_v2_epoch{epoch}"
    elif filename == "best_model.pt" and epoch is not None:
        model_version = f"retinaguard_baseline_epoch{epoch}"
    elif epoch is not None:
        model_version = f"retina_resnet18_epoch{epoch}"
    else:
        # Fallback to model config or generic tag
        model_version = meta.get("config", {}).get("model_version", "retina_resnet18_v1.0")

    return model_version, epoch, val_macro_f1


class RetinaModelService:
    """Manages cached model loading, inference execution, and Grad-CAM generation.

    Enforces singleton pattern to avoid reloading model weights per HTTP request.
    """

    _instance: Optional["RetinaModelService"] = None

    def __init__(
        self,
        checkpoint_path: Optional[Union[Path, str]] = None,
        allow_fallback: bool = True,
        project_root: Optional[Path] = None,
    ) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.target_size = (224, 224)
        self.preprocessor = RetinaImagePreprocessor(
            target_size=self.target_size,
            normalize=True,
            is_training=False,
            augment=False,
        )

        self.project_root = (project_root or PROJECT_ROOT).resolve()
        resolved_ckpt, selection_source, error_reason = resolve_retina_checkpoint(
            override_path=checkpoint_path,
            allow_fallback=allow_fallback,
            project_root=self.project_root,
        )

        self.checkpoint_path: Optional[Path] = resolved_ckpt
        self.selection_source: str = selection_source
        self.status_message: Optional[str] = error_reason
        self.checkpoint_filename: Optional[str] = resolved_ckpt.name if resolved_ckpt else None
        self.checkpoint_epoch: Optional[int] = None
        self.checkpoint_val_macro_f1: Optional[float] = None

        self.model: Optional[RetinaResNet18] = None
        self.gradcam: Optional[RetinaGradCAM] = None
        self.model_version: str = "unloaded"
        self.is_loaded: bool = False

        if self.checkpoint_path and self.checkpoint_path.is_file():
            try:
                self.load_model()
            except Exception as e:
                logger.error("Failed to load RetinaGuard checkpoint at %s: %s", self.checkpoint_path, e)
                self.is_loaded = False
                self.status_message = f"Failed to load checkpoint at {self.checkpoint_path}: {e}"
        else:
            logger.warning(
                "RetinaGuard checkpoint resolution failed or file not found (%s: %s). Model service starting unloaded.",
                self.selection_source,
                self.status_message,
            )

    def load_model(self) -> None:
        """Load weights into memory and initialize Grad-CAM hooks."""
        if not self.checkpoint_path or not self.checkpoint_path.is_file():
            raise FileNotFoundError(f"Cannot load model: checkpoint does not exist at {self.checkpoint_path}")

        logger.info("Loading RetinaGuard model from %s on device %s", self.checkpoint_path, self.device)
        self.model, meta = RetinaResNet18.load_from_checkpoint(self.checkpoint_path, map_location=self.device)
        self.model.to(self.device)
        self.model.eval()
        self.gradcam = RetinaGradCAM(self.model, target_size=self.target_size)

        self.model_version, self.checkpoint_epoch, self.checkpoint_val_macro_f1 = determine_model_version_and_metadata(
            self.checkpoint_path, meta
        )
        self.checkpoint_filename = self.checkpoint_path.name
        self.is_loaded = True
        self.status_message = (
            f"Model loaded successfully from {self.checkpoint_filename} "
            f"(selection: {self.selection_source}, epoch: {self.checkpoint_epoch}, "
            f"val_macro_f1: {round(self.checkpoint_val_macro_f1, 4) if self.checkpoint_val_macro_f1 is not None else 'N/A'})"
        )
        logger.info(
            "RetinaGuard model successfully loaded (version: %s, epoch: %s, macro_f1: %s, source: %s)",
            self.model_version,
            self.checkpoint_epoch,
            self.checkpoint_val_macro_f1,
            self.selection_source,
        )

    def get_status(self) -> RetinaModelStatusResponse:
        """Return readiness and hardware state."""
        return RetinaModelStatusResponse(
            status="ready" if self.is_loaded else "unloaded",
            is_loaded=self.is_loaded,
            model_version=self.model_version,
            checkpoint_path=str(self.checkpoint_path) if (self.is_loaded and self.checkpoint_path and self.checkpoint_path.is_file()) else None,
            checkpoint_filename=self.checkpoint_filename if self.is_loaded else None,
            checkpoint_epoch=self.checkpoint_epoch if self.is_loaded else None,
            checkpoint_val_macro_f1=round(self.checkpoint_val_macro_f1, 4) if (self.is_loaded and self.checkpoint_val_macro_f1 is not None) else None,
            selection_source=self.selection_source if self.is_loaded else None,
            device=str(self.device),
            num_classes=5,
            classes={str(k): v for k, v in DR_CLASS_NAMES.items()},
            gradcam_supported=True,
            status_message=self.status_message,
        )

    def predict(
        self,
        raw_bytes: bytes,
        include_gradcam: bool = True,
    ) -> Tuple[RetinaPredictionDetail, Optional[RetinaGradCAMExplanation]]:
        """Run deep learning forward pass and optional Grad-CAM visual interpretability."""
        if not self.is_loaded or self.model is None or self.gradcam is None:
            err = self.status_message or f"Checkpoint not loaded ({self.checkpoint_path})"
            raise RuntimeError(f"RetinaGuard model is not loaded: {err}")

        # 1. Open PIL image in memory
        pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")

        # 2. Preprocess to normalized tensor
        tensor_np = self.preprocessor.preprocess(pil_img)
        tensor = torch.from_numpy(tensor_np).unsqueeze(0).to(self.device)

        # 3. Model forward pass
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        pred_class = int(np.argmax(probs))
        confidence = float(probs[pred_class])

        class_scores_dict: Dict[str, float] = {
            str(c): round(float(p), 4) for c, p in enumerate(probs)
        }

        prediction_detail = RetinaPredictionDetail(
            predicted_class=pred_class,
            class_label=DR_CLASS_NAMES.get(pred_class, f"Class {pred_class}"),
            severity_level=DR_SEVERITY_LEVELS.get(pred_class, "Unknown"),
            confidence_score=round(confidence, 4),
            all_class_scores=class_scores_dict,
            clinical_description=DR_CLINICAL_DESCRIPTIONS.get(pred_class, ""),
        )

        # 4. Optional Grad-CAM visual heatmap
        explanation: Optional[RetinaGradCAMExplanation] = None
        if include_gradcam:
            cam_data = self.gradcam.generate_visualizations(
                pil_img,
                preprocessor=self.preprocessor,
                target_class=pred_class,
                overlay_alpha=0.4,
            )
            explanation = RetinaGradCAMExplanation(
                target_class=cam_data["target_class"],
                target_class_label=cam_data["target_class_label"],
                logit_score=cam_data["logit_score"],
                target_layer=cam_data["target_layer"],
                resolution=cam_data["resolution"],
                heatmap_overlay_base64=cam_data["heatmap_overlay_base64"],
                raw_heatmap_base64=cam_data["raw_heatmap_base64"],
                salient_region_summary=SalientRegionSummary(**cam_data["salient_region_summary"]),
                interpretability_note=cam_data["interpretability_note"],
            )

        return prediction_detail, explanation


_global_retina_service: Optional[RetinaModelService] = None


def get_retina_service(
    checkpoint_path: Optional[Union[Path, str]] = None,
    allow_fallback: bool = True,
    force_reload: bool = False,
) -> RetinaModelService:
    """Return singleton instance of RetinaModelService, initializing if needed."""
    global _global_retina_service
    if _global_retina_service is None or force_reload:
        _global_retina_service = RetinaModelService(
            checkpoint_path=checkpoint_path,
            allow_fallback=allow_fallback,
        )
    return _global_retina_service


def reset_retina_service(service: Optional[RetinaModelService] = None) -> Optional[RetinaModelService]:
    """Reset the global singleton service instance (useful for test isolation)."""
    global _global_retina_service
    previous = _global_retina_service
    _global_retina_service = service
    return previous


async def predict_retina_image(
    file: UploadFile,
    db: Session,
    include_gradcam: bool = True,
) -> RetinaPredictResponse:
    """Execute validation, inference, and audit registration for retinal images.

    Zero disk storage: processed entirely in memory.
    """
    # 1. In-memory validation
    metadata, raw_bytes = await validate_and_extract_image_metadata(file)

    # 2. Check model service readiness
    service = get_retina_service()
    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RetinaGuard model service is unavailable: {service.status_message or 'Model weights not loaded'}",
        )

    # 3. Model inference and Grad-CAM
    prediction, explanation = service.predict(raw_bytes, include_gradcam=include_gradcam)

    # 4. Anonymous session ID and persistence
    session_id = generate_session_id()
    now = datetime.now(timezone.utc)

    session_record = AnalysisSession(
        session_id=session_id,
        modality="retina",
        file_name=metadata.file_name,
        file_size_bytes=metadata.file_size_bytes,
        file_hash=metadata.file_hash,
        mime_type=metadata.mime_type,
        image_width=metadata.image_width,
        image_height=metadata.image_height,
        model_version=service.model_version,
        status="SUCCESS",
        prediction_category=prediction.class_label,
        prediction_confidence=prediction.confidence_score,
        explanation_text=explanation.interpretability_note if explanation else None,
        explanation_heatmap_path=None,  # Zero-disk policy: heatmaps are returned as data URIs
        created_at=now,
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    # 5. Construct complete response
    return RetinaPredictResponse(
        session_id=session_id,
        modality="retina",
        status="SUCCESS",
        model_version=service.model_version,
        metadata=metadata,
        prediction=prediction,
        explanation=explanation,
        created_at=now,
    )
