from typing import Any

from pydantic import ValidationError

from app.schemas.decision_plan import DecisionPlanCreate, DecisionPlanStatus


class DecisionPlanValidationError(ValueError):
    """Raised when DecisionPlan domain validation fails."""


ALLOWED_STATUS_TRANSITIONS: dict[DecisionPlanStatus, set[DecisionPlanStatus]] = {
    DecisionPlanStatus.draft: {DecisionPlanStatus.generating},
    DecisionPlanStatus.generating: {DecisionPlanStatus.validating},
    DecisionPlanStatus.validating: {DecisionPlanStatus.proposed},
    DecisionPlanStatus.proposed: set(),
}


def validate_decision_plan_payload(payload: DecisionPlanCreate | dict[str, Any]) -> DecisionPlanCreate:
    try:
        plan = payload if isinstance(payload, DecisionPlanCreate) else DecisionPlanCreate.model_validate(payload)
    except ValidationError as exc:
        raise DecisionPlanValidationError("DecisionPlan schema validation failed") from exc

    validate_decision_plan_invariants(plan)
    return plan


def validate_decision_plan_invariants(plan: DecisionPlanCreate) -> None:
    if not plan.success_definition.strip():
        raise DecisionPlanValidationError("DecisionPlan success_definition is required")
    if not (0 <= plan.confidence <= 1):
        raise DecisionPlanValidationError("DecisionPlan confidence must be between 0 and 1")

    primary_key = (plan.primary_path.title.strip(), plan.primary_path.summary.strip())
    for alternative in plan.alternatives:
        alternative_key = (alternative.title.strip(), alternative.summary.strip())
        if alternative_key == primary_key:
            raise DecisionPlanValidationError("DecisionPlan alternatives must not duplicate primary path")

    safety_flags = plan.safety_flags
    if safety_flags.execution_enabled:
        raise DecisionPlanValidationError("DecisionPlan cannot mark execution enabled")
    if safety_flags.approval_mutation_performed or safety_flags.approval_requests_created:
        raise DecisionPlanValidationError("DecisionPlan cannot create or mutate approvals")
    if safety_flags.workflow_triggered or safety_flags.workflow_runs_created:
        raise DecisionPlanValidationError("DecisionPlan cannot trigger workflows or create WorkflowRuns")
    if safety_flags.connector_calls_performed or safety_flags.data_mutation_performed:
        raise DecisionPlanValidationError("DecisionPlan cannot call connectors or mutate data")


def validate_lifecycle_transition(
    current_status: DecisionPlanStatus | str,
    next_status: DecisionPlanStatus | str,
) -> DecisionPlanStatus:
    try:
        current = (
            current_status
            if isinstance(current_status, DecisionPlanStatus)
            else DecisionPlanStatus(current_status)
        )
        target = next_status if isinstance(next_status, DecisionPlanStatus) else DecisionPlanStatus(next_status)
    except ValueError as exc:
        raise DecisionPlanValidationError("Invalid DecisionPlan lifecycle status") from exc

    if target not in ALLOWED_STATUS_TRANSITIONS[current]:
        raise DecisionPlanValidationError(
            f"Invalid DecisionPlan lifecycle transition: {current.value} -> {target.value}"
        )
    return target
