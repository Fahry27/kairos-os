"""
Kairos AI Runtime API endpoints (v2.0.0).

All endpoints are read-only metadata or deterministic planning responses.
No LLM calls, no connector calls, no command execution.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import verify_api_key
from app.core.config import get_settings, Settings
from app.core.ai_runtime import (
    ai_runtime,
    AICapabilities,
    AIProviderManifest,
    AIProviderReadiness,
    AIProviderModelsResponse,
    AIPromptDryRunRequest,
    AIPromptDryRunResponse,
    AIOllamaDispatchRequest,
    AIOllamaDispatchResponse,
    AIParsePlanRequest,
    AIParsedPlan,
    PlanResponse,
)
from app.core.ai_provider_router import (
    AIProviderMetadata,
    AIProviderRouteResponse,
    AIProviderRouterDispatchRequest,
    AIProviderRouterDispatchResponse,
    AIProviderRouterModelsResponse,
    provider_registry,
    provider_router,
)
from app.schemas.approval import ApprovalRequestCreate, ApprovalActionType, ApprovalRiskLevel
from app.services import approval_service
from app.api.deps import get_db
from sqlalchemy.orm import Session
from app.core.plugins import plugin_registry
from app.core.connectors import connector_registry

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response schemas local to this router
# ---------------------------------------------------------------------------


class AIInfoResponse(BaseModel):
    ai_enabled: bool
    provider: str
    model: str | None
    planning_enabled: bool
    execution_enabled: bool  # always False in v2.0
    version: str


class PlanRequest(BaseModel):
    user_goal: str
    context: dict | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=AIInfoResponse)
def get_ai_info(
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Return high-level AI runtime status."""
    return AIInfoResponse(
        ai_enabled=settings.kairos_ai_enabled,
        provider=settings.kairos_ai_provider,
        model=settings.kairos_ai_model or None,
        planning_enabled=settings.kairos_ai_planning_enabled,
        execution_enabled=False,  # hard-gated in v2.0
        version=settings.app_version,
    )


