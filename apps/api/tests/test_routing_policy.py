from unittest.mock import MagicMock
import pytest
from app.core.ai_provider_router import AIProviderMetadata, AIProviderRegistry
from app.core.routing_policy import (
    RoutingPolicy,
    CapabilityResolver,
    ProviderScoring,
    ProviderSelection
)
from app.core.fallback import circuit_breakers


@pytest.fixture(autouse=True)
def clean_breakers():
    circuit_breakers.clear()


def test_routing_policy_defaults():
    policy = RoutingPolicy()
    assert policy.mode == "auto"
    assert policy.preferred_provider_id is None
    assert policy.required_capabilities == []
    assert policy.require_local is False
    assert policy.max_cost_tier is None


def test_capability_resolver():
    provider = MagicMock(spec=AIProviderMetadata)
    provider.has_capability.side_effect = lambda cap: cap in ["chat", "vision"]

    assert CapabilityResolver.resolve(provider, ["chat"]) is True
    assert CapabilityResolver.resolve(provider, ["chat", "vision"]) is True
    assert CapabilityResolver.resolve(provider, ["tools"]) is False
    assert CapabilityResolver.resolve(provider, ["chat", "tools"]) is False


def test_provider_scoring():
    policy = RoutingPolicy()
    
    from app.core.ai_provider_router import ProviderPriorityMetadata, ProviderCostMetadata

    p1 = AIProviderMetadata(
        id="p1",
        name="P1",
        provider_type="local",
        priority_metadata=ProviderPriorityMetadata(default_priority=10),
        cost=ProviderCostMetadata(tier="free")
    )
    
    p2 = AIProviderMetadata(
        id="p2",
        name="P2",
        provider_type="cloud",
        priority_metadata=ProviderPriorityMetadata(default_priority=80),
        cost=ProviderCostMetadata(tier="high")
    )

    score_p1 = ProviderScoring.score(p1, policy)
    score_p2 = ProviderScoring.score(p2, policy)
    
    # p1 should score higher than p2
    assert score_p1 > score_p2

    # Cost penalty threshold test
    budget_policy = RoutingPolicy(max_cost_tier="medium")
    budget_score_p1 = ProviderScoring.score(p1, budget_policy)
    budget_score_p2 = ProviderScoring.score(p2, budget_policy)
    
    # p2 should be heavily penalized
    assert budget_score_p2 < 0
    assert budget_score_p1 > 0


def test_provider_selection(monkeypatch):
    registry = AIProviderRegistry()
    providers = registry.list()

    policy = RoutingPolicy(
        mode="auto",
        required_capabilities=["chat"]
    )
    
    settings = MagicMock()
    # Mock settings keys so environment variables are bypassable if present
    settings.openai_api_key = None
    settings.gemini_api_key = None
    settings.kairos_gemini_api_key = None

    # Enable local Ollama dispatch, Ollama is functional by default in tests
    selected = ProviderSelection.select(providers, policy, settings)
    
    # Ollama should be functional & returned as the top candidate since OpenAI/Gemini are metadata-only
    assert len(selected) > 0
    assert selected[0].id == "ai.ollama"


def test_provider_selection_local_only():
    registry = AIProviderRegistry()
    providers = registry.list()

    policy = RoutingPolicy(
        mode="auto",
        required_capabilities=["chat"],
        require_local=True
    )

    settings = MagicMock()
    settings.openai_api_key = None
    settings.gemini_api_key = None

    selected = ProviderSelection.select(providers, policy, settings)
    assert len(selected) == 1
    assert selected[0].id == "ai.ollama"
