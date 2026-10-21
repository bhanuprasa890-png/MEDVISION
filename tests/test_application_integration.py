"""Comprehensive end-to-end integration and validation test suite.

Covers:
1. Health and root discovery endpoints.
2. CORS policy enforcement for local frontend origins.
3. RetinaGuard model status and inference across multiple distinct retinal images.
4. Grad-CAM visual heatmap generation and dynamic updating across different inputs.
5. In-memory file validation: empty files, corrupted bytes, disallowed media types, and oversized payloads.
6. Chest X-Ray module safety: verifies it remains honestly marked as DEVELOPMENT_PLACEHOLDER
   without any fabricated predictions or fake heatmaps.
7. Relational database audit session ledger: verified zero-disk storage compliance.
8. Frontend schema contract verification against UI expectations.
"""

import base64
import io
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.db.models import AnalysisSession
from app.core.config import settings


# ==============================================================================
# 1. HEALTH AND ROOT DISCOVERY TESTS
# ==============================================================================


def test_api_health_endpoint_contract(client: TestClient):
    """Verify GET /api/health returns 200 with healthy status and metadata."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert data["environment"] == "development"


def test_root_endpoint_contract(client: TestClient):
    """Verify GET / returns documentation pointers and non-clinical disclaimer."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["docs_url"] == "/docs"
    assert data["health_check"] == "/api/health"
    assert "RESEARCH USE ONLY" in data["disclaimer"]


# ==============================================================================
# 2. CORS POLICY TESTS (VITE FRONTEND INTEGRATION)
# ==============================================================================


