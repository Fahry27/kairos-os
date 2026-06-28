import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-monitoring-test.sqlite3"
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.monitoring import metrics_tracker  # noqa: E402


def test_ready_endpoint():
    # Use context manager to trigger FastAPI startup lifespan checks
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        res_data = response.json()
        assert res_data["status"] == "ready"
        assert "database" in res_data
        assert "checks" in res_data
        assert res_data["checks"].get("sqlite_writable") is True

        # Check api v1 endpoint
        response = client.get("/api/v1/ready")
        assert response.status_code == 200


def test_metrics_endpoint():
    with TestClient(app) as client:
        metrics_tracker.clear()

        # Make request to generate HTTP request metrics
        client.get("/health")
        client.get("/health")

        response = client.get("/metrics")
        assert response.status_code == 200
        res_data = response.json()
        assert "uptime_seconds" in res_data
        assert "database_status" in res_data
        assert "docker_mode" in res_data
        assert "http_requests_total" in res_data
        assert "http_response_status_codes" in res_data

        # Total requests: /health, /health, /metrics (the current request is active)
        assert res_data["http_requests_total"] >= 3
        # Response codes: Only the previous 2 requests have returned their status code so far
        assert res_data["http_response_status_codes"]["2xx"] >= 2

        # Check api v1 endpoint
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
