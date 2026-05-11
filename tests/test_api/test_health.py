"""Tests for API health endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


class TestAPIHealth:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"

    def test_evaluate_empty(self):
        response = client.post("/api/v1/evaluate", json={})
        assert response.status_code == 400

    def test_evaluate_invalid(self):
        response = client.post("/api/v1/evaluate", json={
            "biomarkers": {"age": 200, "albumin": 43}
        })
        assert response.status_code == 422
