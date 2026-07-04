"""AI provider registry and router.

The router gives dashboard clients one provider-facing interface while keeping
provider implementation details server-side. In v3.3.0 only Ollama can perform
local dispatch. Cloud providers are metadata-only stubs and never make outbound
API calls.
"""

from pydantic import BaseModel, Field

from app.core.ai_runtime import (
    AIOllamaDispatchRequest,
    AIOllamaDispatchResponse,
    AIParsedPlan,
    AIProviderModelsResponse,
    OllamaModelManifest,
    ai_runtime,
)


def normalize_provider_id(provider_id: str | None) -> str | None:
    if not provider_id:
        return None
    normalized = provider_id.strip()
    if not normalized or normalized == "auto" or normalized == "ai.auto":
        return None
    return normalized if normalized.startswith("ai.") else f"ai.{normalized}"


class ProviderCapability(BaseModel):
    name: str
    description: str | None = None
    enabled: bool = True


class ProviderHealthMetadata(BaseModel):
    status: str = "unknown"
    last_check: str | None = None
    error_count: int = 0
    message: str | None = None


class ProviderCostMetadata(BaseModel):
    tier: str = "medium"
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


class ProviderPriorityMetadata(BaseModel):
    default_priority: int = 100
    override_priority: int | None = None

    @property
    def effective_priority(self) -> int:
        return self.override_priority if self.override_priority is not None else self.default_priority


class ProviderPolicyModel(BaseModel):
    required_capabilities: list[str] = Field(default_factory=list)
    max_cost_tier: str | None = None
    require_local: bool = False


class AIProviderMetadata(BaseModel):
    id: str
    name: str
    provider_type: str
    enabled: bool = True
    functional: bool = False
    status: str = "stub"
    auth_type: str = "none"
    oauth_implemented: bool = False
    external_api_calls_enabled: bool = False
    default_model: str | None = None
    configured_model: str | None = None
    supports_local: bool = False
    supports_chat: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    priority: int = 100
    capabilities: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    
    # V2 Metadata
    health: ProviderHealthMetadata = Field(default_factory=ProviderHealthMetadata)
    priority_metadata: ProviderPriorityMetadata = Field(default_factory=ProviderPriorityMetadata)
    cost: ProviderCostMetadata = Field(default_factory=ProviderCostMetadata)
    capability_registry: dict[str, ProviderCapability] = Field(default_factory=dict)

    def has_capability(self, name: str) -> bool:
        if name in self.capabilities:
            return True
        cap = self.capability_registry.get(name)
        return cap.enabled if cap else False


class AIProviderSelectionPolicy(BaseModel):
    mode: str
    requested_provider_id: str | None = None
    selected_provider_id: str | None = None
    fallback_enabled: bool = True
    fallback_order: list[str] = Field(default_factory=list)
    attempts: list[str] = Field(default_factory=list)
    reason: str


class AIProviderRouteResponse(BaseModel):
    providers: list[AIProviderMetadata]
    selected_provider: AIProviderMetadata | None = None
    policy: AIProviderSelectionPolicy
    auto_mode: bool
    dispatch_enabled: bool = False


class AIProviderRouterModelsResponse(BaseModel):
    provider_id: str
    provider_name: str
    policy: AIProviderSelectionPolicy
    checked: bool = False
    reachable: bool | None = None
    models: list[OllamaModelManifest] = Field(default_factory=list)
    model_count: int = 0
    configured_model_available: bool | None = None
    error_type: str | None = None
    message: str | None = None


class AIProviderRouterDispatchRequest(AIOllamaDispatchRequest):
    provider_id: str | None = None
    fallback_enabled: bool | None = None


class AIProviderRouterDispatchResponse(AIOllamaDispatchResponse):
    selected_provider_id: str
    selected_provider_name: str
    policy: AIProviderSelectionPolicy
    fallback_used: bool = False
    provider_attempts: list[str] = Field(default_factory=list)


class AIProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, AIProviderMetadata] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            AIProviderMetadata(
                id="ai.ollama",
                name="Ollama",
                provider_type="local",
                functional=True,
                status="functional",
                auth_type="none",
                default_model="",
                supports_local=True,
                supports_chat=True,
                supports_tools=True,
                supports_vision=True,
                priority=10,
                capabilities=["models", "prompt_dry_run", "dispatch", "parse_plan"],
                notes=["Only functional provider in v3.3.0."],
                priority_metadata=ProviderPriorityMetadata(default_priority=10),
                cost=ProviderCostMetadata(tier="free"),
                capability_registry={
                    "chat": ProviderCapability(name="chat", enabled=True),
                    "tools": ProviderCapability(name="tools", enabled=True),
                    "vision": ProviderCapability(name="vision", enabled=True),
                }
            )
        )
        self.register(
            AIProviderMetadata(
                id="ai.openai",
                name="OpenAI",
                provider_type="cloud",
                status="metadata_only",
                auth_type="api_key",
                default_model="gpt-4o",
                supports_chat=True,
                supports_tools=True,
                supports_vision=True,
                priority=50,
                capabilities=["metadata"],
                notes=["Provider stub only. No external API calls are implemented."],
                priority_metadata=ProviderPriorityMetadata(default_priority=50),
                cost=ProviderCostMetadata(tier="high"),
                capability_registry={
                    "chat": ProviderCapability(name="chat", enabled=True),
                    "tools": ProviderCapability(name="tools", enabled=True),
                    "vision": ProviderCapability(name="vision", enabled=True),
                }
            )
        )
        self.register(
            AIProviderMetadata(
                id="ai.gemini",
                name="Gemini",
                provider_type="cloud",
                status="metadata_only",
                auth_type="api_key",
                default_model="gemini-1.5-pro",
                supports_chat=True,
                supports_tools=True,
                supports_vision=True,
                priority=60,
                capabilities=["metadata"],
                notes=["Provider stub only. No external API calls are implemented."],
                priority_metadata=ProviderPriorityMetadata(default_priority=60),
                cost=ProviderCostMetadata(tier="medium"),
                capability_registry={
                    "chat": ProviderCapability(name="chat", enabled=True),
                    "tools": ProviderCapability(name="tools", enabled=True),
                    "vision": ProviderCapability(name="vision", enabled=True),
                }
            )
        )
        self.register(
            AIProviderMetadata(
                id="ai.claude",
                name="Claude",
                provider_type="cloud",
                status="metadata_only",
                auth_type="api_key",
                default_model="claude-3-5-sonnet",
                supports_chat=True,
                supports_tools=True,
                supports_vision=True,
                priority=70,
                capabilities=["metadata"],
                notes=["Provider stub only. No external API calls are implemented."],
                priority_metadata=ProviderPriorityMetadata(default_priority=70),
                cost=ProviderCostMetadata(tier="high"),
                capability_registry={
                    "chat": ProviderCapability(name="chat", enabled=True),
                    "tools": ProviderCapability(name="tools", enabled=True),
                    "vision": ProviderCapability(name="vision", enabled=True),
                }
            )
        )

    def register(self, provider: AIProviderMetadata) -> None:
        self._providers[provider.id] = provider

    def get(self, provider_id: str | None) -> AIProviderMetadata | None:
        normalized = normalize_provider_id(provider_id)
        return self._providers.get(normalized or "")

    def list(self, include_disabled: bool = True) -> list[AIProviderMetadata]:
        providers = sorted(self._providers.values(), key=lambda p: (p.priority_metadata.effective_priority, p.priority))
        if include_disabled:
            return providers
        return [provider for provider in providers if provider.enabled]

    def find_by_policy(self, policy: ProviderPolicyModel) -> list[AIProviderMetadata]:
        results = []
        for p in self.list(include_disabled=False):
            if policy.require_local and not p.supports_local:
                continue
                
            missing_cap = False
            for cap in policy.required_capabilities:
                if not p.has_capability(cap):
                    missing_cap = True
                    break
            if missing_cap:
                continue
                
            results.append(p)
        return results


