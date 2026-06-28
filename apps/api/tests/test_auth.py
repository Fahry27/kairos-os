import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-test.sqlite3"

os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings, Settings  # noqa: E402

client = TestClient(app)


def test_auth_disabled():
    # Force settings with empty API key
    def get_test_settings_no_auth():
        return Settings(
            KAIROS_API_KEY=None,
            use_mock_data=True
        )

    app.dependency_overrides[get_settings] = get_test_settings_no_auth
    try:
        # Health endpoints should be public
        res = client.get("/health")
        assert res.status_code == 200

        res = client.get("/api/v1/health")
        assert res.status_code == 200

        # Protected endpoints should be accessible
        res = client.get("/api/v1/projects")
        assert res.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_auth_enabled():
    def get_test_settings_auth():
        return Settings(
            KAIROS_API_KEY="my-secret-key",
            use_mock_data=True
        )

    app.dependency_overrides[get_settings] = get_test_settings_auth
    try:
        # Health endpoints should still be public
        res = client.get("/health")
        assert res.status_code == 200

        res = client.get("/api/v1/health")
        assert res.status_code == 200

        # Protected endpoints should require API Key
        res = client.get("/api/v1/projects")
        assert res.status_code == 401
        assert res.json()["detail"] == "X-Kairos-API-Key header is missing"

        # Wrong key should fail
        res = client.get("/api/v1/projects", headers={"X-Kairos-API-Key": "wrong-key"})
        assert res.status_code == 401
        assert res.json()["detail"] == "Invalid X-Kairos-API-Key"

        # Correct key should work
        res = client.get("/api/v1/projects", headers={"X-Kairos-API-Key": "my-secret-key"})
        assert res.status_code == 200
    finally:
        app.dependency_overrides.clear()
