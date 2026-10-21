"""Comprehensive tests for genuine Chest X-Ray (CXR) inference pipeline, Grad-CAM, and audit integrity."""

import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from app.db.models import AnalysisSession
from app.services.chest_xray_service import get_chest_xray_service


def _create_sample_cxr_image(size=(300, 300), format="PNG", mode="L", fill=128) -> bytes:
    """Helper to generate in-memory synthetic radiograph bytes with anatomical gradient."""
    buf = io.BytesIO()
    img = Image.new(mode, size, color=fill)
    # Add a slight intensity gradient to emulate radiograph density variations
    if mode == "L":
        for x in range(size[0]):
            for y in range(size[1]):
                val = int((x / size[0]) * 100 + (y / size[1]) * 100)
                img.putpixel((x, y), val)
    img.save(buf, format=format)
    return buf.getvalue()


class TestChestXrayModelStatus:
    """Verifies GET /api/v1/chest-xray/model-status endpoint."""

    def test_model_status_returns_loaded_and_verified_metadata(self, client: TestClient):
        response = client.get("/api/v1/chest-xray/model-status")
        assert response.status_code == 200
        data = response.json()

        assert data["model_name"] == "DenseNet-121"
        assert "TorchXRayVision" in data["model_version"]
        assert data["status"] == "LOADED"
        assert data["pathologies_count"] == 18
        assert data["checkpoint_hash"] == "56524913dd16a906422e8d8b66a7a5c46be1d82eb7ac012d8103776f1aa68899"
        assert "RESEARCH ONLY" in data["disclaimer"]

        expected_pathologies = [
            "Atelectasis", "Consolidation", "Infiltration", "Pneumothorax",
            "Edema", "Emphysema", "Fibrosis", "Effusion",
            "Pneumonia", "Pleural_Thickening", "Cardiomegaly", "Nodule",
            "Mass", "Hernia", "Lung Lesion", "Fracture",
            "Lung Opacity", "Enlarged Cardiomediastinum"
        ]
        assert data["pathologies"] == expected_pathologies


