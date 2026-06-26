import os

os.environ["CREATE_TABLES_ON_STARTUP"] = "false"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "kairos-api",
        "version": "0.1.0",
    }


def test_api_v1_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "kairos-api",
        "version": "0.1.0",
    }
