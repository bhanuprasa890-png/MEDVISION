"""Tests for the Chest X-Ray analysis placeholder endpoint."""

from fastapi.testclient import TestClient


def test_chest_xray_analysis_placeholder_contract(client: TestClient, create_sample_image):
    """Ensure POST /api/v1/chest-xray/analyze returns honest placeholder fields."""
    img_bytes = create_sample_image(format="PNG", size=(512, 512))
    files = {"file": ("cxr_sample.png", img_bytes, "image/png")}

    response = client.post("/api/v1/chest-xray/analyze", files=files)
    assert response.status_code == 200

    data = response.json()
    # Contract validation
    assert data["modality"] == "chest_xray"
    assert data["status"] == "DEVELOPMENT_PLACEHOLDER"
    assert "not implemented yet" in data["message"].lower()

    # CRITICAL: Prediction and explanation MUST be null/None
    assert data["prediction"] is None
    assert data["explanation"] is None

    # Mandatory medical disclaimer presence
    assert "RESEARCH ONLY" in data["disclaimer"]
    assert "session_id" in data
    assert "created_at" in data


def test_chest_xray_transparent_png_support(client: TestClient):
    """Verify PNG with alpha transparency channel is accepted and technical metadata recorded."""
    import io
    from PIL import Image

    buf = io.BytesIO()
    # Create RGBA image with transparent background (alpha = 0)
    img = Image.new("RGBA", (400, 500), (0, 0, 0, 0))
    for x in range(100, 300):
        for y in range(100, 400):
            img.putpixel((x, y), (200, 200, 200, 255))
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    response = client.post(
        "/api/v1/chest-xray/analyze",
        files={"file": ("segmented_cxr.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["mime_type"] == "image/png"
    assert data["metadata"]["image_width"] == 400
    assert data["metadata"]["image_height"] == 500
    assert data["status"] == "DEVELOPMENT_PLACEHOLDER"
    assert data["prediction"] is None


def test_chest_xray_portrait_aspect_ratio_scan(client: TestClient, create_sample_image):
    """Verify portrait radiograph aspect ratio (e.g., 512x768) is parsed accurately."""
    portrait_bytes = create_sample_image(format="JPEG", size=(512, 768))
    response = client.post(
        "/api/v1/chest-xray/analyze",
        files={"file": ("portrait_cxr.jpg", portrait_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["image_width"] == 512
    assert data["metadata"]["image_height"] == 768
    assert data["status"] == "DEVELOPMENT_PLACEHOLDER"

