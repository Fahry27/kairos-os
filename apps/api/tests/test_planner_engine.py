import json

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from app.core.ai_provider_router import (
    AIProviderRouterDispatchResponse,
    AIProviderSelectionPolicy,
)
from app.core.config import Settings
from app.db.base import Base
from app.models.decision_plan import DecisionPlan
from app.schemas.decision_plan import DecisionPlanCreate, DecisionPlanStatus
from app.schemas.planner import PlannerRequest
from app.services.decision_plan_service import create_decision_plan
from app.services.decision_plan_validator import validate_decision_plan_payload
from app.services.planner_engine import (
    PlannerEngine,
    PlannerOutputError,
    PlannerPersistenceError,
    PlannerProviderError,
    PlannerValidationError,
)


@pytest.fixture()
def db_session():
    engine = sa.create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with LocalSession() as db:
        yield db
    engine.dispose()


def _settings(**updates):
    return Settings(APP_ENV="test").model_copy(
        update={
            "kairos_planner_enabled": True,
            "kairos_ai_enabled": True,
            "kairos_ai_model": "llama3.2:latest",
            "kairos_planner_max_provider_response_chars": 8000,
            **updates,
        }
    )


def _provider_payload(**updates) -> dict:
    payload = {
        "primary_path": {
            "title": "Prepare a reviewed backup plan",
            "summary": "Keep the backup action behind human approval.",
            "steps": ["Review goal.", "Prepare approval metadata."],
            "capability_refs": [{"type": "command", "id": "core.operations.run_backup"}],
        },
        "alternatives": [],
        "rationale": "The safest path preserves the Approval Gate.",
        "evidence": [{"source": "operator_goal", "summary": "The operator requested planning."}],
        "confidence": 0.84,
        "assumptions": ["Approval remains separate from planning."],
        "risks": [{"severity": "medium", "description": "Backup may fail later."}],
        "constraints": ["Planner cannot execute workflows."],
        "success_definition": "A valid DecisionPlan draft is persisted for review.",
    }
    payload.update(updates)
    return payload


def _policy() -> AIProviderSelectionPolicy:
    return AIProviderSelectionPolicy(
        mode="auto",
        selected_provider_id="ai.ollama",
        fallback_enabled=True,
        fallback_order=["ai.ollama"],
        attempts=["ai.ollama:selected"],
        reason="auto_selected",
    )


def _dispatch_response(
    *,
    response_text: str | None = None,
    prompt_sent: bool = True,
    raw_response_metadata: dict | None = None,
) -> AIProviderRouterDispatchResponse:
    return AIProviderRouterDispatchResponse(
        provider_id="ai.ollama",
        model="llama3.2:latest",
        prompt_sent=prompt_sent,
        response_text=response_text if response_text is not None else json.dumps(_provider_payload()),
        raw_response_metadata=raw_response_metadata or {},
        safety_notes=["No execution performed."],
        latency_ms=12,
        truncated=False,
        selected_provider_id="ai.ollama",
        selected_provider_name="Ollama",
        policy=_policy(),
        fallback_used=False,
        provider_attempts=["ai.ollama:selected"],
        network_call_performed=True,
    )


class FakeRouter:
    def __init__(self, response: AIProviderRouterDispatchResponse):
        self.response = response
        self.calls = []

    def dispatch(self, request, settings, plugin_registry, connector_registry):
        self.calls.append(
            {
                "request": request,
                "settings": settings,
                "plugin_registry": plugin_registry,
                "connector_registry": connector_registry,
            }
        )
        return self.response


def test_successful_planning(db_session):
    router = FakeRouter(_dispatch_response())
    engine = PlannerEngine(router=router)

    response = engine.plan(
        db_session,
        PlannerRequest(goal="  Back up Kairos data  ", context={"priority": "high"}),
        _settings(),
    )

    assert response.persisted is True
    assert response.decision_plan.goal == "Back up Kairos data"
    assert response.decision_plan.status == DecisionPlanStatus.draft
    assert response.decision_plan.primary_path.title == "Prepare a reviewed backup plan"
    assert response.provider_attempts == ["ai.ollama:selected"]
    assert len(router.calls) == 1
    assert router.calls[0]["request"].create_approval_requests is False
    assert db_session.query(DecisionPlan).count() == 1


