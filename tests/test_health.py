"""Tests for the health-check endpoint."""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Test GET /api/health returns 200 with status=healthy and expected keys."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data
    assert data["environment"] == "development"


def test_root_endpoint(client: TestClient):
    """Test root endpoint provides service overview and disclaimer."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "RESEARCH USE ONLY" in data["disclaimer"]
