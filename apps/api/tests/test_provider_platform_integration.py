import time
from unittest.mock import MagicMock, patch
import pytest
from app.core.ai_provider_router import (
    AIProviderRouter,
    AIProviderRegistry,
    AIProviderRouterDispatchRequest
)
from app.core.provider_session import provider_session_registry, ProviderSession, ProviderIdentity, ProviderCredential
from app.core.provider_health import health_cache, ProviderHealth
from app.core.fallback import circuit_breakers
from app.core.routing_policy import RoutingPolicy, ProviderSelection
from app.core.ai_runtime import ai_runtime


@pytest.fixture(autouse=True)
def clean_platform_state():
    # Reset all registries, caches, and breakers before each integration test
    provider_session_registry.clear()
    health_cache.clear()
    circuit_breakers.clear()


@patch("app.core.codex_runtime.CodexCliRuntime.dispatch")
def test_integration_full_healthy_flow(mock_dispatch):
    from app.core.ai_runtime import AIOllamaDispatchResponse
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    mock_dispatch.return_value = AIOllamaDispatchResponse(
        provider_id="ai.codex",
        model="codex-default",
        prompt_sent=True,
        response_text="success response",
        raw_response_metadata={},
        safety_notes=[],
        latency_ms=15,
        truncated=False,
    )

    settings = MagicMock()
    settings.kairos_ai_provider = "codex"
    settings.kairos_ai_provider_mode = "auto"
    settings.kairos_ai_provider_fallback_enabled = True

    request = AIProviderRouterDispatchRequest(user_goal="Plan system upgrade")
    resp = router.dispatch(request, settings, None, None)

    assert resp.prompt_sent is True
    assert resp.selected_provider_id == "ai.codex"
    assert "ai.codex:selected" in resp.provider_attempts


def test_integration_capability_filtering():
    registry = AIProviderRegistry()
    providers = registry.list()

    settings = MagicMock()
    settings.openai_api_key = None

    policy = RoutingPolicy(
        mode="auto",
        required_capabilities=["prompt_dry_run"]
    )

    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) >= 1
    assert any(p.id in ("ai.codex", "ai.ollama") for p in selected)


def test_integration_manual_override_respected():
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    settings = MagicMock()
    settings.kairos_ai_provider = "openai"  # Configured manually to OpenAI
    settings.kairos_ai_provider_mode = "manual"
    settings.kairos_ai_provider_fallback_enabled = False

    # OpenAI has no active session in test env, so it fails session check
    selected, policy = router.select_provider(settings)
    assert selected is None
    assert "ai.openai:no_session" in policy.attempts


def test_integration_unhealthy_provider_exclusion():
    registry = AIProviderRegistry()
    providers = registry.list()

    settings = MagicMock()

    # Mark both local providers (Codex + Ollama) as Offline in Health Cache
    health_cache.set(
        "ai.codex",
        ProviderHealth(provider_id="ai.codex", status="offline", reachable=False)
    )
    health_cache.set(
        "ai.ollama",
        ProviderHealth(provider_id="ai.ollama", status="offline", reachable=False)
    )

    policy = RoutingPolicy(mode="auto", required_capabilities=["chat"])

    # Selection should return empty because both local providers are offline
    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) == 0


@patch("app.core.codex_runtime.CodexCliRuntime.dispatch")
@patch.object(ai_runtime, "dispatch_to_ollama")
def test_integration_fallback_chain_and_retry(mock_ollama_dispatch, mock_codex_dispatch):
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    # Both providers fail to trigger exhaustion
    mock_ollama_dispatch.side_effect = Exception("Connection Refused")
    mock_codex_dispatch.side_effect = Exception("Codex unavailable")

    settings = MagicMock()
    settings.kairos_ai_provider = "ollama"
    settings.kairos_ai_provider_mode = "manual"
    settings.kairos_ai_provider_fallback_enabled = True

    # Dispatch should attempt Ollama (which retries and fails),
    # then failover to Codex (which also fails), then return error
    request = AIProviderRouterDispatchRequest(user_goal="Audit database logs", provider_id="ai.ollama")
    resp = router.dispatch(request, settings, None, None)

    # Prompt not sent successfully
    assert resp.prompt_sent is False
    assert "ai.ollama:selected" in resp.provider_attempts


def test_integration_circuit_breaker_recovery():
    # Trip circuit breakers for both functional local providers
    for pid in ("ai.codex", "ai.ollama"):
        breaker = circuit_breakers.get(pid)
        breaker.failure_threshold = 2
        breaker.cooldown_seconds = 1
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == "open"
        assert breaker.is_available() is False

    # Verify both are excluded
    registry = AIProviderRegistry()
    providers = registry.list()
    settings = MagicMock()
    policy = RoutingPolicy(mode="auto", required_capabilities=["chat"])

    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) == 0

    # Wait for cooldown to expire and verify recovery
    time.sleep(1.1)
    for pid in ("ai.codex", "ai.ollama"):
        breaker = circuit_breakers.get(pid)
        assert breaker.is_available() is True
        assert breaker.state == "half-open"

    selected_recovered = ProviderSelection.select(providers, policy, settings)
    assert len(selected_recovered) >= 1
    assert any(p.id in ("ai.codex", "ai.ollama") for p in selected_recovered)
