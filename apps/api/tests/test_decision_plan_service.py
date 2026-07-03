from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.decision_plan import DecisionPlan
from app.schemas.decision_plan import (
    DECISION_PLAN_SCHEMA_VERSION,
    DecisionPlanCreate,
    DecisionPlanStatus,
)
from app.services.decision_plan_service import (
    create_decision_plan,
    create_decision_plan_revision,
    get_decision_plan,
    list_decision_plans,
    update_decision_plan_status,
)
from app.services.decision_plan_validator import (
    DecisionPlanValidationError,
    validate_decision_plan_payload,
)


@pytest.fixture()
def db_session():
    engine = sa.create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with LocalSession() as db:
        yield db
    engine.dispose()


def _valid_payload(goal: str = "Back up Kairos data and confirm health") -> dict:
    return {
        "schema_version": DECISION_PLAN_SCHEMA_VERSION,
        "goal": goal,
        "status": DecisionPlanStatus.draft.value,
        "revision": 1,
        "root_decision_id": None,
        "parent_decision_plan_id": None,
        "workspace_session_id": "pytest-session",
        "primary_path": {
            "title": "Controlled backup and health verification",
            "summary": "Prepare a metadata-only plan for backup review.",
            "steps": ["Review intent.", "Keep execution behind approval."],
            "capability_refs": [{"type": "command", "id": "core.operations.run_backup"}],
        },
        "alternatives": [
            {
                "title": "Health check first",
                "summary": "Check service health before backup planning.",
                "steps": ["Review health metadata."],
                "capability_refs": [{"type": "command", "id": "core.operations.get_health"}],
            }
        ],
        "rationale": "Human approval remains authoritative.",
        "evidence": [{"source": "operator_goal", "summary": "Operator requested safe planning."}],
        "confidence": 0.8,
        "assumptions": ["Approval Gate remains the authorization boundary."],
        "risks": [{"severity": "medium", "description": "Backup can fail."}],
        "constraints": ["Planner cannot execute workflows."],
        "success_definition": "A valid metadata-only DecisionPlan is available for review.",
        "provider_trace": {
            "provider_id": None,
            "model": None,
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


def test_create_decision_plan(db_session: Session):
    plan = create_decision_plan(db_session, _valid_payload())

    assert plan.id is not None
    assert plan.root_decision_id == plan.id
    assert plan.status == DecisionPlanStatus.draft.value
    assert plan.revision == 1
    assert plan.primary_path["title"] == "Controlled backup and health verification"
    assert plan.safety_flags["workflow_runs_created"] is False


def test_load_decision_plan(db_session: Session):
    created = create_decision_plan(db_session, _valid_payload())

    loaded = get_decision_plan(db_session, created.id)

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.goal == created.goal


def test_list_decision_plans(db_session: Session):
    first = create_decision_plan(db_session, _valid_payload("First goal"))
    second = create_decision_plan(db_session, _valid_payload("Second goal"))
    update_decision_plan_status(db_session, second, DecisionPlanStatus.generating)

    all_plans = list_decision_plans(db_session)
    generating = list_decision_plans(db_session, status=DecisionPlanStatus.generating)

    assert {plan.id for plan in all_plans} == {first.id, second.id}
    assert [plan.id for plan in generating] == [second.id]


def test_valid_lifecycle_transitions(db_session: Session):
    plan = create_decision_plan(db_session, _valid_payload())

    plan = update_decision_plan_status(db_session, plan, DecisionPlanStatus.generating)
    assert plan.status == DecisionPlanStatus.generating.value

    plan = update_decision_plan_status(db_session, plan, DecisionPlanStatus.validating)
    assert plan.status == DecisionPlanStatus.validating.value

    plan = update_decision_plan_status(db_session, plan, DecisionPlanStatus.proposed)
    assert plan.status == DecisionPlanStatus.proposed.value


@pytest.mark.parametrize(
    "current_status,next_status",
    [
        (DecisionPlanStatus.draft, DecisionPlanStatus.proposed),
        (DecisionPlanStatus.generating, DecisionPlanStatus.proposed),
        (DecisionPlanStatus.validating, DecisionPlanStatus.draft),
        (DecisionPlanStatus.proposed, DecisionPlanStatus.validating),
    ],
)
def test_invalid_lifecycle_transitions(
    db_session: Session,
    current_status: DecisionPlanStatus,
    next_status: DecisionPlanStatus,
):
    plan = create_decision_plan(db_session, _valid_payload())
    plan.status = current_status.value
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)

    with pytest.raises(DecisionPlanValidationError):
        update_decision_plan_status(db_session, plan, next_status)


def test_create_decision_plan_revision(db_session: Session):
    source = create_decision_plan(db_session, _valid_payload())
    revision_payload = _valid_payload("Revised goal")

    revision = create_decision_plan_revision(db_session, source, revision_payload)

    assert revision.id != source.id
    assert revision.parent_decision_plan_id == source.id
    assert revision.root_decision_id == source.root_decision_id
    assert revision.revision == source.revision + 1
    assert revision.status == DecisionPlanStatus.draft.value
    assert revision.approval_request_id is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.pop("success_definition"),
        lambda payload: payload.update({"confidence": 2}),
        lambda payload: payload.update({"status": "approved"}),
        lambda payload: payload["safety_flags"].update({"execution_enabled": True}),
        lambda payload: payload["safety_flags"].update({"approval_requests_created": True}),
        lambda payload: payload["safety_flags"].update({"workflow_runs_created": True}),
        lambda payload: payload.update(
            {
                "alternatives": [
                    {
                        "title": payload["primary_path"]["title"],
                        "summary": payload["primary_path"]["summary"],
                        "steps": ["Duplicate."],
                    }
                ]
            }
        ),
    ],
)
def test_validator_failures(mutate):
    payload = _valid_payload()
    mutate(payload)

    with pytest.raises(DecisionPlanValidationError):
        validate_decision_plan_payload(payload)


def test_create_rejects_invalid_payload_without_persisting(db_session: Session):
    payload = _valid_payload()
    payload["safety_flags"]["workflow_triggered"] = True

    with pytest.raises(DecisionPlanValidationError):
        create_decision_plan(db_session, payload)

    assert db_session.query(DecisionPlan).count() == 0


def test_revision_ignores_payload_parent_and_approval_fields(db_session: Session):
    source = create_decision_plan(db_session, _valid_payload())
    revision_payload = _valid_payload("Revised goal")
    revision_payload["parent_decision_plan_id"] = str(uuid4())
    revision_payload["root_decision_id"] = str(uuid4())
    revision_payload["approval_request_id"] = str(uuid4())
    revision_payload["revision"] = 99
    revision_payload["status"] = DecisionPlanStatus.proposed.value

    revision = create_decision_plan_revision(db_session, source, DecisionPlanCreate.model_validate(revision_payload))

    assert revision.parent_decision_plan_id == source.id
    assert revision.root_decision_id == source.root_decision_id
    assert revision.approval_request_id is None
    assert revision.revision == 2
    assert revision.status == DecisionPlanStatus.draft.value
