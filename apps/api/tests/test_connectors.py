import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-connectors-test.sqlite3"
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings, Settings  # noqa: E402
from app.core.connectors import connector_registry  # noqa: E402

client = TestClient(app)


def test_list_connectors():
    response = client.get("/api/v1/connectors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 9
    ids = [c["id"] for c in data]
    assert "connector.ollama" in ids
    assert "connector.n8n" in ids
    assert "connector.plex" in ids


def test_get_connector_by_id():
    response = client.get("/api/v1/connectors/connector.ollama")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "connector.ollama"
    assert data["name"] == "Ollama LLM Engine"
    assert "text_generation" in data["capabilities"]


def test_get_unknown_connector_returns_404():
    response = client.get("/api/v1/connectors/unknown.connector")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_connectors_disabled_behavior():
    def override_settings():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_CONNECTORS_ENABLED=False,
        )

    app.dependency_overrides[get_settings] = override_settings
    try:
        response = client.get("/api/v1/connectors")
        assert response.status_code == 200
        assert response.json() == []

        response = client.get("/api/v1/connectors/connector.ollama")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_external_connector_scanner_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Valid External Manifest
        valid_json = """{
            "id": "custom.home-assistant",
            "name": "Local Home Assistant",
            "version": "1.0.0",
            "description": "Smart home hub.",
            "category": "iot",
            "service_type": "smart_home",
            "auth_type": "api_key"
        }"""
        (tmp_path / "hass.json").write_text(valid_json, encoding="utf-8")

        # 2. Invalid Manifest (Malformed JSON)
        (tmp_path / "invalid.json").write_text("{invalid-json}", encoding="utf-8")

        # 3. Duplicate Built-in ID Manifest
        duplicate_json = """{
            "id": "connector.ollama",
            "name": "Duplicate Ollama",
            "version": "1.0.0",
            "description": "Duplicate details.",
            "category": "ai",
            "service_type": "ai_inference",
            "auth_type": "none"
        }"""
        (tmp_path / "duplicate.json").write_text(duplicate_json, encoding="utf-8")

        # Load external connectors into registry
        connector_registry.load_external_connectors(tmp_path)

        try:
            # Override settings to point KAIROS_CONNECTORS_DIR to our temp directory
            def override_settings():
                return Settings(
                    APP_ENV="test",
                    DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
                    KAIROS_CONNECTORS_DIR=str(tmp_path),
                )

            app.dependency_overrides[get_settings] = override_settings

            # Verify list contains both built-in and our loaded custom connector
            response = client.get("/api/v1/connectors")
            assert response.status_code == 200
            data = response.json()
            ids = [c["id"] for c in data]
            assert "custom.home-assistant" in ids
            assert "connector.ollama" in ids  # built-in remains unchanged

            # Verify built-in metadata is NOT overwritten by duplicates
            ollama_connector = next(c for c in data if c["id"] == "connector.ollama")
            assert ollama_connector["name"] == "Ollama LLM Engine"

        finally:
            app.dependency_overrides.clear()
            # Restore registry to clean built-in state
            connector_registry.load_external_connectors(Path(tmpdir))
