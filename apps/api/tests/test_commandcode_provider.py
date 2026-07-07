"""Tests for Command Code provider integration."""

import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.ai_provider_router import AIProviderRegistry, AIProviderRouter, AIProviderMetadata
from app.core.provider_session import get_session_for_provider, provider_session_registry
from app.main import app

client = TestClient(app)


def _settings_override(**updates):
    def override():
        settings = Settings()
        return settings.model_copy(update=updates)

    app.dependency_overrides[get_settings] = override


def test_commandcode_registered_in_provider_registry():
    """Command Code provider is registered with correct metadata."""
    registry = AIProviderRegistry()
    provider = registry.get("ai.commandcode")

    assert provider is not None
    assert provider.id == "ai.commandcode"
    assert provider.name == "Command Code"
    assert provider.provider_type == "cloud"
    assert provider.functional is True
    assert provider.status == "functional"
    assert provider.auth_type == "api_key"
    assert provider.default_model == "mimo-v2.5"
    assert provider.supports_chat is True
    assert provider.supports_tools is True
    assert provider.supports_vision is False
    assert provider.priority == 20
    assert provider.external_api_calls_enabled is True


def test_commandcode_supported_models_in_notes():
    """Command Code notes list all supported models."""
    registry = AIProviderRegistry()
    provider = registry.get("ai.commandcode")

    assert provider is not None
    notes_text = " ".join(provider.notes)
    assert "mimo-v2.5" in notes_text
    assert "mimo-v2.5-pro" in notes_text
    assert "deepseek-v4-pro" in notes_text
    assert "minimax-m3" in notes_text


def test_commandcode_in_fallback_order():
    """Command Code is in the default fallback order."""
    settings = Settings()
    fallback_order = settings.kairos_ai_provider_fallback_order
    assert "ai.commandcode" in fallback_order


def test_commandcode_config_fields():
    """Command Code config fields have correct defaults."""
    settings = Settings()
    assert settings.commandcode_api_key is None
    assert settings.commandcode_base_url == "https://api.commandcode.ai/provider"
    assert settings.commandcode_model == "mimo-v2.5"


def test_commandcode_config_from_env(monkeypatch):
    """Command Code config fields load from environment variables."""
    monkeypatch.setenv("COMMANDCODE_API_KEY", "test-key-123")
    monkeypatch.setenv("COMMANDCODE_BASE_URL", "https://custom.endpoint.com")
    monkeypatch.setenv("COMMANDCODE_MODEL", "mimo-v2.5-pro")

    settings = Settings()
    assert settings.commandcode_api_key == "test-key-123"
    assert settings.commandcode_base_url == "https://custom.endpoint.com"
    assert settings.commandcode_model == "mimo-v2.5-pro"


def test_commandcode_session_requires_api_key(monkeypatch):
    """Command Code session is None without API key."""
    monkeypatch.delenv("COMMANDCODE_API_KEY", raising=False)
    settings = Settings()
    session = get_session_for_provider("ai.commandcode", settings)
    assert session is None


def test_commandcode_session_created_with_api_key(monkeypatch):
    """Command Code session is created when API key is set."""
    monkeypatch.setenv("COMMANDCODE_API_KEY", "test-key-123")
    settings = Settings()
    session = get_session_for_provider("ai.commandcode", settings)

    assert session is not None
    assert session.provider_id == "ai.commandcode"
    assert session.session_id == "session.commandcode.auto"
    assert session.credential.auth_type == "api_key"
    assert session.state == "active"


def test_commandcode_can_dispatch_with_api_key(monkeypatch):
    """_can_dispatch returns True when COMMANDCODE_API_KEY is set."""
    monkeypatch.setenv("COMMANDCODE_API_KEY", "test-key-123")
    settings = Settings()
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)
    provider = registry.get("ai.commandcode")

    assert router._can_dispatch(provider, settings) is True


def test_commandcode_cannot_dispatch_without_api_key(monkeypatch):
    """_can_dispatch returns False when COMMANDCODE_API_KEY is not set."""
    monkeypatch.delenv("COMMANDCODE_API_KEY", raising=False)
    settings = Settings()
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)
    provider = registry.get("ai.commandcode")

    assert router._can_dispatch(provider, settings) is False


