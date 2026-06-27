import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-test.sqlite3"
if TEST_DATABASE_PATH.exists():
    TEST_DATABASE_PATH.unlink()

os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import initialize_database  # noqa: E402
from app.main import app  # noqa: E402

initialize_database()

client = TestClient(app)


def test_root_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "kairos-api",
        "version": "0.3.0",
    }


def test_api_v1_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "kairos-api",
        "version": "0.3.0",
    }


def test_health_allows_dashboard_origin():
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_database_initialization_seeds_default_data():
    assert TEST_DATABASE_PATH.exists()

    projects = client.get("/api/v1/projects")
    tasks = client.get("/api/v1/tasks")
    memories = client.get("/api/v1/memories")

    assert projects.status_code == 200
    assert tasks.status_code == 200
    assert memories.status_code == 200

    assert any(project["name"] == "Kairos OS" for project in projects.json())
    assert any(task["title"] == "Connect Kairos Dashboard to the Core API" for task in tasks.json())
    assert any(memory["type"] == "technical_context" for memory in memories.json())

    project_count = len(projects.json())
    task_count = len(tasks.json())
    memory_count = len(memories.json())

    initialize_database()

    assert len(client.get("/api/v1/projects").json()) == project_count
    assert len(client.get("/api/v1/tasks").json()) == task_count
    assert len(client.get("/api/v1/memories").json()) == memory_count


def test_dashboard_read_endpoints_return_sqlite_data():
    created_project = client.post(
        "/api/v1/projects",
        json={
            "name": "SQLite Project",
            "description": "Created during API tests.",
            "priority": "high",
        },
    )
    assert created_project.status_code == 201
    project_id = created_project.json()["id"]

    created_task = client.post(
        "/api/v1/tasks",
        json={
            "project_id": project_id,
            "title": "Persist task in SQLite",
            "priority": "medium",
        },
    )
    assert created_task.status_code == 201

    created_memory = client.post(
        "/api/v1/memories",
        json={
            "type": "technical_context",
            "content": "Kairos API v0.3 stores local records in SQLite.",
            "tags": ["kairos", "sqlite"],
        },
    )
    assert created_memory.status_code == 201

    projects = client.get("/api/v1/projects")
    tasks = client.get("/api/v1/tasks")
    memories = client.get("/api/v1/memories")

    assert projects.status_code == 200
    assert any(project["name"] == "SQLite Project" for project in projects.json())

    assert tasks.status_code == 200
    assert any(task["title"] == "Persist task in SQLite" for task in tasks.json())

    assert memories.status_code == 200
    assert any(memory["type"] == "technical_context" for memory in memories.json())


def test_sqlite_project_crud_is_consistent():
    created = client.post(
        "/api/v1/projects",
        json={
            "name": "SQLite CRUD Project",
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


def test_sqlite_task_crud_is_consistent():
    created = client.post(
        "/api/v1/tasks",
        json={
            "title": "SQLite CRUD Task",
            "description": "Created during API tests.",
            "priority": "medium",
        },
    )

    assert created.status_code == 201
    task_id = created.json()["id"]

    listed = client.get("/api/v1/tasks")
    assert any(task["id"] == task_id for task in listed.json())

    updated = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "done", "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["priority"] == "low"

    deleted = client.delete(f"/api/v1/tasks/{task_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/tasks/{task_id}")
    assert missing.status_code == 404


def test_sqlite_memory_crud_is_consistent():
    created = client.post(
        "/api/v1/memories",
        json={
            "type": "note",
            "content": "SQLite CRUD memory.",
            "tags": ["sqlite", "test"],
            "importance": "normal",
        },
    )

    assert created.status_code == 201
    memory_id = created.json()["id"]

    listed = client.get("/api/v1/memories")
    assert any(memory["id"] == memory_id for memory in listed.json())

    updated = client.patch(
        f"/api/v1/memories/{memory_id}",
        json={"importance": "high", "tags": ["sqlite", "updated"]},
    )
    assert updated.status_code == 200
    assert updated.json()["importance"] == "high"
    assert updated.json()["tags"] == ["sqlite", "updated"]

    deleted = client.delete(f"/api/v1/memories/{memory_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/memories/{memory_id}")
    assert missing.status_code == 404
