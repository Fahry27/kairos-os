import os

os.environ["CREATE_TABLES_ON_STARTUP"] = "false"
os.environ["USE_MOCK_DATA"] = "true"

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


def test_health_allows_dashboard_origin():
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_dashboard_read_endpoints_return_mock_data():
    projects = client.get("/api/v1/projects")
    tasks = client.get("/api/v1/tasks")
    memories = client.get("/api/v1/memories")

    assert projects.status_code == 200
    assert projects.json()[0]["name"] == "Kairos OS"

    assert tasks.status_code == 200
    assert tasks.json()[0]["title"] == "Connect Kairos Dashboard to the Core API"

    assert memories.status_code == 200
    assert memories.json()[0]["type"] == "technical_context"


def test_mock_project_crud_is_consistent():
    created = client.post(
        "/api/v1/projects",
        json={
            "name": "Mock CRUD Project",
            "description": "Created during API tests.",
            "priority": "medium",
        },
    )

    assert created.status_code == 201
    project_id = created.json()["id"]

    listed = client.get("/api/v1/projects")
    assert any(project["id"] == project_id for project in listed.json())

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"status": "paused", "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "paused"
    assert updated.json()["priority"] == "low"

    deleted = client.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/projects/{project_id}")
    assert missing.status_code == 404