def test_provider_unavailable(db_session):
    router = FakeRouter(
        _dispatch_response(
            prompt_sent=False,
            response_text="",
            raw_response_metadata={"error": "No functional provider is available."},
        )
    )
    engine = PlannerEngine(router=router)

    with pytest.raises(PlannerProviderError):
        engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert db_session.query(DecisionPlan).count() == 0


def test_provider_timeout(db_session):
    router = FakeRouter(
        _dispatch_response(
            response_text="",
            raw_response_metadata={"error": "Timeout after 30s"},
        )
    )
    engine = PlannerEngine(router=router)

    with pytest.raises(PlannerProviderError):
        engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert db_session.query(DecisionPlan).count() == 0


def test_malformed_provider_output(db_session):
    router = FakeRouter(_dispatch_response(response_text="not-json"))
    engine = PlannerEngine(router=router)

    with pytest.raises(PlannerOutputError):
        engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert db_session.query(DecisionPlan).count() == 0


def test_wrapped_provider_output(db_session):
    payload = _provider_payload()
    wrapped_text = f"Here is the plan:\n```json\n{json.dumps(payload)}\n```\nHope this helps!"
    router = FakeRouter(_dispatch_response(response_text=wrapped_text))
    engine = PlannerEngine(router=router)

    response = engine.plan(db_session, {"goal": "Plan something"}, _settings())
    assert response.decision_plan.id is not None
    assert db_session.query(DecisionPlan).count() == 1


def test_validator_rejection(db_session):
    router = FakeRouter(
        _dispatch_response(
            response_text=json.dumps(
                _provider_payload(
                    safety_flags={
                        "execution_enabled": True,
                        "approval_mutation_performed": False,
                        "approval_requests_created": False,
                        "workflow_triggered": False,
                        "workflow_runs_created": False,
                        "connector_calls_performed": False,
                        "data_mutation_performed": False,
                    }
                )
            )
        )
    )
    engine = PlannerEngine(router=router)

    with pytest.raises(PlannerValidationError):
        engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert db_session.query(DecisionPlan).count() == 0


def test_persistence_failure(db_session):
    def failing_create(db, payload):
        raise RuntimeError("database unavailable")

    router = FakeRouter(_dispatch_response())
    engine = PlannerEngine(router=router, create_plan=failing_create)

    with pytest.raises(PlannerPersistenceError):
        engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert db_session.query(DecisionPlan).count() == 0


def test_planner_cannot_bypass_validator(db_session):
    calls = []

    def spy_validator(payload) -> DecisionPlanCreate:
        calls.append(payload)
        return validate_decision_plan_payload(payload)

    router = FakeRouter(_dispatch_response())
    engine = PlannerEngine(router=router, validator=spy_validator)

    response = engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert response.decision_plan.id is not None
    assert len(calls) == 1


def test_planner_cannot_bypass_service(db_session):
    calls = []

    def spy_create(db, payload):
        calls.append(payload)
        return create_decision_plan(db, payload)

    router = FakeRouter(_dispatch_response())
    engine = PlannerEngine(router=router, create_plan=spy_create)

    response = engine.plan(db_session, {"goal": "Plan something"}, _settings())

    assert response.decision_plan.id is not None
    assert len(calls) == 1


def test_provider_output_size_limit(db_session):
    router = FakeRouter(_dispatch_response(response_text=json.dumps(_provider_payload())))
    engine = PlannerEngine(router=router)

    with pytest.raises(PlannerOutputError):
        engine.plan(
            db_session,
            {"goal": "Plan something"},
            _settings(kairos_planner_max_provider_response_chars=5),
        )

    assert db_session.query(DecisionPlan).count() == 0