class TestChestXrayPredictionPipeline:
    """Verifies POST /api/v1/chest-xray/predict endpoint and audit persistence."""

    def test_predict_success_with_gradcam_and_audit_persistence(self, client: TestClient, db_session):
        img_bytes = _create_sample_cxr_image(size=(256, 256), format="PNG")
        files = {"file": ("radiograph_sample.png", img_bytes, "image/png")}

        response = client.post("/api/v1/chest-xray/predict?include_gradcam=true", files=files)
        assert response.status_code == 200
        data = response.json()

        # Contract checks
        assert data["modality"] == "chest_xray"
        assert data["status"] == "SUCCESS"
        assert "session_id" in data
        assert "created_at" in data
        assert "DenseNet-121" in data["model_version"]
        assert "RESEARCH ONLY" in data["disclaimer"]

        # Technical metadata
        assert data["metadata"]["file_name"] == "radiograph_sample.png"
        assert data["metadata"]["mime_type"] == "image/png"
        assert data["metadata"]["image_width"] == 256
        assert data["metadata"]["image_height"] == 256
        assert len(data["metadata"]["file_hash"]) == 64

        # Prediction details
        pred = data["prediction"]
        assert isinstance(pred["top_finding"], str)
        assert 0.0 <= pred["top_score"] <= 1.0
        assert len(pred["findings"]) == 18
        for path_name, score in pred["findings"].items():
            assert 0.0 <= score <= 1.0
        assert "uncalibrated sigmoid" in pred["calibration_notice"].lower()
        assert len(pred["clinical_description"]) > 10

        # Grad-CAM explanation details
        exp = data["explanation"]
        assert exp is not None
        assert exp["target_pathology"] == pred["top_finding"]
        assert exp["target_layer"] == "denseblock4"
        assert exp["resolution"] == [224, 224]
        assert exp["heatmap_overlay_base64"].startswith("data:image/png;base64,")
        assert exp["raw_heatmap_base64"].startswith("data:image/png;base64,")
        assert "salient_region_summary" in exp
        salient = exp["salient_region_summary"]
        assert 0 <= salient["peak_x"] < 224
        assert 0 <= salient["peak_y"] < 224
        assert 0.0 <= salient["peak_intensity"] <= 1.0
        assert "machine attention" in exp["interpretability_note"].lower()

        # Verify DB audit persistence
        record = db_session.query(AnalysisSession).filter_by(session_id=data["session_id"]).first()
        assert record is not None
        assert record.modality == "chest_xray"
        assert record.status == "SUCCESS"
        assert record.prediction_category == pred["top_finding"]
        assert record.prediction_confidence == pred["top_score"]
        assert record.file_hash == data["metadata"]["file_hash"]

    def test_predict_without_gradcam(self, client: TestClient):
        img_bytes = _create_sample_cxr_image(size=(224, 224), format="JPEG")
        files = {"file": ("chest_scan.jpg", img_bytes, "image/jpeg")}

        response = client.post("/api/v1/chest-xray/predict?include_gradcam=false", files=files)
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "SUCCESS"
        assert data["prediction"] is not None
        assert data["explanation"] is None

    def test_predict_transparent_png_radiograph(self, client: TestClient):
        """Ensures RGBA images with transparency are composited onto black background without crashing."""
        buf = io.BytesIO()
        rgba_img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        for x in range(50, 150):
            for y in range(50, 150):
                rgba_img.putpixel((x, y), (200, 200, 200, 255))
        rgba_img.save(buf, format="PNG")

        response = client.post(
            "/api/v1/chest-xray/predict",
            files={"file": ("alpha_cxr.png", buf.getvalue(), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["metadata"]["mime_type"] == "image/png"


class TestChestXrayValidationAndErrors:
    """Verifies edge cases, invalid payloads, and security rejections."""

    def test_reject_corrupted_image(self, client: TestClient):
        corrupted_bytes = b"NotAValidChestXrayFileCorruptData"
        response = client.post(
            "/api/v1/chest-xray/predict",
            files={"file": ("broken.png", corrupted_bytes, "image/png")},
        )
        assert response.status_code == 400
        assert "corrupted" in response.json()["detail"].lower()

    def test_reject_unsupported_extension(self, client: TestClient):
        response = client.post(
            "/api/v1/chest-xray/predict",
            files={"file": ("scan.pdf", b"%PDF-1.4...", "application/pdf")},
        )
        assert response.status_code == 415
        assert "unsupported file extension" in response.json()["detail"].lower()

    def test_reject_oversized_file(self, client: TestClient):
        huge_bytes = b"0" * (10 * 1024 * 1024 + 10)
        response = client.post(
            "/api/v1/chest-xray/predict",
            files={"file": ("huge.png", huge_bytes, "image/png")},
        )
        assert response.status_code == 413
        assert "exceeds" in response.json()["detail"].lower()

    def test_medassist_scan_context_safely_rejects_chest_xray(self, client: TestClient):
        """Verifies that client cannot inject unverified chest_xray scan context into MedAssist."""
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "Explain my chest x-ray findings",
                "scan_context": {
                    "modality": "chest_xray",
                },
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "Chest X-ray scan context is not currently supported" in str(data)

    def test_medassist_general_chat_answers_chest_xray_queries(self, client: TestClient):
        """Verifies that MedAssist answers general questions about chest x-ray educationally."""
        from unittest.mock import AsyncMock, patch
        import httpx

        mock_reply = httpx.Response(
            status_code=200,
            json={
                "candidates": [{
                    "content": {
                        "parts": [{"text": "Cardiomegaly refers to an enlarged cardiac silhouette on a chest radiograph."}]
                    },
                    "finishReason": "STOP",
                }]
            },
            request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
        )

        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_reply)):
            response = client.post(
                "/api/v1/chat/message",
                json={
                    "message": "What does cardiomegaly mean on a chest radiograph?",
                    "language": "en",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "Cardiomegaly" in data["message"]
            assert "EDUCATIONAL RESEARCH USE ONLY" in data["disclaimer"]