@router.get("/providers", response_model=list[AIProviderManifest])
def list_ai_providers(
    include_disabled: bool = False,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Return all registered AI provider manifests.

    When AI is disabled, returns an empty list.
    """
    if not settings.kairos_ai_enabled:
        return []
    return ai_runtime.get_all_providers(include_disabled=include_disabled)


@router.get("/providers/{provider_id}", response_model=AIProviderManifest)
def get_ai_provider(
    provider_id: str,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Return a single AI provider manifest by ID."""
    if not settings.kairos_ai_enabled:
        raise HTTPException(
            status_code=404,
            detail="AI runtime is disabled by system configuration",
        )
    provider = ai_runtime.get_provider(provider_id)
    if not provider:
        raise HTTPException(
            status_code=404,
            detail=f"AI provider '{provider_id}' not found",
        )
    return provider


@router.get("/providers/{provider_id}/readiness", response_model=AIProviderReadiness)
def check_provider_readiness(
    provider_id: str,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Check if the given AI provider is reachable.
    
    Safe, prompt-free check for local engines like Ollama.
    """
    if not settings.kairos_ai_enabled:
        return AIProviderReadiness(
            provider_id=provider_id,
            checked=False,
            reachable=None,
            message="AI runtime is disabled.",
        )
        
    provider = ai_runtime.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"AI provider '{provider_id}' not found")
        
    if provider_id == "ai.ollama":
        return ai_runtime.check_ollama_readiness(settings)
        
    return AIProviderReadiness(
        provider_id=provider_id,
        checked=False,
        reachable=None,
        message="Readiness check not available for this provider type.",
    )


@router.get("/readiness", response_model=AIProviderReadiness)
def check_active_provider_readiness(
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Check if the currently configured AI provider is reachable."""
    provider_id = f"ai.{settings.kairos_ai_provider}" if not settings.kairos_ai_provider.startswith("ai.") else settings.kairos_ai_provider
    return check_provider_readiness(provider_id, settings=settings)


@router.get("/providers/{provider_id}/models", response_model=AIProviderModelsResponse)
def get_provider_models(
    provider_id: str,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """List available models from the given AI provider.
    
    Safe, prompt-free check for local engines like Ollama.
    """
    if not settings.kairos_ai_enabled:
        return AIProviderModelsResponse(
            provider_id=provider_id,
            checked=False,
            reachable=None,
            message="AI runtime is disabled.",
        )
        
    provider = ai_runtime.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"AI provider '{provider_id}' not found")
        
    if provider_id == "ai.ollama":
        return ai_runtime.get_ollama_models(settings)
        
    return AIProviderModelsResponse(
        provider_id=provider_id,
        checked=False,
        reachable=None,
        message="Model discovery not available for this provider type.",
    )


@router.get("/models", response_model=AIProviderModelsResponse)
def get_active_provider_models(
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """List available models for the currently configured AI provider."""
    provider_id = f"ai.{settings.kairos_ai_provider}" if not settings.kairos_ai_provider.startswith("ai.") else settings.kairos_ai_provider
    return get_provider_models(provider_id, settings=settings)


@router.get("/capabilities", response_model=AICapabilities)
def get_ai_capabilities(
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Return a full runtime capabilities summary derived from live registries."""
    return ai_runtime.get_capabilities(settings, plugin_registry, connector_registry)


@router.get("/provider-router/providers", response_model=list[AIProviderMetadata])
def list_router_providers(
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    """Return provider router metadata.

    Cloud providers are metadata-only stubs in this release.
    """
    if not settings.kairos_ai_enabled:
        return []
    return provider_registry.list()


@router.get("/provider-router/route", response_model=AIProviderRouteResponse)
def get_provider_route(
    provider_id: str | None = None,
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    """Return the provider selected by the current router policy."""
    if not settings.kairos_ai_enabled:
        raise HTTPException(status_code=503, detail="AI runtime is disabled.")
    return provider_router.route(settings, provider_id)


@router.get("/provider-router/models", response_model=AIProviderRouterModelsResponse)
def get_provider_router_models(
    provider_id: str | None = None,
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    """Return model metadata through the provider router interface."""
    if not settings.kairos_ai_enabled:
        raise HTTPException(status_code=503, detail="AI runtime is disabled.")
    return provider_router.list_models(settings, provider_id)


@router.post("/provider-router/dispatch", response_model=AIProviderRouterDispatchResponse)
def provider_router_dispatch(
    body: AIProviderRouterDispatchRequest,
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    """Dispatch through the provider router.

    Only Ollama can dispatch in v3.3.0. Metadata-only provider stubs are never
    called externally and are skipped by fallback.
    """
    if body.create_approval_requests:
        raise HTTPException(
            status_code=400,
            detail="Provider router dispatch does not create approvals. Use parse-plan explicitly.",
        )
    if not body.user_goal or not body.user_goal.strip():
        raise HTTPException(status_code=422, detail="user_goal cannot be empty")
    if not settings.kairos_ai_enabled:
        raise HTTPException(status_code=503, detail="AI runtime is disabled.")
    if not settings.kairos_ollama_dispatch_enabled:
        raise HTTPException(
            status_code=403,
            detail="Provider router dispatch is disabled. Enable KAIROS_OLLAMA_DISPATCH_ENABLED.",
        )
    if not body.model:
        body.model = settings.kairos_ai_model
    if not body.model:
        raise HTTPException(
            status_code=400,
            detail="No model provided and KAIROS_AI_MODEL is not configured.",
        )
    return provider_router.dispatch(body, settings, plugin_registry, connector_registry)


@router.post("/plan", response_model=PlanResponse)
def create_plan(
    body: PlanRequest,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """Generate a deterministic, rule-based advisory plan for a user goal.

    Safety guarantees:
      - No LLM is called.
      - No commands are executed.
      - No connectors are called.
      - Response always contains execution_enabled=false.
    """
    if not settings.kairos_ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI runtime is disabled. Enable KAIROS_AI_ENABLED to use planning.",
        )
    if not settings.kairos_ai_planning_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI planning is disabled. Enable KAIROS_AI_PLANNING_ENABLED to use this endpoint.",
        )

    return ai_runtime.generate_plan(
        user_goal=body.user_goal,
        context=body.context,
        settings=settings,
        plugin_registry=plugin_registry,
        connector_registry=connector_registry,
    )


@router.post("/prompt/dry-run", response_model=AIPromptDryRunResponse)
def prompt_dry_run(
    body: AIPromptDryRunRequest,
    settings=Depends(get_settings),
    _=Depends(verify_api_key),
):
    """
    Builds a prompt payload for future LLM execution without sending it anywhere.
    """
    if not body.user_goal.strip():
        raise HTTPException(
            status_code=422,
            detail="user_goal cannot be empty.",
        )
        
    if not settings.kairos_ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI runtime is disabled. Enable KAIROS_AI_ENABLED.",
        )
        
    if not settings.kairos_ai_dry_run_enabled:
        raise HTTPException(
            status_code=403,
            detail="AI dry-run mode is disabled. Enable KAIROS_AI_DRY_RUN_ENABLED.",
        )
        
    return ai_runtime.generate_prompt_dry_run(
        request=body,
        settings=settings,
        plugin_registry=plugin_registry,
        connector_registry=connector_registry,
    )


@router.post(
    "/ollama/dispatch",
    response_model=AIOllamaDispatchResponse,
    summary="Dispatch a prompt to local Ollama",
    description="Manually dispatch a prompt to local Ollama. No execution, no mutation."
)
def ollama_dispatch(
    body: AIOllamaDispatchRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    if body.create_approval_requests and not settings.kairos_approval_gate_enabled:
        raise HTTPException(
            status_code=403,
            detail="Cannot create approval requests because the approval gate is disabled.",
        )
    if not body.user_goal or not body.user_goal.strip():
        raise HTTPException(
            status_code=422,
            detail="user_goal cannot be empty",
        )
        
    if not settings.kairos_ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI runtime is disabled.",
        )
        
    if not settings.kairos_ollama_dispatch_enabled:
        raise HTTPException(
            status_code=403,
            detail="Ollama local dispatch is disabled. Enable KAIROS_OLLAMA_DISPATCH_ENABLED.",
        )
        
    if settings.kairos_ai_provider not in ("ai.ollama", "ollama"):
        raise HTTPException(
            status_code=400,
            detail="Ollama dispatch requires KAIROS_AI_PROVIDER to be ai.ollama.",
        )
        
    # If no model provided, try fallback
    if not body.model:
        body.model = settings.kairos_ai_model
        
    if not body.model:
        raise HTTPException(
            status_code=400,
            detail="No model provided and KAIROS_AI_MODEL is not configured.",
        )
        
    response = ai_runtime.dispatch_to_ollama(
        request=body,
        settings=settings,
        plugin_registry=plugin_registry,
        connector_registry=connector_registry,
    )

    if body.create_approval_requests and response.parsed_plan:
        _handle_approval_requests(db, settings, response.parsed_plan)
        response.approval_requests = response.parsed_plan.approval_requests

    return response


@router.post(
    "/parse-plan",
    response_model=AIParsedPlan,
    summary="Parse raw LLM text into a structured plan",
    description="Parser-only endpoint. Does not call Ollama or any network. No execution, no mutation."
)
def parse_plan(
    body: AIParsePlanRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    if not body.response_text or not body.response_text.strip():
        raise HTTPException(
            status_code=422,
            detail="response_text cannot be empty.",
        )

    if not body.user_goal or not body.user_goal.strip():
        raise HTTPException(
            status_code=422,
            detail="user_goal cannot be empty.",
        )

    if not settings.kairos_ai_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI runtime is disabled.",
        )

    if not settings.kairos_ai_response_parser_enabled:
        raise HTTPException(
            status_code=403,
            detail="Response parser is disabled. Enable KAIROS_AI_RESPONSE_PARSER_ENABLED.",
        )

    if body.create_approval_requests and not settings.kairos_approval_gate_enabled:
        raise HTTPException(
            status_code=403,
            detail="Cannot create approval requests because the approval gate is disabled.",
        )

    parsed_plan = ai_runtime.parse_llm_response(
        response_text=body.response_text,
        user_goal=body.user_goal,
        model=body.model,
        settings=settings,
        plugin_registry=plugin_registry,
    )

    if body.create_approval_requests:
        _handle_approval_requests(db, settings, parsed_plan)

    return parsed_plan

def _handle_approval_requests(db: Session, settings: Settings, parsed_plan: AIParsedPlan) -> None:
    approvals = []
    for cmd in parsed_plan.command_suggestions:
        # Create approval request for each suggested command
        req = ApprovalRequestCreate(
            title=f"Execute {cmd.command_id}",
            description=cmd.reason,
            action_type=ApprovalActionType.command,
            proposed_action_id=cmd.command_id,
            source="ai.parsed_plan",
            risk_level=ApprovalRiskLevel.high if cmd.dangerous else ApprovalRiskLevel.medium,
            requires_manual_review=True,
            payload_summary={"user_goal": parsed_plan.user_goal, "reason": cmd.reason},
            safety_notes=parsed_plan.safety_notes,
            expires_in_minutes=settings.kairos_approval_default_ttl_minutes,
        )
        try:
            created = approval_service.create_approval(
                db, 
                req, 
                default_ttl_minutes=settings.kairos_approval_default_ttl_minutes,
                max_pending=settings.kairos_approval_max_pending
            )
            # Add simple dict representation for the response
            approvals.append({
                "id": str(created.id),
                "title": created.title,
                "status": created.status,
                "action_type": created.action_type,
                "proposed_action_id": created.proposed_action_id
            })
        except HTTPException:
            # If max pending is reached, we log or append a warning, but don't fail the parse
            parsed_plan.parser_warnings.append(
                f"Failed to create approval for {cmd.command_id}: maximum pending approvals reached."
            )
    parsed_plan.approval_requests = approvals
    
    parsed_plan.approval_requests = approvals
