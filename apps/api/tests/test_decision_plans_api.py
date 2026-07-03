import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.api.v1.endpoints.decision_plans import get_planner_engine
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.main import app
from app.schemas.decision_plan import DecisionPlanRead, DecisionPlanStatus
from app.schemas.planner import PlannerResponse
from app.services.decision_plan_service import create_decision_plan
from app.services.planner_engine import (
    PlannerOutputError,
    PlannerProviderError,
    PlannerValidationError,
)

client = TestClient(app)


def _valid_payload(goal: str = "Back up Kairos data and confirm health") -> dict:
    return {
        "goal": goal,
        "status": DecisionPlanStatus.draft.value,
        "primary_path": {
            "title": "Prepare reviewed backup plan",
            "summary": "Keep backup execution behind approval.",
            "steps": ["Review goal.", "Prepare metadata-only plan."],
            "capability_refs": [{"type": "command", "id": "core.operations.run_backup"}],
        },
        "alternatives": [],
        "rationale": "Planning should preserve human authority.",
        "evidence": [{"source": "operator_goal", "summary": "Operator requested planning."}],
        "confidence": 0.8,
        "assumptions": ["Approval remains separate."],
        "risks": [{"severity": "medium", "description": "Backup may fail later."}],
        "constraints": ["Planner cannot execute workflows."],
        "success_definition": "A DecisionPlan draft exists for operator review.",
        "provider_trace": {
            "provider_id": "ai.ollama",
            "model": "llama3.2:latest",
            "dispatch_used": True,
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
    }


def _settings(api_key: str | None = None) -> Settings:
    return Settings(APP_ENV="test").model_copy(
        update={
            "kairos_api_key": api_key,
            "kairos_planner_enabled": True,
            "kairos_ai_enabled": True,
        }
    )


def _install_db_override():
    engine = sa.create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sa.orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return engine, SessionLocal


class FakePlannerEngine:
    def __init__(self, failure: Exception | None = None):
        self.failure = failure
        self.calls = []

    def plan(self, db, request, settings):
        self.calls.append({"db": db, "request": request, "settings": settings})
        if self.failure:
            raise self.failure
        plan = create_decision_plan(db, _valid_payload(request.goal))
        return PlannerResponse(
            decision_plan=DecisionPlanRead.model_validate(plan),
            provider_attempts=["ai.ollama:selected"],
            warnings=[],
        )


def _clear_overrides(engine):
    app.dependency_overrides.clear()
    engine.dispose()


def test_create_decision_plan_endpoint():
    engine, _ = _install_db_override()
    fake_engine = FakePlannerEngine()
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_planner_engine] = lambda: fake_engine
    try:
        response = client.post(
            "/api/v1/decision-plans",
            json={"goal": "Back up Kairos data", "context": {"priority": "high"}},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["goal"] == "Back up Kairos data"
        assert data["status"] == "draft"
        assert data["primary_path"]["title"] == "Prepare reviewed backup plan"
        assert data["safety_flags"]["workflow_runs_created"] is False
        assert len(fake_engine.calls) == 1
    finally:
        _clear_overrides(engine)


def test_list_decision_plans_endpoint():
    engine, SessionLocal = _install_db_override()
    app.dependency_overrides[get_settings] = lambda: _settings()
    try:
        with SessionLocal() as db:
            create_decision_plan(db, _valid_payload("First plan"))
            create_decision_plan(db, _valid_payload("Second plan"))

        response = client.get("/api/v1/decision-plans", params={"offset": 0, "limit": 100})

        assert response.status_code == 200
        goals = {item["goal"] for item in response.json()}
        assert goals == {"First plan", "Second plan"}
    finally:
        _clear_overrides(engine)


def test_get_decision_plan_endpoint():
    engine, SessionLocal = _install_db_override()
    app.dependency_overrides[get_settings] = lambda: _settings()
    try:
        with SessionLocal() as db:
            plan = create_decision_plan(db, _valid_payload("Find this plan"))
            plan_id = str(plan.id)

        response = client.get(f"/api/v1/decision-plans/{plan_id}")

        assert response.status_code == 200
        assert response.json()["id"] == plan_id
        assert response.json()["goal"] == "Find this plan"
    finally:
        _clear_overrides(engine)


def test_get_decision_plan_missing_returns_404():
    engine, _ = _install_db_override()
    app.dependency_overrides[get_settings] = lambda: _settings()
    try:
        response = client.get("/api/v1/decision-plans/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert response.json()["detail"] == "DecisionPlan not found"
    finally:
        _clear_overrides(engine)


def test_create_decision_plan_invalid_request_returns_422():
    engine, _ = _install_db_override()
    fake_engine = FakePlannerEngine()
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_planner_engine] = lambda: fake_engine
    try:
        response = client.post("/api/v1/decision-plans", json={"goal": ""})

        assert response.status_code == 422
        assert fake_engine.calls == []
    finally:
        _clear_overrides(engine)


def test_decision_plans_authentication_required():
    engine, _ = _install_db_override()
    app.dependency_overrides[get_settings] = lambda: _settings(api_key="secret")
    try:
        missing = client.get("/api/v1/decision-plans")
        invalid = client.get("/api/v1/decision-plans", headers={"X-Kairos-API-Key": "wrong"})
        valid = client.get("/api/v1/decision-plans", headers={"X-Kairos-API-Key": "secret"})

        assert missing.status_code == 401
        assert invalid.status_code == 401
        assert valid.status_code == 200
    finally:
        _clear_overrides(engine)


def test_create_decision_plan_provider_failure_returns_503():
    engine, _ = _install_db_override()
    fake_engine = FakePlannerEngine(failure=PlannerProviderError("provider unavailable"))
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_planner_engine] = lambda: fake_engine
    try:
        response = client.post("/api/v1/decision-plans", json={"goal": "Plan something"})

        assert response.status_code == 503
        assert response.json()["detail"] == "provider unavailable"
    finally:
        _clear_overrides(engine)


def test_create_decision_plan_validation_failure_returns_422():
    engine, _ = _install_db_override()
    fake_engine = FakePlannerEngine(failure=PlannerValidationError("validation failed"))
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_planner_engine] = lambda: fake_engine
    try:
        response = client.post("/api/v1/decision-plans", json={"goal": "Plan something"})

        assert response.status_code == 422
        assert response.json()["detail"] == "validation failed"
    finally:
        _clear_overrides(engine)


def test_create_decision_plan_malformed_output_returns_422():
    engine, _ = _install_db_override()
    fake_engine = FakePlannerEngine(failure=PlannerOutputError("malformed output"))
    app.dependency_overrides[get_settings] = lambda: _settings()
    app.dependency_overrides[get_planner_engine] = lambda: fake_engine
    try:
        response = client.post("/api/v1/decision-plans", json={"goal": "Plan something"})

        assert response.status_code == 422
        assert response.json()["detail"] == "malformed output"
    finally:
        _clear_overrides(engine)


def test_openapi_includes_decision_plan_paths():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/decision-plans" in paths
    assert "/api/v1/decision-plans/{decision_plan_id}" in paths
