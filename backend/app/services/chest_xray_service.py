"""Chest X-Ray (CXR) radiograph service.

Handles:
1. In-memory format, size, and integrity validation.
2. Anonymous session ID generation.
3. Persisting session audit records to SQLite database.
4. Deep learning inference via TorchXRayVision DenseNet-121.
5. Aligned Grad-CAM visual attention heatmap generation.
6. Honest development placeholder responses for /analyze endpoint.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ai_models.chest_xray.explainability import ChestXrayExplainabilityEngine
from ai_models.chest_xray.inference import ChestXrayInferencePipeline
from ai_models.chest_xray.preprocessing import preprocess_chest_xray_image
from app.core.security import generate_session_id
from app.db.models import AnalysisSession
from app.schemas.chest_xray import (
    ChestXrayAnalysisResponse,
    ChestXrayGradCAMExplanation,
    ChestXrayModelStatusResponse,
    ChestXrayPathologyScore,
    ChestXrayPredictResponse,
    ChestXrayPredictionDetail,
    ChestXraySalientRegionSummary,
)
from app.services.file_validator import validate_and_extract_image_metadata

logger = logging.getLogger("medvision.chest_xray.service")

CLINICAL_DESCRIPTIONS: Dict[str, str] = {
    "Atelectasis": "Partial or complete collapse of lung parenchyma, frequently caused by airway obstruction, shallow respiration, or hypoventilation.",
    "Consolidation": "Alveolar air spaces filled with inflammatory exudate, pus, fluid, or blood, characteristic of bacterial pneumonia or acute alveolar processes.",
    "Infiltration": "Abnormal accumulation of substance (cellular, fluid, or proteinaceous) in the pulmonary interstitium or alveolar spaces.",
    "Pneumothorax": "Presence of air in the pleural space between the visceral and parietal pleura, potentially compromising pulmonary ventilation.",
    "Edema": "Accumulation of fluid in pulmonary interstitium and alveolar sacs, frequently secondary to elevated pulmonary venous pressure or cardiac decompensation.",
    "Emphysema": "Permanent enlargement and destruction of air spaces distal to terminal bronchioles without fibrosis, a hallmark of chronic obstructive pulmonary disease (COPD).",
    "Fibrosis": "Formation of excess fibrous connective tissue in the lung parenchyma, reducing lung compliance and alveolar gas diffusion capacity.",
    "Effusion": "Excessive accumulation of fluid in the pleural cavity between the parietal and visceral pleura, blunting costophrenic angles.",
    "Pneumonia": "Infectious inflammation of the lung parenchyma, presenting radiographically as lobar or patchy airspace opacification.",
    "Pleural_Thickening": "Fibrous thickening or calcification of the pleural membrane, commonly reflecting sequelae of prior pleuritis, hemothorax, or asbestos exposure.",
    "Cardiomegaly": "Enlargement of the cardiac silhouette where cardiothoracic ratio exceeds 0.50 on standard posteroanterior projection.",
    "Nodule": "Discrete, well-defined pulmonary parenchymal opacity measuring up to 30 mm in diameter, requiring clinical correlation and follow-up.",
    "Mass": "Circumscribed pulmonary parenchymal lesion exceeding 30 mm in diameter, carrying higher clinical suspicion and warranting urgent diagnostic workup.",
    "Hernia": "Protrusion of abdominal contents into the thoracic cavity through a diaphragmatic aperture (e.g. hiatal or traumatic hernia).",
    "Lung Lesion": "Non-specific localized structural abnormality in lung tissue requiring correlation with patient history and high-resolution imaging.",
    "Fracture": "Disruption or cortical discontinuity in thoracic skeletal structures (ribs, clavicles, scapulae, or vertebrae).",
    "Lung Opacity": "Non-specific area of increased radiographic density on chest radiograph, reflecting decreased aeration or increased tissue density.",
    "Enlarged Cardiomediastinum": "Widening of mediastinal or cardiac contour, which may indicate vascular dilatation, lymphadenopathy, or mediastinal mass.",
}


class ChestXrayModelService:
    """Singleton service managing DenseNet-121 CXR model lifecycle and inference."""

    _instance: Optional["ChestXrayModelService"] = None

    def __init__(self) -> None:
        self.pipeline = ChestXrayInferencePipeline()
        self.explainability_engine = ChestXrayExplainabilityEngine(self.pipeline)
        self._ensure_loaded()

    @classmethod
    def get_instance(cls) -> "ChestXrayModelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_loaded(self) -> None:
        try:
            self.pipeline.load_model()
            logger.info("ChestXrayModelService: DenseNet-121 successfully loaded.")
        except Exception as exc:
            logger.warning("ChestXrayModelService: Could not preload model weights: %s", exc)

    def get_status(self) -> ChestXrayModelStatusResponse:
        """Return readiness and metadata of the DenseNet-121 CXR pipeline."""
        is_loaded = self.pipeline.is_loaded
        return ChestXrayModelStatusResponse(
            model_name=self.pipeline.architecture,
            model_version=self.pipeline.model_version,
            status="LOADED" if is_loaded else "UNAVAILABLE",
            device=str(self.pipeline.device),
            checkpoint_hash=self.pipeline.checkpoint_hash,
            weights_path=self.pipeline.model_checkpoint_path or "unresolved",
            pathologies_count=len(self.pipeline.pathologies),
            pathologies=self.pipeline.pathologies,
            disclaimer="RESEARCH ONLY: Experimental AI model for chest radiograph analysis. Not for clinical diagnosis.",
        )

    def run_prediction(
        self,
        image_bytes: bytes,
        include_gradcam: bool = True,
    ) -> Tuple[ChestXrayPredictionDetail, Optional[ChestXrayGradCAMExplanation], Dict[str, Any]]:
        """Execute full preprocessing, inference, and explainability on image bytes."""
        if not self.pipeline.is_loaded:
            self.pipeline.load_model()

        # 1. Preprocessing
        tensor, display_img, meta = preprocess_chest_xray_image(image_bytes, target_size=224)

        # 2. Forward inference
        raw_pred = self.pipeline.predict(tensor)

        top_finding = raw_pred["top_finding"]
        top_score = raw_pred["top_score"]
        findings = raw_pred["findings"]
        raw_above_thresh = raw_pred["findings_above_threshold"]

        findings_above_thresh = [
            ChestXrayPathologyScore(
                name=item["name"],
                score=item["score"],
                threshold=item["threshold"],
                detected=item["detected"],
            )
            for item in raw_above_thresh
        ]

        clinical_desc = CLINICAL_DESCRIPTIONS.get(
            top_finding,
            f"Evaluated thoracic finding '{top_finding}'. Consult a licensed radiologist for clinical evaluation.",
        )

        prediction_detail = ChestXrayPredictionDetail(
            top_finding=top_finding,
            top_score=top_score,
            findings=findings,
            findings_above_threshold=findings_above_thresh,
            all_class_scores=findings,
            calibration_notice=raw_pred["calibration_notice"],
            clinical_description=clinical_desc,
        )

        # 3. Grad-CAM visual explanation
        explanation_detail: Optional[ChestXrayGradCAMExplanation] = None
        if include_gradcam:
            try:
                raw_cam = self.explainability_engine.generate_heatmap(
                    input_tensor=tensor,
                    display_image=display_img,
                    target_pathology=top_finding,
                )
                salient = ChestXraySalientRegionSummary(
                    peak_y=raw_cam["salient_region_summary"]["peak_y"],
                    peak_x=raw_cam["salient_region_summary"]["peak_x"],
                    peak_intensity=raw_cam["salient_region_summary"]["peak_intensity"],
                    mean_intensity=raw_cam["salient_region_summary"]["mean_intensity"],
                    active_area_ratio=raw_cam["salient_region_summary"]["active_area_ratio"],
                )
                explanation_detail = ChestXrayGradCAMExplanation(
                    target_pathology=raw_cam["target_pathology"],
                    target_pathology_index=raw_cam["target_pathology_index"],
                    logit_score=raw_cam["logit_score"],
                    target_layer=raw_cam["target_layer"],
                    resolution=raw_cam["resolution"],
                    heatmap_overlay_base64=raw_cam["heatmap_overlay_base64"],
                    raw_heatmap_base64=raw_cam["raw_heatmap_base64"],
                    salient_region_summary=salient,
                    interpretability_note=raw_cam["interpretability_note"],
                )
            except Exception as cam_exc:
                logger.warning("Grad-CAM generation failed: %s", cam_exc)
                explanation_detail = None

        return prediction_detail, explanation_detail, meta


def get_chest_xray_service() -> ChestXrayModelService:
    """Dependency helper returning singleton ChestXrayModelService."""
    return ChestXrayModelService.get_instance()


async def process_chest_xray_image(
    file: UploadFile,
    db: Session,
) -> ChestXrayAnalysisResponse:
    """Validate chest radiograph, record audit metadata, and return honest development placeholder for /analyze."""
    metadata, _ = await validate_and_extract_image_metadata(file)

    session_id = generate_session_id()
    now = datetime.now(timezone.utc)
    model_version = "chest_xray_v0.1_dev_placeholder"

    session_record = AnalysisSession(
        session_id=session_id,
        modality="chest_xray",
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

    return ChestXrayAnalysisResponse(
        session_id=session_id,
        modality="chest_xray",
        status="DEVELOPMENT_PLACEHOLDER",
        message=(
            "Chest X-Ray model pipeline is not implemented yet. "
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


async def predict_chest_xray_image(
    file: UploadFile,
    db: Session,
    include_gradcam: bool = True,
) -> ChestXrayPredictResponse:
    """Classify chest radiograph, generate Grad-CAM attribution, and persist audit record."""
    # 1. Image validation
    metadata, image_bytes = await validate_and_extract_image_metadata(file)

    service = get_chest_xray_service()
    if not service.pipeline.is_loaded:
        try:
            service.pipeline.load_model()
        except Exception as exc:
            logger.error("Failed to load Chest X-ray model: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Chest X-Ray model service is unavailable: {exc}",
            ) from exc

    session_id = generate_session_id()
    now = datetime.now(timezone.utc)

    # 2. Run inference
    try:
        prediction_detail, explanation_detail, _ = service.run_prediction(
            image_bytes=image_bytes,
            include_gradcam=include_gradcam,
        )
    except ValueError as val_exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process chest radiograph: {val_exc}",
        ) from val_exc
    except Exception as exc:
        logger.error("Chest X-ray prediction failure: %s", exc)
        # Audit failure record in DB without claiming SUCCESS
        fail_record = AnalysisSession(
            session_id=session_id,
            modality="chest_xray",
            file_name=metadata.file_name,
            file_size_bytes=metadata.file_size_bytes,
            file_hash=metadata.file_hash,
            mime_type=metadata.mime_type,
            image_width=metadata.image_width,
            image_height=metadata.image_height,
            model_version=service.pipeline.model_version,
            status="FAILED_INFERENCE",
            prediction_category=None,
            prediction_confidence=None,
            created_at=now,
        )
        db.add(fail_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error during chest radiograph analysis: {exc}",
        ) from exc

    # 3. Persist authoritative successful analysis session
    session_record = AnalysisSession(
        session_id=session_id,
        modality="chest_xray",
        file_name=metadata.file_name,
        file_size_bytes=metadata.file_size_bytes,
        file_hash=metadata.file_hash,
        mime_type=metadata.mime_type,
        image_width=metadata.image_width,
        image_height=metadata.image_height,
        model_version=service.pipeline.model_version,
        status="SUCCESS",
        prediction_category=prediction_detail.top_finding,
        prediction_confidence=prediction_detail.top_score,
        explanation_text=prediction_detail.clinical_description,
        explanation_heatmap_path=None,  # No local file paths leaked
        created_at=now,
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    return ChestXrayPredictResponse(
        session_id=session_id,
        modality="chest_xray",
        status="SUCCESS",
        model_version=service.pipeline.model_version,
        metadata=metadata,
        prediction=prediction_detail,
        explanation=explanation_detail,
        disclaimer=(
            "RESEARCH ONLY: Not for clinical or diagnostic use. "
            "Chest radiograph evaluation requires review by a licensed radiologist or pulmonologist."
        ),
        created_at=now,
    )
