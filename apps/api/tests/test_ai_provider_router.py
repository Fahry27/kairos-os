import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app

client = TestClient(app)


def _settings_override(**updates):
    def override():
        settings = Settings()
        return settings.model_copy(update=updates)

    app.dependency_overrides[get_settings] = override


def test_provider_router_lists_functional_ollama_and_metadata_stubs():
    response = client.get("/api/v1/ai/provider-router/providers")

    assert response.status_code == 200
    providers = {provider["id"]: provider for provider in response.json()}
    assert providers["ai.ollama"]["functional"] is True
    assert providers["ai.ollama"]["auth_type"] == "none"

    for provider_id in ("ai.openai", "ai.gemini", "ai.claude"):
        provider = providers[provider_id]
        assert provider["functional"] is False
        assert provider["status"] == "metadata_only"
        assert provider["auth_type"] == "api_key"
        assert provider["oauth_implemented"] is False
        assert provider["external_api_calls_enabled"] is False


def test_provider_router_auto_selects_ollama():
    response = client.get("/api/v1/ai/provider-router/route")

    assert response.status_code == 200
    data = response.json()
    assert data["auto_mode"] is True
    assert data["selected_provider"]["id"] == "ai.ollama"
    assert data["policy"]["mode"] == "auto"
    assert data["policy"]["selected_provider_id"] == "ai.ollama"


def test_provider_router_falls_back_from_metadata_stub():
    response = client.get("/api/v1/ai/provider-router/route", params={"provider_id": "ai.openai"})

    assert response.status_code == 200
    data = response.json()
    assert data["selected_provider"]["id"] == "ai.ollama"
    assert data["policy"]["requested_provider_id"] == "ai.openai"
    assert data["policy"]["reason"] == "fallback_selected"
    assert "ai.openai:metadata_only" in data["policy"]["attempts"]
    assert "ai.ollama:selected" in data["policy"]["attempts"]


@patch("urllib.request.urlopen")
def test_provider_router_models_use_selected_functional_provider(mock_urlopen):
    _settings_override(kairos_ollama_readiness_enabled=True)
    try:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(
            {
                "models": [
                    {
                        "name": "llama3.2:latest",
                        "model": "llama3.2:latest",
                        "size": 1234567,
                        "details": {"family": "llama"},
                    }
                ]
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = client.get("/api/v1/ai/provider-router/models")

        assert response.status_code == 200
        data = response.json()
        assert data["provider_id"] == "ai.ollama"
        assert data["policy"]["selected_provider_id"] == "ai.ollama"
        assert data["checked"] is True
        assert data["reachable"] is True
        assert data["model_count"] == 1
        assert data["models"][0]["name"] == "llama3.2:latest"
    finally:
        app.dependency_overrides.pop(get_settings, None)


@patch("urllib.request.urlopen")
def test_provider_router_dispatch_falls_back_to_ollama_from_openai_stub(mock_urlopen):
    _settings_override(
        kairos_ollama_dispatch_enabled=True,
        kairos_ai_model="llama3.2:latest",
    )
    try:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(
            {
                "model": "llama3.2:latest",
                "created_at": "2026-07-02T00:00:00Z",
                "response": "Here is the plan.",
                "done": True,
                "total_duration": 1000,
            }
        ).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        response = client.post(
            "/api/v1/ai/provider-router/dispatch",
            json={
                "provider_id": "ai.openai",
                "user_goal": "Plan a safe backup",
                "model": "llama3.2:latest",
                "parse_response": False,
                "create_approval_requests": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["selected_provider_id"] == "ai.ollama"
        assert data["fallback_used"] is True
        assert data["response_text"] == "Here is the plan."
        assert data["network_call_performed"] is True
        assert "ai.openai:metadata_only" in data["provider_attempts"]
        assert mock_urlopen.call_count == 1
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_provider_router_dispatch_blocks_approval_creation():
    _settings_override(kairos_ollama_dispatch_enabled=True, kairos_ai_model="llama3.2:latest")
    try:
        response = client.post(
            "/api/v1/ai/provider-router/dispatch",
            json={
                "user_goal": "Plan a safe backup",
                "model": "llama3.2:latest",
                "create_approval_requests": True,
            },
        )

        assert response.status_code == 400
        assert "does not create approvals" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)
