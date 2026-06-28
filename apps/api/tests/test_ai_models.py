import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings, Settings  # noqa: E402


client = TestClient(app)


def override_settings_enabled():
    base = get_settings()
    return Settings(
        **base.model_dump(exclude={"kairos_ai_enabled", "kairos_ollama_readiness_enabled"}),
        KAIROS_AI_ENABLED=True,
        KAIROS_OLLAMA_READINESS_ENABLED=True,
    )


def override_settings_disabled():
    base = get_settings()
    return Settings(
        **base.model_dump(exclude={"kairos_ollama_readiness_enabled"}),
        KAIROS_OLLAMA_READINESS_ENABLED=False,
    )


@patch("urllib.request.urlopen")
def test_get_ollama_models_success(mock_urlopen):
    app.dependency_overrides[get_settings] = override_settings_enabled
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "models": [
            {
                "name": "llama3.2:latest",
                "model": "llama3.2:latest",
                "size": 1234567,
                "details": {
                    "family": "llama"
                }
            }
        ]
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "ai.ollama"
    assert data["checked"] is True
    assert data["reachable"] is True
    assert data["model_count"] == 1
    assert len(data["models"]) == 1
    assert data["models"][0]["name"] == "llama3.2:latest"
    assert data["models"][0]["details"]["family"] == "llama"
    
    app.dependency_overrides.clear()


@patch("urllib.request.urlopen")
def test_get_ollama_models_timeout(mock_urlopen):
    app.dependency_overrides[get_settings] = override_settings_enabled
    
    mock_urlopen.side_effect = TimeoutError("Connection timed out")

    response = client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert data["checked"] is True
    assert data["reachable"] is False
    assert data["error_type"] == "timeout"
    assert data["model_count"] == 0
    assert len(data["models"]) == 0
    
    app.dependency_overrides.clear()


@patch("urllib.request.urlopen")
def test_get_ollama_models_http_error(mock_urlopen):
    app.dependency_overrides[get_settings] = override_settings_enabled
    
    mock_response = MagicMock()
    mock_response.status = 500
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert data["checked"] is True
    assert data["reachable"] is False
    assert data["error_type"] == "http_error"
    assert "HTTP 500" in data["message"]
    
    app.dependency_overrides.clear()


def test_get_ollama_models_readiness_disabled():
    app.dependency_overrides[get_settings] = override_settings_disabled

    response = client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert data["checked"] is False
    assert data["reachable"] is None
    assert "disabled" in data["message"].lower()
    assert data["model_count"] == 0
    
    app.dependency_overrides.clear()


def test_get_cloud_provider_models_returns_empty():
    response = client.get("/api/v1/ai/providers/ai.openai/models")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "ai.openai"
    assert data["checked"] is False
    assert data["reachable"] is None
    assert data["model_count"] == 0
