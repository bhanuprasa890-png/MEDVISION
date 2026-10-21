"""Automated test suite for RetinaGuard API endpoints and Grad-CAM visual heatmaps."""

import base64
import io
from pathlib import Path
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient
from PIL import Image

from ai_models.retina.gradcam import RetinaGradCAM, apply_jet_colormap
from ai_models.retina.model import DR_CLASS_NAMES, build_retina_model
from app.db.models import AnalysisSession
from app.services.retina_service import get_retina_service


# ==============================================================================
# 1. PURE GRAD-CAM UNIT TESTS
# ==============================================================================


def test_jet_colormap_bounds():
    """Verify apply_jet_colormap maps [0.0, 1.0] inputs to valid (H, W, 3) uint8 arrays."""
    # Test corners and middle
    heatmap = np.array([[0.0, 0.5], [0.75, 1.0]], dtype=np.float32)
    rgb = apply_jet_colormap(heatmap)

    assert rgb.shape == (2, 2, 3)
    assert rgb.dtype == np.uint8
    assert rgb.min() >= 0
    assert rgb.max() <= 255


def test_gradcam_computation_shape_and_bounds():
    """Verify RetinaGradCAM outputs normalized 2D heatmaps in [0.0, 1.0]."""
    model = build_retina_model(num_classes=5, pretrained=False)
    explainer = RetinaGradCAM(model, target_size=(224, 224))

    dummy_input = torch.randn(1, 3, 224, 224)
    cam, target_class, score = explainer.compute_cam(dummy_input, target_class=1)

    assert cam.shape == (224, 224)
    assert target_class == 1
    assert isinstance(score, float)
    assert 0.0 <= cam.min() <= 1.0
    assert 0.0 <= cam.max() <= 1.0


def test_gradcam_invalid_tensor_dimension_raises():
    """Verify compute_cam raises ValueError when given non-batch-1 or 3D tensor."""
    model = build_retina_model(num_classes=5, pretrained=False)
    explainer = RetinaGradCAM(model)

    with pytest.raises(ValueError, match="requires input tensor with shape"):
        explainer.compute_cam(torch.randn(3, 224, 224))  # Missing batch dimension


def test_gradcam_generate_visualizations_data_uris():
    """Verify generate_visualizations returns valid base64 PNG data URIs."""
    model = build_retina_model(num_classes=5, pretrained=False)
    explainer = RetinaGradCAM(model, target_size=(224, 224))

    pil_img = Image.new("RGB", (256, 256), color=(100, 150, 200))
    vis = explainer.generate_visualizations(pil_img, target_class=2)

    assert vis["target_class"] == 2
    assert vis["target_class_label"] == DR_CLASS_NAMES[2]
    assert vis["heatmap_overlay_base64"].startswith("data:image/png;base64,")
    assert vis["raw_heatmap_base64"].startswith("data:image/png;base64,")
    assert "salient_region_summary" in vis
    assert "peak_y" in vis["salient_region_summary"]
    assert "peak_x" in vis["salient_region_summary"]

    # Decode and verify valid PNG bytes
    b64_data = vis["heatmap_overlay_base64"].split(",")[1]
    raw_png = base64.b64decode(b64_data)
    with Image.open(io.BytesIO(raw_png)) as img:
        assert img.size == (224, 224)


# ==============================================================================
# 2. MODEL STATUS ENDPOINT TESTS
# ==============================================================================


def test_retina_model_status_endpoint(client: TestClient):
    """Verify GET /api/v1/retina/model-status reports readiness, device, and verified checkpoint metadata."""
    response = client.get("/api/v1/retina/model-status")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["ready", "unloaded"]
    assert "is_loaded" in data
    assert data["num_classes"] == 5
    assert len(data["classes"]) == 5
    assert data["gradcam_supported"] is True
    if data["is_loaded"]:
        assert data["checkpoint_filename"] == "retinaguard_v2.pt"
        assert data["model_version"] == "retinaguard_v2_epoch8"
        assert data["checkpoint_epoch"] == 8
        assert data["checkpoint_val_macro_f1"] == 0.6931
        assert data["selection_source"] == "v2_preferred"


