"""Tests for the Retina analysis placeholder endpoint."""

from fastapi.testclient import TestClient


def test_retina_analysis_placeholder_contract(client: TestClient, create_sample_image):
    """Ensure POST /api/v1/retina/analyze returns honest placeholder fields."""
    img_bytes = create_sample_image(format="JPEG", size=(512, 512))
    files = {"file": ("fundus_sample.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 200

    data = response.json()
    # Contract validation
    assert data["modality"] == "retina"
    assert data["status"] == "DEVELOPMENT_PLACEHOLDER"
    assert "not implemented yet" in data["message"].lower()

    # CRITICAL: Prediction and explanation MUST be null/None
    assert data["prediction"] is None
    assert data["explanation"] is None

    # Mandatory medical disclaimer presence
    assert "RESEARCH ONLY" in data["disclaimer"]
    assert "session_id" in data
    assert "created_at" in data
