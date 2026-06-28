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
from app.core.plugins import plugin_registry  # noqa: E402

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


def test_commands_endpoints():
    # Verify GET /commands returns built-in commands
    response = client.get("/api/v1/commands")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 8

    c_ids = [c["id"] for c in data]
    assert "core.projects.create_project" in c_ids
    assert "core.tasks.create_task" in c_ids
    assert "core.operations.run_backup" in c_ids

    # Verify run_backup is dangerous
    backup_cmd = next(c for c in data if c["id"] == "core.operations.run_backup")
    assert backup_cmd["dangerous"] is True

    # Verify GET /commands/{command_id} works
    response = client.get("/api/v1/commands/core.projects.create_project")
    assert response.status_code == 200
    cmd_data = response.json()
    assert cmd_data["name"] == "Create Project"

    # Unknown command returns 404
    response = client.get("/api/v1/commands/unknown.command")
    assert response.status_code == 404


def test_external_plugin_scanner_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Valid External Manifest
        valid_json = """{
            "id": "custom.weather",
            "name": "Custom Weather Extension",
            "version": "1.0.0",
            "description": "Fetches local weather reports.",
            "category": "utility",
            "entry_ref": "custom/weather",
            "commands": [
                {
                    "id": "custom.weather.get_report",
                    "plugin_id": "custom.weather",
                    "name": "Get Weather Report",
                    "description": "Exposes readings.",
                    "category": "read"
                }
            ]
        }"""
        (tmp_path / "weather.json").write_text(valid_json, encoding="utf-8")

        # 2. Invalid Manifest (Malformed JSON)
        (tmp_path / "invalid.json").write_text("{invalid-json}", encoding="utf-8")

        # 3. Duplicate Built-in ID Manifest
        duplicate_json = """{
            "id": "core.tasks",
            "name": "Duplicate Core Tasks",
            "version": "1.0.0",
            "description": "Duplicate tasks description.",
            "category": "core",
            "entry_ref": "custom/tasks"
        }"""
        (tmp_path / "duplicate.json").write_text(duplicate_json, encoding="utf-8")

        # Load external plugins into registry
        plugin_registry.load_external_plugins(tmp_path)

        try:
            # Override settings to point KAIROS_PLUGINS_DIR to our temp directory
            def override_settings():
                return Settings(
                    APP_ENV="test",
                    DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
                    KAIROS_PLUGINS_DIR=str(tmp_path),
                )

            app.dependency_overrides[get_settings] = override_settings

            # Verify list contains both built-in and our loaded custom plugin
            response = client.get("/api/v1/plugins")
            assert response.status_code == 200
            data = response.json()
            ids = [p["id"] for p in data]
            assert "custom.weather" in ids
            assert "core.tasks" in ids  # built-in remains unchanged

            # Verify built-in metadata is NOT overwritten by duplicates
            tasks_plugin = next(p for p in data if p["id"] == "core.tasks")
            assert tasks_plugin["name"] == "Core Tasks Extension"  # built-in name

            # Verify external command is listed
            response = client.get("/api/v1/commands")
            assert response.status_code == 200
            cmd_ids = [c["id"] for c in response.json()]
            assert "custom.weather.get_report" in cmd_ids

            # Verify fetching custom command details
            response = client.get("/api/v1/commands/custom.weather.get_report")
            assert response.status_code == 200
            assert response.json()["name"] == "Get Weather Report"

        finally:
            app.dependency_overrides.clear()
            # Restore registry to clean built-in state
            plugin_registry.load_external_plugins(Path(tmpdir))
