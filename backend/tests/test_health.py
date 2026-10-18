from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
client=TestClient(app)

def test_health_check():
    response=client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() =={
        "status":"ok",
        "service":"ai-support-agent",
        "database":"ok",
    }


def test_health_reports_database_failure_as_unavailable():
    with patch("app.routers.health.engine.connect", side_effect=RuntimeError("offline")):
        response = client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
