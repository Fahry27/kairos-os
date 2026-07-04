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


@patch.object(ai_runtime, "dispatch_to_ollama")
def test_integration_full_healthy_flow(mock_dispatch):
    # Setup standard functional Ollama
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "provider_id": "ai.ollama",
        "model": "llama2",
        "prompt_sent": True,
        "response_text": "success response",
        "raw_response_metadata": {},
        "safety_notes": [],
        "latency_ms": 15,
        "truncated": False
    }
    mock_dispatch.return_value = mock_resp

    settings = MagicMock()
    settings.kairos_ai_provider = "ollama"
    settings.kairos_ai_provider_mode = "auto"
    settings.kairos_ai_provider_fallback_enabled = True

    # Ollama has auto-session, passes check
    request = AIProviderRouterDispatchRequest(user_goal="Plan system upgrade")
    resp = router.dispatch(request, settings, None, None)

    assert resp.prompt_sent is True
    assert resp.selected_provider_id == "ai.ollama"
    assert "ai.ollama:selected" in resp.provider_attempts


def test_integration_capability_filtering():
    registry = AIProviderRegistry()
    providers = registry.list()

    settings = MagicMock()
    settings.openai_api_key = None

    # Request capability not supported or functional (e.g. "prompt_dry_run" is only in Ollama)
    policy = RoutingPolicy(
        mode="auto",
        required_capabilities=["prompt_dry_run"]
    )
    
    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) == 1
    assert selected[0].id == "ai.ollama"


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

    # Mark Ollama explicitly Offline in Health Cache
    health_cache.set(
        "ai.ollama",
        ProviderHealth(provider_id="ai.ollama", status="offline", reachable=False)
    )

    policy = RoutingPolicy(mode="auto", required_capabilities=["chat"])
    
    # Selection should return empty because Ollama is offline
    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) == 0


@patch.object(ai_runtime, "dispatch_to_ollama")
def test_integration_fallback_chain_and_retry(mock_dispatch):
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    # Ollama fails with connection issue to trigger retries
    mock_dispatch.side_effect = Exception("Connection Refused")

    settings = MagicMock()
    settings.kairos_ai_provider = "ollama"
    settings.kairos_ai_provider_mode = "manual"
    settings.kairos_ai_provider_fallback_enabled = True

    # Dispatch should attempt Ollama (which retries and fails), 
    # then failover to the next policy model (which are metadata-only stubs)
    request = AIProviderRouterDispatchRequest(user_goal="Audit database logs", provider_id="ai.ollama")
    resp = router.dispatch(request, settings, None, None)

    # Prompt not sent successfully
    assert resp.prompt_sent is False
    # Attempt list should show Ollama failed/selected, and then fallbacks attempted
    assert "ai.ollama:selected" in resp.provider_attempts
    # OpenAI & Gemini are metadata-only stubs (not functional), so they are not attempted as fallback candidates
    assert "ai.openai:metadata_only" not in resp.provider_attempts


def test_integration_circuit_breaker_recovery():
    # 1. Trip the circuit breaker
    breaker = circuit_breakers.get("ai.ollama")
    breaker.failure_threshold = 2
    breaker.cooldown_seconds = 1  # Short cooldown
    
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.is_available() is False

    # 2. Verify it is excluded
    registry = AIProviderRegistry()
    providers = registry.list()
    settings = MagicMock()
    policy = RoutingPolicy(mode="auto", required_capabilities=["chat"])
    
    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) == 0

    # 3. Wait for cooldown to expire and verify it recovers (goes to half-open / available)
    time.sleep(1.1)
    assert breaker.is_available() is True
    assert breaker.state == "half-open"

    selected_recovered = ProviderSelection.select(providers, policy, settings)
    assert len(selected_recovered) > 0
    assert selected_recovered[0].id == "ai.ollama"
