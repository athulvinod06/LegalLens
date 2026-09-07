"""
Tests for service health-check endpoint.
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health check endpoint returns 200 and mandatory fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "LegalLens"
    assert "disclaimer" in data


def test_api_health_check_alias():
    """Verify /api/health alias returns 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
