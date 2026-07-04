import json
import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.core.ai_provider_router import (
    AIProviderRouterDispatchRequest,
    AIProviderRouterDispatchResponse,
    provider_router,
)
from app.core.connectors import connector_registry
from app.core.plugins import plugin_registry
from app.models.decision_plan import DecisionPlan
from app.schemas.decision_plan import (
    DECISION_PLAN_SCHEMA_VERSION,
    DecisionPlanCreate,
    DecisionPlanRead,
    DecisionPlanStatus,
)
from app.schemas.planner import PlannerRequest, PlannerResponse
from app.services.decision_plan_service import create_decision_plan
from app.services.decision_plan_validator import (
    DecisionPlanValidationError,
    validate_decision_plan_payload,
)


class PlannerEngineError(RuntimeError):
    """Base error for Planner Engine orchestration failures."""

logger = logging.getLogger(__name__)


class PlannerProviderError(PlannerEngineError):
    """Raised when the Provider Router cannot return usable planning output."""


class PlannerOutputError(PlannerEngineError):
    """Raised when provider output cannot be converted to a DecisionPlan draft."""


class PlannerValidationError(PlannerEngineError):
    """Raised when provider output fails DecisionPlan validation."""


class PlannerPersistenceError(PlannerEngineError):
    """Raised when a validated DecisionPlan cannot be persisted."""


ValidatorFn = Callable[[DecisionPlanCreate | dict[str, Any]], DecisionPlanCreate]
CreateFn = Callable[[Session, DecisionPlanCreate | dict[str, Any]], DecisionPlan]


