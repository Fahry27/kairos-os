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


def test_provider_router_lists_functional_local_and_metadata_stubs():
    response = client.get("/api/v1/ai/provider-router/providers")

    assert response.status_code == 200
    providers = {provider["id"]: provider for provider in response.json()}
    assert providers["ai.codex"]["functional"] is True
    assert providers["ai.codex"]["auth_type"] == "cli"
    assert providers["ai.ollama"]["functional"] is True
    assert providers["ai.ollama"]["auth_type"] == "none"

    for provider_id in ("ai.openai", "ai.gemini", "ai.claude"):
        provider = providers[provider_id]
        assert provider["functional"] is False
        assert provider["status"] == "metadata_only"
        assert provider["auth_type"] == "api_key"
        assert provider["oauth_implemented"] is False
        assert provider["external_api_calls_enabled"] is False


def test_provider_router_auto_selects_codex():
    response = client.get("/api/v1/ai/provider-router/route")

    assert response.status_code == 200
    data = response.json()
    assert data["auto_mode"] is True
    assert data["selected_provider"]["id"] == "ai.codex"
    assert data["policy"]["mode"] == "auto"
    assert data["policy"]["selected_provider_id"] == "ai.codex"


def test_provider_router_falls_back_from_metadata_stub():
    response = client.get("/api/v1/ai/provider-router/route", params={"provider_id": "ai.openai"})

    assert response.status_code == 200
    data = response.json()
    assert data["selected_provider"]["id"] == "ai.codex"
    assert data["policy"]["requested_provider_id"] == "ai.openai"
    assert data["policy"]["reason"] == "fallback_selected"
    assert "ai.openai:no_session" in data["policy"]["attempts"]
    assert "ai.codex:selected" in data["policy"]["attempts"]


@patch("app.core.codex_runtime.CodexCliRuntime.check_readiness")
def test_provider_router_models_use_selected_functional_provider(mock_check):
    _settings_override(kairos_ollama_readiness_enabled=True)
    from app.core.ai_runtime import AIProviderReadiness
    mock_check.return_value = AIProviderReadiness(
        provider_id="ai.codex",
        checked=True,
        reachable=True,
        message="Codex CLI ready",
    )
    try:
        response = client.get("/api/v1/ai/provider-router/models")

        assert response.status_code == 200
        data = response.json()
        assert data["provider_id"] == "ai.codex"
        assert data["policy"]["selected_provider_id"] == "ai.codex"
        assert data["checked"] is True
        assert data["reachable"] is True
        assert data["configured_model_available"] is True
        assert data["message"] == "Codex CLI ready"
    finally:
        app.dependency_overrides.pop(get_settings, None)


@patch("app.core.codex_runtime.CodexCliRuntime.dispatch")
def test_provider_router_dispatch_falls_back_to_codex_from_openai_stub(mock_dispatch):
    _settings_override(kairos_ollama_dispatch_enabled=True)
    from app.core.ai_runtime import AIOllamaDispatchResponse
    mock_dispatch.return_value = AIOllamaDispatchResponse(
        provider_id="ai.codex",
        model="codex-default",
        prompt_sent=True,
        response_text="Here is the plan.",
        raw_response_metadata={},
        safety_notes=[],
        latency_ms=100,
        truncated=False,
    )
    try:
        response = client.post(
            "/api/v1/ai/provider-router/dispatch",
            json={
                "provider_id": "ai.openai",
                "user_goal": "Plan a safe backup",
                "model": "codex-default",
                "parse_response": False,
                "create_approval_requests": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["selected_provider_id"] == "ai.codex"
        assert data["fallback_used"] is True
        assert data["response_text"] == "Here is the plan."
        assert "ai.openai:no_session" in data["provider_attempts"]
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