class AIProviderRouter:
    def __init__(self, registry: AIProviderRegistry) -> None:
        self.registry = registry

    def _fallback_order(self, settings) -> list[str]:
        raw_order = getattr(settings, "kairos_ai_provider_fallback_order", "")
        order = [normalize_provider_id(item) for item in raw_order.split(",") if item.strip()]
        normalized = [provider_id for provider_id in order if provider_id]
        if normalized:
            return normalized
        return [p.id for p in self.registry.list()]

    def _provider_with_config(self, provider: AIProviderMetadata, settings) -> AIProviderMetadata:
        configured_model = settings.kairos_ai_model if provider.id == "ai.ollama" else None
        return provider.model_copy(update={"configured_model": configured_model or None})

    def select_provider(
        self,
        settings,
        requested_provider_id: str | None = None,
        fallback_enabled: bool | None = None,
    ) -> tuple[AIProviderMetadata | None, AIProviderSelectionPolicy]:
        requested = normalize_provider_id(requested_provider_id)
        configured = normalize_provider_id(settings.kairos_ai_provider)
        mode = settings.kairos_ai_provider_mode
        fallback = settings.kairos_ai_provider_fallback_enabled
        if fallback_enabled is not None:
            fallback = fallback_enabled

        fallback_order = self._fallback_order(settings)
        attempts: list[str] = []
        candidates: list[str] = []
        if requested:
            candidates.append(requested)
        elif mode == "manual" and configured:
            candidates.append(configured)
        else:
            candidates.extend(fallback_order)

        if fallback:
            for provider_id in fallback_order:
                if provider_id not in candidates:
                    candidates.append(provider_id)

        for provider_id in candidates:
            provider = self.registry.get(provider_id)
            if provider is None:
                attempts.append(f"{provider_id}:missing")
                continue
            if not provider.enabled:
                attempts.append(f"{provider_id}:disabled")
                continue
            if not provider.functional:
                attempts.append(f"{provider_id}:metadata_only")
                continue
            selected = self._provider_with_config(provider, settings)
            attempts.append(f"{provider_id}:selected")
            reason = "auto_selected" if not requested and mode == "auto" else "provider_selected"
            if requested and requested != provider_id:
                reason = "fallback_selected"
            policy = AIProviderSelectionPolicy(
                mode=mode,
                requested_provider_id=requested,
                selected_provider_id=selected.id,
                fallback_enabled=fallback,
                fallback_order=fallback_order,
                attempts=attempts,
                reason=reason,
            )
            return selected, policy

        policy = AIProviderSelectionPolicy(
            mode=mode,
            requested_provider_id=requested,
            selected_provider_id=None,
            fallback_enabled=fallback,
            fallback_order=fallback_order,
            attempts=attempts,
            reason="no_functional_provider_available",
        )
        return None, policy

    def route(self, settings, requested_provider_id: str | None = None) -> AIProviderRouteResponse:
        selected, policy = self.select_provider(settings, requested_provider_id)
        providers = [self._provider_with_config(provider, settings) for provider in self.registry.list()]
        dispatch_enabled = bool(
            selected and selected.id == "ai.ollama" and settings.kairos_ollama_dispatch_enabled
        )
        return AIProviderRouteResponse(
            providers=providers,
            selected_provider=selected,
            policy=policy,
            auto_mode=policy.mode == "auto" and policy.requested_provider_id is None,
            dispatch_enabled=dispatch_enabled,
        )

    def list_models(
        self,
        settings,
        requested_provider_id: str | None = None,
    ) -> AIProviderRouterModelsResponse:
        selected, policy = self.select_provider(settings, requested_provider_id)
        if selected is None:
            return AIProviderRouterModelsResponse(
                provider_id="",
                provider_name="No provider",
                policy=policy,
                message="No functional provider is available.",
            )
        if selected.id != "ai.ollama":
            return AIProviderRouterModelsResponse(
                provider_id=selected.id,
                provider_name=selected.name,
                policy=policy,
                message="Provider is metadata-only in this release.",
            )

        models: AIProviderModelsResponse = ai_runtime.get_ollama_models(settings)
        return AIProviderRouterModelsResponse(
            provider_id=selected.id,
            provider_name=selected.name,
            policy=policy,
            checked=models.checked,
            reachable=models.reachable,
            models=models.models,
            model_count=models.model_count,
            configured_model_available=models.configured_model_available,
            error_type=models.error_type,
            message=models.message,
        )

    def dispatch(
        self,
        request: AIProviderRouterDispatchRequest,
        settings,
        plugin_registry,
        connector_registry,
    ) -> AIProviderRouterDispatchResponse:
        selected, policy = self.select_provider(
            settings,
            request.provider_id,
            request.fallback_enabled,
        )
        if selected is None:
            return self._router_error_response(request, policy, "No functional provider is available.")

        if selected.id != "ai.ollama":
            return self._router_error_response(
                request,
                policy,
                "Selected provider is metadata-only in this release.",
                selected,
            )

        ollama_request = AIOllamaDispatchRequest(**request.model_dump(exclude={"provider_id", "fallback_enabled"}))
        response = ai_runtime.dispatch_to_ollama(
            request=ollama_request,
            settings=settings,
            plugin_registry=plugin_registry,
            connector_registry=connector_registry,
        )
        return AIProviderRouterDispatchResponse(
            **response.model_dump(),
            selected_provider_id=selected.id,
            selected_provider_name=selected.name,
            policy=policy,
            fallback_used=bool(policy.requested_provider_id and policy.requested_provider_id != selected.id),
            provider_attempts=policy.attempts,
        )

    def _router_error_response(
        self,
        request: AIProviderRouterDispatchRequest,
        policy: AIProviderSelectionPolicy,
        message: str,
        selected: AIProviderMetadata | None = None,
    ) -> AIProviderRouterDispatchResponse:
        return AIProviderRouterDispatchResponse(
            provider_id=selected.id if selected else policy.selected_provider_id or "ai.none",
            model=request.model or "",
            prompt_sent=False,
            response_text="",
            raw_response_metadata={"error": message},
            safety_notes=["Provider router did not dispatch any prompt."],
            latency_ms=0,
            truncated=False,
            selected_provider_id=selected.id if selected else policy.selected_provider_id or "ai.none",
            selected_provider_name=selected.name if selected else "No provider",
            policy=policy,
            fallback_used=False,
            provider_attempts=policy.attempts,
            network_call_performed=False,
        )


provider_registry = AIProviderRegistry()
provider_router = AIProviderRouter(provider_registry)
AIProviderRouterDispatchResponse.model_rebuild(_types_namespace={"AIParsedPlan": AIParsedPlan})