class PlannerEngine:
    def __init__(
        self,
        router=provider_router,
        validator: ValidatorFn = validate_decision_plan_payload,
        create_plan: CreateFn = create_decision_plan,
    ) -> None:
        self.router = router
        self.validator = validator
        self.create_plan = create_plan

    def plan(self, db: Session, request: PlannerRequest | dict[str, Any], settings) -> PlannerResponse:
        planner_request = self._normalize_request(request)
        self._check_enabled(settings)

        dispatch_response = self._dispatch(planner_request, settings)
        draft_payload = self._to_decision_plan_payload(planner_request, dispatch_response, settings)
        validated = self._validate(draft_payload)
        persisted = self._persist(db, validated)

        return PlannerResponse(
            decision_plan=DecisionPlanRead.model_validate(persisted),
            provider_attempts=dispatch_response.provider_attempts,
            warnings=list(dispatch_response.safety_notes),
        )

    def _normalize_request(self, request: PlannerRequest | dict[str, Any]) -> PlannerRequest:
        planner_request = request if isinstance(request, PlannerRequest) else PlannerRequest.model_validate(request)
        trimmed_goal = planner_request.goal.strip()
        if not trimmed_goal:
            raise PlannerOutputError("Planner goal cannot be empty")
        return planner_request.model_copy(update={"goal": trimmed_goal, "context": planner_request.context or {}})

    def _check_enabled(self, settings) -> None:
        if not getattr(settings, "kairos_planner_enabled", True):
            raise PlannerEngineError("Planner Engine is disabled")
        if not getattr(settings, "kairos_ai_enabled", True):
            raise PlannerProviderError("AI runtime is disabled")

    def _dispatch(self, request: PlannerRequest, settings) -> AIProviderRouterDispatchResponse:
        prompt_instruction = (
            "You MUST return a JSON object containing a decision plan. "
            "Do NOT include conversational text outside the JSON. "
            "Do NOT use markdown code blocks (```json) or any formatting. Return ONLY the raw JSON string. "
            "The JSON must have this exact structure:\n"
            "{\n"
            '  "primary_path": {"title": "str", "summary": "str", "steps": ["str"], "capability_refs": [{"type": "command", "id": "str"}]},\n'
            '  "alternatives": [],\n'
            '  "rationale": "str",\n'
            '  "evidence": [{"source": "str", "summary": "str"}],\n'
            '  "confidence": 0.9,\n'
            '  "assumptions": ["str"],\n'
            '  "risks": [{"severity": "low", "description": "str"}],\n'
            '  "constraints": ["str"],\n'
            '  "success_definition": "str"\n'
            "}"
        )
        enriched_goal = f"{request.goal}\n\n{prompt_instruction}"

        dispatch_request = AIProviderRouterDispatchRequest(
            provider_id=request.provider_id or "ai.codex",
            fallback_enabled=request.fallback_enabled if request.fallback_enabled is not None else True,
            user_goal=enriched_goal,
            context=request.context,
            model=request.model or getattr(settings, "kairos_ai_model", None) or None,
            dry_run_first=True,
            include_commands=True,
            include_plugins=True,
            include_connectors=True,
            parse_response=False,
            create_approval_requests=False,
        )
        response = self.router.dispatch(dispatch_request, settings, plugin_registry, connector_registry)
        provider_error = response.raw_response_metadata.get("error")
        if provider_error:
            raise PlannerProviderError(str(provider_error))
        if not response.prompt_sent:
            raise PlannerProviderError("Provider Router did not dispatch a planning prompt")
        if not response.response_text.strip():
            raise PlannerProviderError("Provider returned no planning output")
        return response

    def _to_decision_plan_payload(
        self,
        request: PlannerRequest,
        response: AIProviderRouterDispatchResponse,
        settings,
    ) -> dict[str, Any]:
        output = self._parse_provider_output(response.response_text, settings)
        provider_trace = output.get("provider_trace") or {}
        provider_trace.update(
            {
                "provider_id": response.selected_provider_id,
                "model": response.model or request.model,
                "dispatch_used": response.prompt_sent,
                "fallback_used": response.fallback_used,
                "warnings": list(response.safety_notes),
            }
        )

        return {
            "schema_version": output.get("schema_version", DECISION_PLAN_SCHEMA_VERSION),
            "goal": request.goal,
            "status": output.get("status", DecisionPlanStatus.draft.value),
            "revision": output.get("revision", 1),
            "root_decision_id": None,
            "parent_decision_plan_id": None,
            "workspace_session_id": request.workspace_session_id,
            "primary_path": output.get("primary_path"),
            "alternatives": output.get("alternatives", []),
            "rationale": output.get("rationale"),
            "evidence": output.get("evidence"),
            "confidence": output.get("confidence"),
            "assumptions": output.get("assumptions", []),
            "risks": output.get("risks", []),
            "constraints": output.get("constraints", []),
            "success_definition": output.get("success_definition"),
            "provider_trace": provider_trace,
            "safety_flags": output.get(
                "safety_flags",
                {
                    "execution_enabled": False,
                    "approval_mutation_performed": False,
                    "approval_requests_created": False,
                    "workflow_triggered": False,
                    "workflow_runs_created": False,
                    "connector_calls_performed": False,
                    "data_mutation_performed": False,
                },
            ),
            "approval_request_id": None,
        }

    def _parse_provider_output(self, response_text: str, settings) -> dict[str, Any]:
        logger.info(f"Raw provider output:\n{response_text}")
        max_chars = getattr(settings, "kairos_planner_max_provider_response_chars", 8000)
        if len(response_text) > max_chars:
            raise PlannerOutputError("Provider planning output exceeded configured size limit")

        # Save raw output to a temporary file in the workspace
        try:
            temp_path = "raw_provider_output.json"
            with open(temp_path, "w") as f:
                f.write(response_text)
            logger.info(f"Saved raw provider output to {temp_path}")
        except Exception as e:
            logger.error(f"Failed to save raw provider output: {e}")

        text = response_text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error(f"Parser exception: {exc}")
            raise PlannerOutputError("Provider planning output is not valid JSON") from exc

        if not isinstance(parsed, dict):
            logger.error("Parsed JSON is not a dictionary.")
            raise PlannerOutputError("Provider planning output must be a JSON object")
        return parsed

    def _validate(self, payload: dict[str, Any]) -> DecisionPlanCreate:
        try:
            return self.validator(payload)
        except DecisionPlanValidationError as exc:
            cause = exc.__cause__
            if cause and hasattr(cause, "errors"):
                logger.error(f"Pydantic Validation Errors: {cause.errors()}")
            else:
                logger.error(f"Validation exception for payload: {exc}")
            raise PlannerValidationError(str(exc)) from exc

    def _persist(self, db: Session, payload: DecisionPlanCreate) -> DecisionPlan:
        try:
            return self.create_plan(db, payload)
        except Exception as exc:
            raise PlannerPersistenceError("DecisionPlan persistence failed") from exc


planner_engine = PlannerEngine()
