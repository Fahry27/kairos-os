import time
from unittest.mock import MagicMock, patch
import pytest
from app.core.fallback import (
    CircuitBreaker,
    circuit_breakers,
    RetryPolicy
)
from app.core.ai_provider_router import (
    AIProviderRouter,
    AIProviderRegistry,
    AIProviderRouterDispatchRequest
)


from app.core.ai_runtime import ai_runtime

@pytest.fixture(autouse=True)
def clean_breakers():
    circuit_breakers.clear()

def test_circuit_breaker_states():
    breaker = CircuitBreaker(provider_id="ai.test", failure_threshold=2, cooldown_seconds=1)
    
    assert breaker.is_available() is True
    assert breaker.state == "closed"

    breaker.record_failure()
    assert breaker.is_available() is True
    assert breaker.state == "closed"

    # Trip breaker
    breaker.record_failure()
    assert breaker.state == "open"
    assert breaker.is_available() is False

    # Wait for cooldown
    time.sleep(1.1)
    assert breaker.is_available() is True
    assert breaker.state == "half-open"

    # Reset
    breaker.record_success()
    assert breaker.state == "closed"
    assert breaker.failure_count == 0


def test_retry_policy():
    policy = RetryPolicy(max_retries=2, backoff_factor=2.0, backoff_max_seconds=5.0)
    assert policy.max_retries == 2
    assert policy.backoff_factor == 2.0


@patch.object(AIProviderRouter, "_ollama_is_reachable", return_value=True)
@patch.object(ai_runtime, "dispatch_to_ollama")
def test_router_dispatch_success(mock_dispatch, _mock_reachable):
    # Setup registry with Ollama functional
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    mock_resp = MagicMock()
    mock_resp.model_dump.return_value = {
        "provider_id": "ai.ollama",
        "model": "llama2",
        "prompt_sent": True,
        "response_text": "hello",
        "raw_response_metadata": {},
        "safety_notes": [],
        "latency_ms": 10,
        "truncated": False
    }
    mock_dispatch.return_value = mock_resp

    settings = MagicMock()
    settings.kairos_ai_provider = "ollama"
    settings.kairos_ai_provider_mode = "manual"
    settings.kairos_ai_provider_fallback_enabled = False

    request = AIProviderRouterDispatchRequest(user_goal="Test goal", provider_id="ai.ollama")
    
    # Ensure Ollama breaker is clear
    circuit_breakers.get("ai.ollama").record_success()

    resp = router.dispatch(request, settings, None, None)
    assert resp.prompt_sent is True
    assert resp.selected_provider_id == "ai.ollama"
    assert mock_dispatch.call_count == 1


@patch.object(AIProviderRouter, "_ollama_is_reachable", return_value=True)
@patch.object(ai_runtime, "dispatch_to_ollama")
def test_router_dispatch_retries_and_trips(mock_dispatch, _mock_reachable):
    registry = AIProviderRegistry()
    router = AIProviderRouter(registry)

    # Force dispatch error
    mock_dispatch.side_effect = Exception("Ollama Down")

    settings = MagicMock()
    settings.kairos_ai_provider = "ollama"
    settings.kairos_ai_provider_mode = "manual"
    settings.kairos_ai_provider_fallback_enabled = False

    request = AIProviderRouterDispatchRequest(user_goal="Test goal", provider_id="ai.ollama", fallback_enabled=False)

    breaker = circuit_breakers.get("ai.ollama")
    breaker.record_success()  # Reset
    # Set threshold to 2 for quick testing
    breaker.failure_threshold = 2

    resp = router.dispatch(request, settings, None, None)
    
    # Since Ollama failed all retries, breaker should be tripped and prompt_sent False
    assert resp.prompt_sent is False
    assert breaker.state == "open"