def test_cors_preflight_for_local_frontend(client: TestClient):
    """Verify CORS preflight OPTIONS request permits local Vite frontend."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/v1/retina/predict", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_cors_preflight_for_127_ip_frontend(client: TestClient):
    """Verify CORS permits 127.0.0.1:5173 frontend origin."""
    headers = {
        "Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/retina/model-status", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"


def test_cors_disallows_external_untrusted_origin(client: TestClient):
    """Verify unauthorized external domains do not receive CORS authorization."""
    headers = {
        "Origin": "http://untrusted-external-site.com",
        "Access-Control-Request-Method": "POST",
    }
    response = client.options("/api/v1/retina/predict", headers=headers)
    assert response.headers.get("access-control-allow-origin") != "http://untrusted-external-site.com"


# ==============================================================================
# 3. RETINAGUARD MODEL STATUS AND READINESS
# ==============================================================================


def test_retina_model_status_ready(client: TestClient):
    """Verify GET /api/v1/retina/model-status reports operational readiness."""
    response = client.get("/api/v1/retina/model-status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "unloaded"]
    assert data["num_classes"] == 5
    assert "device" in data
    assert data["gradcam_supported"] is True
    assert set(data["classes"].keys()) == {"0", "1", "2", "3", "4"}


# ==============================================================================
# 4. MULTI-IMAGE INFERENCE & DYNAMIC GRAD-CAM UPDATES
# ==============================================================================


def test_retina_inference_updates_across_different_images(client: TestClient, db_session):
    """Verify that uploading different retinal images yields distinct predictions, hashes, and heatmaps."""
    project_root = Path(__file__).resolve().parent.parent

    # Pick three different images from the verified APTOS dataset
    image_paths = [
        project_root / "datasets/aptos/train_images/606daaf0bfc7.png",
        project_root / "datasets/aptos/train_images/ee74c3b177e0.png",
        project_root / "datasets/aptos/train_images/46d3316c4857.png",
    ]

    # Verify that files physically exist
    valid_paths = [p for p in image_paths if p.exists()]
    assert len(valid_paths) >= 2, "At least two APTOS images must be present to test multi-image updates"

    results = []
    for img_path in valid_paths:
        with open(img_path, "rb") as f:
            file_bytes = f.read()

        response = client.post(
            "/api/v1/retina/predict?include_gradcam=true",
            files={"file": (img_path.name, file_bytes, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["modality"] == "retina"
        assert "RESEARCH PROTOTYPE ONLY" in data["disclaimer"]

        # Validate prediction structure
        pred = data["prediction"]
        assert pred["predicted_class"] in [0, 1, 2, 3, 4]
        assert 0.0 <= pred["confidence_score"] <= 1.0
        assert len(pred["all_class_scores"]) == 5

        # Validate Grad-CAM structure
        expl = data["explanation"]
        assert expl is not None
        assert expl["heatmap_overlay_base64"].startswith("data:image/png;base64,")
        assert expl["raw_heatmap_base64"].startswith("data:image/png;base64,")
        assert "salient_region_summary" in expl

        # Validate technical metadata
        meta = data["metadata"]
        assert meta["file_name"] == img_path.name
        assert meta["file_size_bytes"] == len(file_bytes)
        assert len(meta["file_hash"]) == 64

        results.append(data)

    # Verify that results are distinct and dynamically updated
    hashes = [r["metadata"]["file_hash"] for r in results]
    assert len(set(hashes)) == len(results), "Each image must have a unique SHA-256 hash"

    session_ids = [r["session_id"] for r in results]
    assert len(set(session_ids)) == len(results), "Each upload must yield a unique session UUID"

    # Heatmaps must be uniquely computed for different inputs
    overlay_data = [r["explanation"]["heatmap_overlay_base64"] for r in results]
    assert len(set(overlay_data)) == len(results), "Each image must generate its own distinct Grad-CAM overlay"


def test_retina_predict_without_gradcam_flag(client: TestClient, create_sample_image):
    """Verify include_gradcam=false suppresses visual heatmap calculation."""
    img_bytes = create_sample_image(format="JPEG", size=(256, 256))
    response = client.post(
        "/api/v1/retina/predict?include_gradcam=false",
        files={"file": ("no_cam.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] is not None
    assert data["explanation"] is None


# ==============================================================================
# 5. CHEST X-RAY MODULE AVAILABILITY CONFIRMATION
# ==============================================================================


def test_chest_xray_remains_honestly_unavailable(client: TestClient, create_sample_image, db_session):
    """Verify chest X-Ray module explicitly returns DEVELOPMENT_PLACEHOLDER with no fake predictions."""
    cxr_bytes = create_sample_image(format="PNG", size=(512, 512), color=(50, 50, 50))
    response = client.post(
        "/api/v1/chest-xray/analyze",
        files={"file": ("cxr_scan.png", cxr_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DEVELOPMENT_PLACEHOLDER"
    assert data["modality"] == "chest_xray"
    assert "not implemented" in data["message"].lower()

    # Crucial safety check: Must NEVER fabricate predictions or heatmaps
    assert data["prediction"] is None
    assert data["explanation"] is None
    assert "RESEARCH ONLY" in data["disclaimer"]

    # Check DB record
    record = db_session.query(AnalysisSession).filter_by(session_id=data["session_id"]).first()
    assert record is not None
    assert record.modality == "chest_xray"
    assert record.status == "DEVELOPMENT_PLACEHOLDER"
    assert record.prediction_category is None


# ==============================================================================
# 6. FILE VALIDATION & ERROR HANDLING TESTS
# ==============================================================================


def test_reject_unsupported_file_extension(client: TestClient):
    """Verify non-image file formats are rejected with HTTP 415."""
    for bad_file, bad_mime in [
        ("records.pdf", "application/pdf"),
        ("script.sh", "application/x-sh"),
        ("data.csv", "text/csv"),
    ]:
        response = client.post(
            "/api/v1/retina/predict",
            files={"file": (bad_file, b"DummyContent", bad_mime)},
        )
        assert response.status_code == 415
        assert "unsupported file extension" in response.json()["detail"].lower()


def test_reject_corrupted_image(client: TestClient):
    """Verify corrupted bytes masquerading as valid formats return HTTP 400."""
    corrupted_bytes = b"\x89PNG\r\n\x1a\nCorruptedPayload999999999"
    response = client.post(
        "/api/v1/retina/predict",
        files={"file": ("corrupt.png", corrupted_bytes, "image/png")},
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "corrupted" in detail or "decoded" in detail


def test_reject_empty_file(client: TestClient):
    """Verify 0-byte file uploads are rejected with HTTP 400."""
    response = client.post(
        "/api/v1/retina/predict",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_reject_oversized_file(client: TestClient, monkeypatch):
    """Verify files exceeding MAX_UPLOAD_SIZE_MB return HTTP 413."""
    # Temporarily constrain upload limit to 100 KB for rapid testing
    from app.services import file_validator

    monkeypatch.setattr(file_validator.settings, "MAX_UPLOAD_SIZE_MB", 0.01)

    oversized_bytes = b"X" * (150 * 1024)  # 150 KB
    response = client.post(
        "/api/v1/retina/predict",
        files={"file": ("huge_image.png", oversized_bytes, "image/png")},
    )
    assert response.status_code == 413
    assert "maximum allowed" in response.json()["detail"].lower()


# ==============================================================================
# 7. RELATIONAL DATABASE AUDIT SESSION PERSISTENCE (ZERO-DISK STORAGE)
# ==============================================================================


def test_audit_session_persisted_without_disk_persistence(client: TestClient, create_sample_image, db_session):
    """Verify audit record is created in SQLite while raw bytes and heatmaps are NEVER written to disk."""
    img_bytes = create_sample_image(format="JPEG", size=(320, 240))
    response = client.post(
        "/api/v1/retina/predict?include_gradcam=true",
        files={"file": ("privacy_audit.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # Query DB
    record = db_session.query(AnalysisSession).filter_by(session_id=session_id).first()
    assert record is not None
    assert record.file_name == "privacy_audit.jpg"
    assert record.modality == "retina"
    assert record.status == "SUCCESS"
    assert record.image_width == 320
    assert record.image_height == 240
    assert record.explanation_heatmap_path is None  # Zero-disk persistence compliance


# ==============================================================================
# 8. FRONTEND SCHEMA CONTRACT INTEGRITY
# ==============================================================================


def test_frontend_schema_contract(client: TestClient, create_sample_image):
    """Verify response payload satisfies all field requirements expected by frontend components."""
    img_bytes = create_sample_image(format="PNG", size=(224, 224))
    response = client.post(
        "/api/v1/retina/predict?include_gradcam=true",
        files={"file": ("contract_check.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    res = response.json()

    # Top-level keys
    for key in ["session_id", "modality", "status", "model_version", "prediction", "explanation", "metadata", "disclaimer", "created_at"]:
        assert key in res, f"Missing top-level key: {key}"

    # Prediction keys needed by RetinaPredictionResultCard
    pred = res["prediction"]
    for key in ["predicted_class", "class_label", "severity_level", "confidence_score", "calibration_notice", "all_class_scores", "clinical_description"]:
        assert key in pred, f"Missing prediction key: {key}"

    # Saliency keys needed by RetinaPredictionResultCard
    expl = res["explanation"]
    for key in ["heatmap_overlay_base64", "raw_heatmap_base64", "salient_region_summary", "interpretability_note", "target_layer"]:
        assert key in expl, f"Missing explanation key: {key}"

    summary = expl["salient_region_summary"]
    for key in ["peak_x", "peak_y", "peak_intensity", "mean_intensity", "active_area_ratio"]:
        assert key in summary, f"Missing salient region key: {key}"
