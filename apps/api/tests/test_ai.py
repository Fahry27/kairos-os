import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-ai-test.sqlite3"
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings, Settings  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /api/v1/ai
# ---------------------------------------------------------------------------


def test_ai_info_endpoint():
    response = client.get("/api/v1/ai")
    assert response.status_code == 200
    data = response.json()
    assert "ai_enabled" in data
    assert "provider" in data
    assert "planning_enabled" in data
    # Hard gate — must always be False in v2.0/2.1
    assert data["execution_enabled"] is False
    assert data["version"] == "2.5.0"


# ---------------------------------------------------------------------------
# GET /api/v1/ai/providers
# ---------------------------------------------------------------------------


def test_ai_providers_list_includes_ollama():
    response = client.get("/api/v1/ai/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    ids = [p["id"] for p in data]
    # Ollama is the only enabled=true provider
    assert "ai.ollama" in ids


def test_ai_providers_list_disabled_by_default():
    """Disabled providers should NOT appear in the default listing."""
    response = client.get("/api/v1/ai/providers")
    data = response.json()
    ids = [p["id"] for p in data]
    assert "ai.openai_codex" not in ids
    assert "ai.openai" not in ids
    assert "ai.openrouter" not in ids


def test_ai_providers_list_include_disabled():
    """With include_disabled=true, all four providers should be returned."""
    response = client.get("/api/v1/ai/providers?include_disabled=true")
    assert response.status_code == 200
    data = response.json()
    ids = [p["id"] for p in data]
    assert "ai.ollama" in ids
    assert "ai.openai_codex" in ids
    assert "ai.openai" in ids
    assert "ai.openrouter" in ids
    # Anthropic is NOT included per design decision
    assert "ai.anthropic" not in ids


def test_ai_no_anthropic_provider():
    """Confirm Anthropic is never present, even with include_disabled."""
    response = client.get("/api/v1/ai/providers?include_disabled=true")
    data = response.json()
    assert all(p["id"] != "ai.anthropic" for p in data)


# ---------------------------------------------------------------------------
# GET /api/v1/ai/providers/{provider_id}
# ---------------------------------------------------------------------------


def test_ai_provider_detail_ollama():
    response = client.get("/api/v1/ai/providers/ai.ollama")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ai.ollama"
    assert data["provider_type"] == "local"
    assert data["supports_local"] is True
    assert data["auth_type"] == "none"
    assert data["enabled"] is True


def test_ai_provider_detail_openai_codex():
    """openai_codex must exist as a disabled metadata stub."""
    response = client.get("/api/v1/ai/providers/ai.openai_codex")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ai.openai_codex"
    assert data["enabled"] is False
    assert data["supports_local"] is False
    # No secrets, no real credentials
    assert data.get("api_key") is None


def test_ai_provider_unknown_returns_404():
    response = client.get("/api/v1/ai/providers/ai.nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET /api/v1/ai/capabilities
# ---------------------------------------------------------------------------


def test_ai_capabilities_fields():
    response = client.get("/api/v1/ai/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "ai_enabled" in data
    assert "provider" in data
    assert "planning_enabled" in data
    assert "execution_enabled" in data
    assert "available_plugins" in data
    assert "available_commands" in data
    assert "available_connectors" in data
    assert "dangerous_commands" in data
    assert "provider_reachable" in data
    assert "provider_checked" in data
    assert "provider_readiness_message" in data
    assert "model_count" in data
    assert "discovered_models_enabled" in data
    assert "configured_model_available" in data
    
    # Dry run defaults
    assert data["dry_run_enabled"] is True
    assert data["max_context_commands"] == 20
    assert data["max_context_connectors"] == 20
    assert data["max_context_plugins"] == 20
    
    # Dispatch defaults
    assert data["ollama_dispatch_enabled"] is False
    assert data["ollama_generate_path"] == "/api/generate"
    assert data["ollama_request_timeout_seconds"] == 30
    assert data["ollama_max_prompt_chars"] == 12000
    assert data["ollama_max_response_chars"] == 8000
    
    # Parser defaults (v2.5.0)
    assert data["response_parser_enabled"] is True
    assert data["max_parsed_steps"] == 10
    assert data["max_parsed_commands"] == 10


def test_ai_capabilities_execution_always_false():
    """Execution must always be False — hard-gated regardless of settings."""
    response = client.get("/api/v1/ai/capabilities")
    data = response.json()
    assert data["execution_enabled"] is False


def test_ai_capabilities_counts_positive():
    response = client.get("/api/v1/ai/capabilities")
    data = response.json()
    assert data["available_plugins"] >= 4   # 4 built-in plugins
    assert data["available_commands"] >= 8  # built-in commands
    assert data["available_connectors"] >= 9
    assert data["dangerous_commands"] >= 1  # run_backup is dangerous


# ---------------------------------------------------------------------------
# POST /api/v1/ai/plan
# ---------------------------------------------------------------------------


def test_ai_plan_basic_goal():
    response = client.post("/api/v1/ai/plan", json={"user_goal": "I want to manage my tasks"})
    assert response.status_code == 200
    data = response.json()
    assert "goal" in data
    assert "summary" in data
    assert "suggested_steps" in data
    assert "suggested_commands" in data
    assert "safety_notes" in data
    # Hard gate
    assert data["execution_enabled"] is False
    assert data["requires_approval"] is True


def test_ai_plan_never_has_execution_required_true():
    """No suggested command may have execution_required=True."""
    for goal in [
        "create a project",
        "run backup",
        "search memories",
        "get system health",
        "do something completely unknown xyz123",
    ]:
        response = client.post("/api/v1/ai/plan", json={"user_goal": goal})
        assert response.status_code == 200
        data = response.json()
        # Top-level hard gate
        assert data["execution_enabled"] is False
        # Per-command hard gate
        for cmd in data.get("suggested_commands", []):
            assert cmd["execution_required"] is False, (
                f"execution_required=True found for command {cmd['command_id']} on goal '{goal}'"
            )


def test_ai_plan_dangerous_commands_flagged():
    """Goals touching backup / admin must surface dangerous=true."""
    response = client.post("/api/v1/ai/plan", json={"user_goal": "run a backup of the database"})
    assert response.status_code == 200
    data = response.json()
    dangerous = [c for c in data["suggested_commands"] if c["dangerous"]]
    assert len(dangerous) >= 1, "Expected at least one dangerous command for a backup goal"
    # Dangerous warning must appear in safety_notes
    assert any("DANGEROUS" in note for note in data["safety_notes"])


def test_ai_plan_unknown_goal_returns_safe_response():
    """Unrecognised goal must return safe generic guidance, not raise an error."""
    response = client.post(
        "/api/v1/ai/plan",
        json={"user_goal": "xyzzy unknown frobnicate 12345"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["execution_enabled"] is False
    assert len(data["suggested_steps"]) >= 1
    assert len(data["safety_notes"]) >= 1


def test_ai_plan_with_context():
    response = client.post(
        "/api/v1/ai/plan",
        json={"user_goal": "create a project", "context": {"priority": "high"}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["execution_enabled"] is False


# ---------------------------------------------------------------------------
# AI disabled behavior
# ---------------------------------------------------------------------------


def test_ai_disabled_providers_returns_empty():
    def override():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_AI_ENABLED=False,
        )

    app.dependency_overrides[get_settings] = override
    try:
        response = client.get("/api/v1/ai/providers")
        assert response.status_code == 200
        assert response.json() == []

        response = client.get("/api/v1/ai/providers/ai.ollama")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_ai_disabled_plan_returns_503():
    def override():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_AI_ENABLED=False,
        )

    app.dependency_overrides[get_settings] = override
    try:
        response = client.post("/api/v1/ai/plan", json={"user_goal": "create a task"})
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_ai_planning_disabled_plan_returns_503():
    def override():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_AI_PLANNING_ENABLED=False,
        )

    app.dependency_overrides[get_settings] = override
    try:
        response = client.post("/api/v1/ai/plan", json={"user_goal": "create a task"})
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()


def test_ai_info_disabled_returns_ai_enabled_false():
    def override():
        return Settings(
            APP_ENV="test",
            DATABASE_URL=f"sqlite:///{TEST_DATABASE_PATH}",
            KAIROS_AI_ENABLED=False,
        )

    app.dependency_overrides[get_settings] = override
    try:
        response = client.get("/api/v1/ai")
        assert response.status_code == 200
        data = response.json()
        assert data["ai_enabled"] is False
        assert data["execution_enabled"] is False
    finally:
        app.dependency_overrides.clear()


def test_no_secrets_returned_in_any_ai_response():
    """Verify no credential-like fields appear in any AI response."""
    secret_keys = {"api_key", "token", "secret", "password", "credential"}
    endpoints = [
        "/api/v1/ai",
        "/api/v1/ai/capabilities",
        "/api/v1/ai/providers",
        "/api/v1/ai/providers/ai.ollama",
        "/api/v1/ai/providers?include_disabled=true",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        for sk in secret_keys:
            # auth_type field is fine; we're checking for actual secret values being returned
            # Just ensure none of these appear as top-level response keys in provider manifests
            pass
        # No actual secrets should appear in manifest metadata notes
        for provider_data in (response.json() if isinstance(response.json(), list) else [response.json()]):
            if isinstance(provider_data, dict):
                for sk in secret_keys:
                    assert sk not in provider_data, f"Found secret key '{sk}' in response from {endpoint}"
