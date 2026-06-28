import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-plugins-test.sqlite3"
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings, Settings  # noqa: E402

client = TestClient(app)


def test_list_plugins():
    response = client.get("/api/v1/plugins")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    ids = [p["id"] for p in data]
    assert "core.projects" in ids
    assert "core.tasks" in ids
    assert "core.memories" in ids
    assert "core.operations" in ids


def test_get_plugin_by_id():
    response = client.get("/api/v1/plugins/core.tasks")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "core.tasks"
    assert data["name"] == "Core Tasks Extension"
    assert "task_management" in data["capabilities"]


def test_get_unknown_plugin_returns_404():
    response = client.get("/api/v1/plugins/unknown.plugin")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_plugins_disabled_behavior():
    def override_settings():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_PLUGINS_ENABLED=False,
        )

    app.dependency_overrides[get_settings] = override_settings
    try:
        # Verify list returns empty
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200
        assert response.json() == []

        # Verify get by ID returns 404
        response = client.get("/api/v1/plugins/core.tasks")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
