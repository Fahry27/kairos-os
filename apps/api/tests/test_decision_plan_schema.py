from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.decision_plan import (
    DECISION_PLAN_SCHEMA_VERSION,
    DecisionPlanCreate,
    DecisionPlanStatus,
)


def _valid_decision_plan_payload() -> dict:
    return {
        "schema_version": DECISION_PLAN_SCHEMA_VERSION,
        "goal": "Back up Kairos data and confirm health",
        "status": DecisionPlanStatus.draft.value,
        "revision": 1,
        "root_decision_id": str(uuid4()),
        "parent_decision_plan_id": None,
        "workspace_session_id": "pytest-session",
        "primary_path": {
            "title": "Controlled backup and health verification",
            "summary": "Prepare a metadata-only plan for backup review before approval.",
            "steps": [
                "Review the backup intent and target data.",
                "Submit the plan for approval before any workflow trigger.",
                "Verify system health after an approved workflow completes.",
            ],
            "capability_refs": [
                {"type": "command", "id": "core.operations.run_backup"},
                {"type": "command", "id": "core.operations.get_health"},
            ],
        },
        "alternatives": [
            {
                "title": "Manual verification first",
                "summary": "Check health before preparing any backup approval.",
                "steps": ["Review health metadata.", "Prepare approval only if health is acceptable."],
                "capability_refs": [{"type": "command", "id": "core.operations.get_health"}],
            }
        ],
        "rationale": "This plan preserves human authority and keeps execution behind approval.",
        "evidence": [
            {
                "source": "operator_goal",
                "summary": "The operator requested a backup and health confirmation.",
                "reference_id": "goal",
            }
        ],
        "confidence": 0.82,
        "assumptions": ["The configured backup workflow is available only after approval."],
        "risks": [
            {
                "severity": "medium",
                "description": "Backup workflow could fail or time out.",
                "mitigation": "Review sanitized WorkflowRun status after explicit trigger.",
            }
        ],
        "constraints": ["Planner must not execute, approve, or trigger workflows."],
        "success_definition": "A reviewed approval exists and any later workflow run is audited.",
        "provider_trace": {
            "provider_id": "ai.ollama",
            "model": "llama3.2:latest",
            "dispatch_used": False,
            "fallback_used": False,
            "warnings": [],
        },
        "safety_flags": {
            "execution_enabled": False,
            "approval_mutation_performed": False,
            "approval_requests_created": False,
            "workflow_triggered": False,
            "workflow_runs_created": False,
            "connector_calls_performed": False,
            "data_mutation_performed": False,
        },
        "approval_request_id": None,
    }


def test_valid_decision_plan_schema():
    plan = DecisionPlanCreate.model_validate(_valid_decision_plan_payload())

    assert plan.schema_version == DECISION_PLAN_SCHEMA_VERSION
    assert plan.goal == "Back up Kairos data and confirm health"
    assert plan.status == DecisionPlanStatus.draft
    assert plan.primary_path.title == "Controlled backup and health verification"
    assert plan.success_definition
    assert plan.confidence == 0.82
    assert plan.safety_flags.execution_enabled is False
    assert plan.safety_flags.approval_requests_created is False
    assert plan.safety_flags.workflow_runs_created is False


def test_decision_plan_requires_success_definition():
    payload = _valid_decision_plan_payload()
    payload.pop("success_definition")

    with pytest.raises(ValidationError):
        DecisionPlanCreate.model_validate(payload)


def test_decision_plan_requires_primary_path():
    payload = _valid_decision_plan_payload()
    payload.pop("primary_path")

    with pytest.raises(ValidationError):
        DecisionPlanCreate.model_validate(payload)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_decision_plan_rejects_invalid_confidence(confidence: float):
    payload = _valid_decision_plan_payload()
    payload["confidence"] = confidence

    with pytest.raises(ValidationError):
        DecisionPlanCreate.model_validate(payload)


def test_decision_plan_rejects_invalid_status():
    payload = _valid_decision_plan_payload()
    payload["status"] = "approved"

    with pytest.raises(ValidationError):
        DecisionPlanCreate.model_validate(payload)


@pytest.mark.parametrize(
    "flag_name",
    [
        "execution_enabled",
        "approval_mutation_performed",
        "approval_requests_created",
        "workflow_triggered",
        "workflow_runs_created",
        "connector_calls_performed",
        "data_mutation_performed",
    ],
)
def test_decision_plan_rejects_planner_side_effect_flags(flag_name: str):
    payload = _valid_decision_plan_payload()
    payload["safety_flags"][flag_name] = True

    with pytest.raises(ValidationError):
        DecisionPlanCreate.model_validate(payload)


def test_decision_plan_rejects_duplicate_primary_path_as_alternative():
    payload = _valid_decision_plan_payload()
    payload["alternatives"] = [
        {
            "title": payload["primary_path"]["title"],
            "summary": payload["primary_path"]["summary"],
            "steps": ["Duplicate path should not validate."],
        }
    ]

    with pytest.raises(ValidationError):
        DecisionPlanCreate.model_validate(payload)
