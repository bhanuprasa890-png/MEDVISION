"""Tests for file validation security rules and error codes."""

import io
from fastapi.testclient import TestClient


def test_reject_empty_file(client: TestClient):
    """Uploading an empty file should return 400 Bad Request."""
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_reject_unsupported_file_extension(client: TestClient):
    """Uploading a disallowed extension (e.g., .pdf) should return 415."""
    files = {"file": ("document.pdf", b"%PDF-1.5 fake content", "application/pdf")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 415
    assert "unsupported" in response.json()["detail"].lower()


def test_reject_corrupted_image(client: TestClient):
    """Uploading bytes with image/jpeg mime but corrupt payload should return 400."""
    files = {"file": ("corrupt.jpg", b"NOT_A_REAL_IMAGE_DATA_BYTES", "image/jpeg")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()


def test_accept_valid_image(client: TestClient, create_sample_image):
    """Valid JPEG should be successfully accepted and parsed."""
    img_bytes = create_sample_image(format="JPEG", size=(320, 240))
    files = {"file": ("test_retina.jpg", img_bytes, "image/jpeg")}
    response = client.post("/api/v1/retina/analyze", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["file_name"] == "test_retina.jpg"
    assert data["metadata"]["image_width"] == 320
    assert data["metadata"]["image_height"] == 240
    assert len(data["metadata"]["file_hash"]) == 64  # Valid SHA-256 length