# ==============================================================================
# 3. RETINAGUARD PREDICT ENDPOINT TESTS (REAL / INTEGRATION)
# ==============================================================================


def test_retina_predict_success(client: TestClient, create_sample_image, db_session):
    """Verify POST /api/v1/retina/predict returns full classification and Grad-CAM."""
    img_bytes = create_sample_image(format="JPEG", size=(300, 300))
    files = {"file": ("patient_fundus.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/v1/retina/predict?include_gradcam=true", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["modality"] == "retina"
    assert "session_id" in data
    assert "model_version" in data
    assert "RESEARCH PROTOTYPE ONLY" in data["disclaimer"]

    # Prediction validation
    pred = data["prediction"]
    assert pred["predicted_class"] in [0, 1, 2, 3, 4]
    assert pred["class_label"] in DR_CLASS_NAMES.values()
    assert pred["severity_level"] in ["None", "Mild", "Moderate", "Severe", "Proliferative"]
    assert 0.0 <= pred["confidence_score"] <= 1.0
    assert len(pred["all_class_scores"]) == 5
    assert "uncalibrated" in pred["calibration_notice"].lower()

    # Verify Grad-CAM explanation presence
    expl = data["explanation"]
    assert expl is not None
    assert expl["target_class"] == pred["predicted_class"]
    assert expl["heatmap_overlay_base64"].startswith("data:image/png;base64,")
    assert expl["raw_heatmap_base64"].startswith("data:image/png;base64,")
    assert "attention, NOT verified medical pathology" in expl["interpretability_note"]
    assert expl["salient_region_summary"]["peak_intensity"] == 1.0

    # Verify audit session record in DB (zero disk storage compliance)
    session_record = db_session.query(AnalysisSession).filter_by(session_id=data["session_id"]).first()
    assert session_record is not None
    assert session_record.modality == "retina"
    assert session_record.status == "SUCCESS"
    assert session_record.prediction_category == pred["class_label"]
    assert session_record.explanation_heatmap_path is None  # Zero-disk persistence rule


def test_retina_predict_without_gradcam(client: TestClient, create_sample_image):
    """Verify POST /api/v1/retina/predict with include_gradcam=false omits explanation."""
    img_bytes = create_sample_image(format="PNG", size=(256, 256))
    files = {"file": ("fundus_nogradcam.png", img_bytes, "image/png")}

    response = client.post("/api/v1/retina/predict?include_gradcam=false", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["prediction"] is not None
    assert data["explanation"] is None


def test_retina_predict_route_alias(client: TestClient, create_sample_image):
    """Verify POST /api/retina/predict works as alias to /api/v1/retina/predict."""
    img_bytes = create_sample_image(format="JPEG", size=(224, 224))
    files = {"file": ("alias_test.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/retina/predict", files=files)
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"


# ==============================================================================
# 4. ERROR HANDLING & VALIDATION REJECTIONS
# ==============================================================================


def test_retina_predict_reject_empty_file(client: TestClient):
    """Verify empty file upload returns 400 Bad Request."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/retina/predict", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_retina_predict_reject_corrupted_file(client: TestClient):
    """Verify corrupted bytes return 400 Bad Request."""
    files = {"file": ("corrupt.png", b"NotARealPNGFileHeader12345", "image/png")}
    response = client.post("/api/v1/retina/predict", files=files)
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "corrupted" in detail or "decoded" in detail


def test_retina_predict_reject_unsupported_extension(client: TestClient):
    """Verify non-image format returns 415 Unsupported Media Type."""
    files = {"file": ("report.pdf", b"%PDF-1.4 dummy", "application/pdf")}
    response = client.post("/api/v1/retina/predict", files=files)
    assert response.status_code == 415
    assert "unsupported file extension" in response.json()["detail"].lower()
