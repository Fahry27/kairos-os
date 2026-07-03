from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decision_plan import DecisionPlan
from app.schemas.decision_plan import DecisionPlanCreate, DecisionPlanStatus
from app.services.decision_plan_validator import (
    validate_decision_plan_payload,
    validate_lifecycle_transition,
)


def _to_decision_plan_model(payload: DecisionPlanCreate) -> DecisionPlan:
    json_data = payload.model_dump(mode="json")
    return DecisionPlan(
        schema_version=payload.schema_version,
        goal=payload.goal,
        status=payload.status.value,
        revision=payload.revision,
        root_decision_id=payload.root_decision_id,
        parent_decision_plan_id=payload.parent_decision_plan_id,
        workspace_session_id=payload.workspace_session_id,
        primary_path=json_data["primary_path"],
        alternatives=json_data["alternatives"],
        rationale=payload.rationale,
        evidence=json_data["evidence"],
        confidence=payload.confidence,
        assumptions=json_data["assumptions"],
        risks=json_data["risks"],
        constraints=json_data["constraints"],
        success_definition=payload.success_definition,
        provider_trace=json_data["provider_trace"],
        safety_flags=json_data["safety_flags"],
        approval_request_id=payload.approval_request_id,
    )


def create_decision_plan(db: Session, payload: DecisionPlanCreate | dict[str, Any]) -> DecisionPlan:
    validated = validate_decision_plan_payload(payload)
    plan = _to_decision_plan_model(validated)
    db.add(plan)
    db.commit()
    db.refresh(plan)

    if plan.root_decision_id is None:
        plan.root_decision_id = plan.id
        db.add(plan)
        db.commit()
        db.refresh(plan)

    return plan


def get_decision_plan(db: Session, decision_plan_id: UUID) -> DecisionPlan | None:
    return db.get(DecisionPlan, decision_plan_id)


def list_decision_plans(
    db: Session,
    status: DecisionPlanStatus | str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[DecisionPlan]:
    statement = select(DecisionPlan)
    if status:
        status_value = status.value if isinstance(status, DecisionPlanStatus) else status
        statement = statement.where(DecisionPlan.status == status_value)
    statement = statement.order_by(DecisionPlan.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


def update_decision_plan_status(
    db: Session,
    plan: DecisionPlan,
    next_status: DecisionPlanStatus | str,
) -> DecisionPlan:
    target = validate_lifecycle_transition(plan.status, next_status)
    plan.status = target.value
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def create_decision_plan_revision(
    db: Session,
    source_plan: DecisionPlan,
    payload: DecisionPlanCreate | dict[str, Any],
) -> DecisionPlan:
    validated = validate_decision_plan_payload(payload)
    next_payload = validated.model_copy(
        update={
            "status": DecisionPlanStatus.draft,
            "revision": source_plan.revision + 1,
            "root_decision_id": source_plan.root_decision_id or source_plan.id,
            "parent_decision_plan_id": source_plan.id,
            "approval_request_id": None,
        }
    )
    return create_decision_plan(db, next_payload)
