import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-ai-readiness-test.sqlite3"
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings, Settings  # noqa: E402
import urllib.error  # noqa: E402

client = TestClient(app)

def test_ollama_readiness_success():
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = b'{"models": [{"name": "llama2"}]}'
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        response = client.get("/api/v1/ai/providers/ai.ollama/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["provider_id"] == "ai.ollama"
        assert data["reachable"] is True
        assert data["checked"] is True
        assert data["model_count"] == 1
        assert "latency_ms" in data

def test_ollama_readiness_timeout():
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timeout")):
        response = client.get("/api/v1/ai/providers/ai.ollama/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["reachable"] is False
        assert data["error_type"] == "timeout"
        
def test_ollama_readiness_connection_error():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
        response = client.get("/api/v1/ai/providers/ai.ollama/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["reachable"] is False
        assert data["error_type"] == "connection_error"
        
def test_ollama_readiness_disabled():
    def override():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_OLLAMA_READINESS_ENABLED=False,
        )
    app.dependency_overrides[get_settings] = override
    try:
        response = client.get("/api/v1/ai/providers/ai.ollama/readiness")
        assert response.status_code == 200
        data = response.json()
        assert data["checked"] is False
        assert data["reachable"] is None
    finally:
        app.dependency_overrides.clear()

def test_cloud_provider_readiness():
    response = client.get("/api/v1/ai/providers/ai.openai/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "ai.openai"
    assert data["checked"] is False
    assert data["reachable"] is None