def test_existing_providers_still_registered():
    """Existing providers (codex, ollama, openai) are still registered."""
    registry = AIProviderRegistry()

    codex = registry.get("ai.codex")
    assert codex is not None
    assert codex.functional is True
    assert codex.name == "Codex CLI"

    ollama = registry.get("ai.ollama")
    assert ollama is not None
    assert ollama.functional is True
    assert ollama.name == "Ollama"

    openai = registry.get("ai.openai")
    assert openai is not None
    assert openai.name == "OpenAI"


def test_commandcode_provider_listed_in_api():
    """Command Code appears in the provider list endpoint."""
    response = client.get("/api/v1/ai/provider-router/providers")

    assert response.status_code == 200
    providers = {p["id"]: p for p in response.json()}
    assert "ai.commandcode" in providers
    cc = providers["ai.commandcode"]
    assert cc["name"] == "Command Code"
    assert cc["functional"] is True
    assert cc["default_model"] == "mimo-v2.5"


@patch("app.core.ai_runtime.AIRuntime.dispatch_to_openai_compatible")
def test_commandcode_dispatch_uses_openai_compatible(mock_dispatch, monkeypatch):
    """Dispatch to Command Code uses the OpenAI-compatible path."""
    from app.core.ai_runtime import AIOllamaDispatchResponse

    monkeypatch.setenv("COMMANDCODE_API_KEY", "test-key-123")

    mock_dispatch.return_value = AIOllamaDispatchResponse(
        provider_id="ai.commandcode",
        model="mimo-v2.5",
        prompt_sent=True,
        response_text="Test response",
        raw_response_metadata={},
        safety_notes=[],
        latency_ms=100,
        truncated=False,
    )

    _settings_override(commandcode_api_key="test-key-123", kairos_ollama_dispatch_enabled=True)
    try:
        response = client.post(
            "/api/v1/ai/provider-router/dispatch",
            json={
                "provider_id": "ai.commandcode",
                "user_goal": "Help me with a task",
                "model": "mimo-v2.5",
                "parse_response": False,
                "create_approval_requests": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["selected_provider_id"] == "ai.commandcode"
        assert data["model"] == "mimo-v2.5"
        assert data["response_text"] == "Test response"

        mock_dispatch.assert_called_once()
        call_kwargs = mock_dispatch.call_args
        assert call_kwargs.kwargs.get("provider_id") or call_kwargs[1].get("provider_id") == "ai.commandcode"
    finally:
        app.dependency_overrides.pop(get_settings, None)


@patch("app.core.ai_runtime.AIRuntime.dispatch_to_openai_compatible")
def test_commandcode_dispatch_defaults_to_mimo(mock_dispatch, monkeypatch):
    """Dispatch defaults to mimo-v2.5 when no model specified in request."""
    from app.core.ai_runtime import AIOllamaDispatchResponse

    monkeypatch.setenv("COMMANDCODE_API_KEY", "test-key-123")

    mock_dispatch.return_value = AIOllamaDispatchResponse(
        provider_id="ai.commandcode",
        model="mimo-v2.5",
        prompt_sent=True,
        response_text="Test response",
        raw_response_metadata={},
        safety_notes=[],
        latency_ms=100,
        truncated=False,
    )

    _settings_override(
        commandcode_api_key="test-key-123",
        kairos_ollama_dispatch_enabled=True,
        kairos_ai_model="some-model",
    )
    try:
        response = client.post(
            "/api/v1/ai/provider-router/dispatch",
            json={
                "provider_id": "ai.commandcode",
                "user_goal": "Help me with a task",
                "parse_response": False,
                "create_approval_requests": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["selected_provider_id"] == "ai.commandcode"
        # Verify the dispatch was called with mimo-v2.5 (default for commandcode)
        mock_dispatch.assert_called_once()
        call_args = mock_dispatch.call_args
        dispatched_request = call_args.kwargs.get("request") or call_args[1].get("request")
        assert dispatched_request.model == "mimo-v2.5"
    finally:
        app.dependency_overrides.pop(get_settings, None)
