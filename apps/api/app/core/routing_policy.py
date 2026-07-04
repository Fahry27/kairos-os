from typing import Any, Optional
from pydantic import BaseModel, Field
from app.core.ai_provider_router import AIProviderMetadata


class RoutingPolicy(BaseModel):
    mode: str = "auto"  # "auto" or "manual"
    preferred_provider_id: Optional[str] = None
    required_capabilities: list[str] = Field(default_factory=list)
    require_local: bool = False
    max_cost_tier: Optional[str] = None  # "free", "low", "medium", "high"


class CapabilityResolver:
    @staticmethod
    def resolve(provider: AIProviderMetadata, required_capabilities: list[str]) -> bool:
        for cap in required_capabilities:
            if not provider.has_capability(cap):
                return False
        return True


class ProviderScoring:
    @staticmethod
    def score(provider: AIProviderMetadata, policy: RoutingPolicy) -> float:
        # Base score derived from priority (lower value is higher priority)
        effective_prio = provider.priority_metadata.effective_priority
        score = 1000.0 - effective_prio

        # Cost adjustment
        cost_tier = provider.cost.tier.lower()
        if cost_tier == "high":
            score -= 200.0
        elif cost_tier == "medium":
            score -= 100.0
        elif cost_tier == "low":
            score -= 50.0
        elif cost_tier == "free":
            score += 50.0

        # Cost policy enforcement
        if policy.max_cost_tier:
            tier_order = {"free": 0, "low": 1, "medium": 2, "high": 3}
            max_val = tier_order.get(policy.max_cost_tier.lower(), 99)
            prov_val = tier_order.get(cost_tier, 99)
            if prov_val > max_val:
                score -= 10000.0  # Penalize heavily if exceeds budget

        return score


class ProviderSelection:
    @staticmethod
    def select(
        providers: list[AIProviderMetadata],
        policy: RoutingPolicy,
        settings
    ) -> list[AIProviderMetadata]:
        candidates = []
        for p in providers:
            # 1. Check if local-only is required
            if policy.require_local and not p.supports_local:
                continue

            # 2. Check capabilities
            if not CapabilityResolver.resolve(p, policy.required_capabilities):
                continue

            # 3. Verify session exists & is valid
            from app.core.provider_session import get_session_for_provider
            session = get_session_for_provider(p.id, settings)
            if session is None or not session.is_valid(settings):
                continue

            # 4. Check if functional (as per current system requirements)
            if not p.functional:
                continue

            # 5. Check Fallback Circuit Breaker
            from app.core.fallback import circuit_breakers
            breaker = circuit_breakers.get(p.id)
            if not breaker.is_available():
                continue

            candidates.append(p)

        # Score candidates and return sorted descending
        scored = [(ProviderScoring.score(c, policy), c) for c in candidates]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored]
