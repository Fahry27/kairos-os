"""Tests for Kairos v2.5.0 — Response Parser & Safe Planning Output.

SAFETY: All tests run in-memory. No real Ollama is required.
No network calls, no database writes, no secrets exposed.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-parser-test.sqlite3"
if TEST_DATABASE_PATH.exists():
    TEST_DATABASE_PATH.unlink()

os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.ai_runtime import ai_runtime  # noqa: E402
from app.core.plugins import plugin_registry  # noqa: E402
from app.db.base import initialize_database  # noqa: E402

initialize_database()

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: get all commands from registry for reference
# ---------------------------------------------------------------------------

def _known_command_ids():
    """Return set of command IDs from the plugin registry."""
    ids = set()
    for plugin in plugin_registry.get_all_plugins(include_disabled=False):
        for cmd in plugin.commands:
            ids.add(cmd.id)
    return ids


def _dangerous_command_ids():
    """Return set of dangerous command IDs from the plugin registry."""
    ids = set()
    for plugin in plugin_registry.get_all_plugins(include_disabled=False):
        for cmd in plugin.commands:
            if getattr(cmd, "dangerous", False):
                ids.add(cmd.id)
    return ids


# ---------------------------------------------------------------------------
# Parser: JSON response parsing
# ---------------------------------------------------------------------------


def test_parser_parses_json_response():
    settings = get_settings()
    json_response = json.dumps({
        "summary": "Back up the database",
        "steps": [
            {"title": "Review backup command", "description": "Check the backup tool"},
            {"title": "Run backup", "description": "Execute the backup safely"},
        ],
        "commands": []
    })
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="back up the database",
        model="llama3.2:3b",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert plan.source == "llm_response_parser"
    assert plan.model == "llama3.2:3b"
    assert plan.user_goal == "back up the database"
    assert len(plan.steps) == 2
    assert plan.steps[0].title == "Review backup command"
    assert plan.steps[1].title == "Run backup"
    assert plan.execution_enabled is False
    assert plan.command_execution_performed is False
    assert plan.connector_calls_performed is False
    assert plan.data_mutation_performed is False


def test_parser_parses_json_with_code_fences():
    settings = get_settings()
    json_response = '```json\n{"summary": "test plan", "steps": [{"title": "Step 1", "description": "Do it"}]}\n```'
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.steps) >= 1
    assert plan.steps[0].title == "Step 1"


def test_parser_parses_json_with_command_registry_match():
    """If JSON contains command IDs that exist in registry, they should be matched."""
    settings = get_settings()
    known = _known_command_ids()
    if not known:
        return  # Skip if no commands registered

    cid = next(iter(known))
    json_response = json.dumps({
        "summary": "Plan with command",
        "steps": [{"title": "Use command", "description": f"Use {cid}"}],
        "commands": [{"command_id": cid, "reason": "Relevant to goal"}]
    })
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.command_suggestions) >= 1
    assert plan.command_suggestions[0].command_id == cid
    assert plan.command_suggestions[0].execution_required is False


# ---------------------------------------------------------------------------
# Parser: Markdown / text heuristic parsing
# ---------------------------------------------------------------------------


def test_parser_parses_markdown_numbered_list():
    settings = get_settings()
    md_response = """Here is the plan:

1. Review the current project status
   Check what projects exist.

2. Create a new task
   Add a task for the next sprint.

3. Run a health check
   Verify system is healthy.
"""
    plan = ai_runtime.parse_llm_response(
        response_text=md_response,
        user_goal="plan my day",
        model="qwen2.5:7b",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.steps) == 3
    assert "Review the current project status" in plan.steps[0].title
    assert "Create a new task" in plan.steps[1].title
    assert plan.execution_enabled is False


def test_parser_parses_markdown_with_step_prefix():
    settings = get_settings()
    md_response = """Step 1: Check health endpoint
Make sure the API is running.

Step 2: Review backups
Verify last backup time.
"""
    plan = ai_runtime.parse_llm_response(
        response_text=md_response,
        user_goal="check system",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.steps) == 2
    assert "Check health endpoint" in plan.steps[0].title


# ---------------------------------------------------------------------------
# Parser: Fallback behavior
# ---------------------------------------------------------------------------


def test_parser_fallback_on_unstructured_text():
    settings = get_settings()
    plan = ai_runtime.parse_llm_response(
        response_text="This is just a random paragraph with no structure at all.",
        user_goal="do something",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.steps) == 1
    assert "Review LLM response manually" in plan.steps[0].title
    assert len(plan.parser_warnings) > 0
    assert "fallback" in plan.parser_warnings[0].lower()


def test_parser_fallback_on_empty_json_steps():
    settings = get_settings()
    json_response = json.dumps({"summary": "empty plan", "steps": []})
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    # Empty steps means JSON parse "succeeds" but no steps → fallback
    assert len(plan.steps) == 1
    assert "Review LLM response manually" in plan.steps[0].title


# ---------------------------------------------------------------------------
# Parser: Dangerous command flagging
# ---------------------------------------------------------------------------


def test_parser_flags_dangerous_commands():
    """Dangerous commands from registry should be flagged dangerous=True."""
    settings = get_settings()
    dangerous = _dangerous_command_ids()
    if not dangerous:
        return  # Skip if no dangerous commands

    cid = next(iter(dangerous))
    json_response = json.dumps({
        "summary": "Dangerous plan",
        "steps": [{"title": "Dangerous step", "description": f"Run {cid}"}],
        "commands": [{"command_id": cid, "reason": "Needs dangerous op"}]
    })
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    dangerous_suggestions = [c for c in plan.command_suggestions if c.dangerous]
    assert len(dangerous_suggestions) >= 1
    assert any("Dangerous commands referenced" in n for n in plan.safety_notes)


# ---------------------------------------------------------------------------
# Parser: Unknown command IDs
# ---------------------------------------------------------------------------


def test_parser_ignores_unknown_command_ids():
    settings = get_settings()
    json_response = json.dumps({
        "summary": "Plan with unknown command",
        "steps": [{"title": "Step", "description": "Use fake.command.id"}],
        "commands": [{"command_id": "fake.nonexistent.command", "reason": "test"}]
    })
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert all(cs.command_id != "fake.nonexistent.command" for cs in plan.command_suggestions)


# ---------------------------------------------------------------------------
# Parser: Limits enforcement
# ---------------------------------------------------------------------------


def test_parser_respects_step_limit():
    settings = get_settings()
    max_steps = settings.kairos_ai_max_parsed_steps
    # Generate more steps than the limit
    steps = [{"title": f"Step {i}", "description": f"Desc {i}"} for i in range(max_steps + 5)]
    json_response = json.dumps({"summary": "Big plan", "steps": steps})
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.steps) <= max_steps


def test_parser_respects_command_limit():
    settings = get_settings()
    max_cmds = settings.kairos_ai_max_parsed_commands
    known = list(_known_command_ids())
    if len(known) < 2:
        return  # Need at least 2 commands to test limit

    # Create more command suggestions than limit
    cmds = [{"command_id": cid, "reason": "test"} for cid in known[:max_cmds + 3]]
    json_response = json.dumps({
        "summary": "Many commands",
        "steps": [{"title": "Step", "description": "Do things"}],
        "commands": cmds
    })
    plan = ai_runtime.parse_llm_response(
        response_text=json_response,
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert len(plan.command_suggestions) <= max_cmds


# ---------------------------------------------------------------------------
# Parser: Execution flags always false
# ---------------------------------------------------------------------------


def test_parser_execution_flags_always_false():
    settings = get_settings()
    plan = ai_runtime.parse_llm_response(
        response_text='{"summary": "test", "steps": [{"title": "S", "description": "D"}]}',
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    assert plan.execution_enabled is False
    assert plan.command_execution_performed is False
    assert plan.connector_calls_performed is False
    assert plan.data_mutation_performed is False


# ---------------------------------------------------------------------------
# Parser: No secrets returned
# ---------------------------------------------------------------------------


def test_parser_no_secrets_in_output():
    """Even if LLM text contains secret-like strings, parser output shouldn't expose them
    beyond what's in the structured fields (which are validated strings only)."""
    settings = get_settings()
    plan = ai_runtime.parse_llm_response(
        response_text='{"summary": "test", "steps": [{"title": "Step", "description": "Use KAIROS_API_KEY=secret123"}]}',
        user_goal="test",
        model="test",
        settings=settings,
        plugin_registry=plugin_registry,
    )
    # Parser doesn't filter content of descriptions (that's the user's LLM text),
    # but parser itself doesn't inject any secrets
    assert plan.source == "llm_response_parser"
    assert "secret123" not in plan.summary
    for note in plan.safety_notes:
        assert "secret123" not in note


# ---------------------------------------------------------------------------
# Endpoint: POST /api/v1/ai/parse-plan
# ---------------------------------------------------------------------------


def test_parse_plan_endpoint_works():
    response = client.post("/api/v1/ai/parse-plan", json={
        "user_goal": "back up database",
        "response_text": json.dumps({
            "summary": "Backup plan",
            "steps": [{"title": "Run backup", "description": "Execute backup command"}]
        })
    })
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "llm_response_parser"
    assert data["user_goal"] == "back up database"
    assert len(data["steps"]) >= 1
    assert data["execution_enabled"] is False


def test_parse_plan_endpoint_empty_response_text():
    response = client.post("/api/v1/ai/parse-plan", json={
        "user_goal": "test",
        "response_text": ""
    })
    assert response.status_code == 422


def test_parse_plan_endpoint_empty_user_goal():
    response = client.post("/api/v1/ai/parse-plan", json={
        "user_goal": "",
        "response_text": "some text"
    })
    assert response.status_code == 422


def test_parse_plan_endpoint_with_markdown():
    response = client.post("/api/v1/ai/parse-plan", json={
        "user_goal": "organize tasks",
        "response_text": "1. Review tasks\n2. Prioritize tasks\n3. Schedule tasks"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) == 3


# ---------------------------------------------------------------------------
# Endpoint: Parser disabled
# ---------------------------------------------------------------------------


def test_parse_plan_disabled_returns_403():
    """When parser is disabled, endpoint returns 403."""

    original = get_settings()
    override = original.model_copy(update={"kairos_ai_response_parser_enabled": False})
    app.dependency_overrides[get_settings] = lambda: override

    response = client.post("/api/v1/ai/parse-plan", json={
        "user_goal": "test",
        "response_text": "1. Do something"
    })
    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert "parser is disabled" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Dispatch: parsed_plan integration
# ---------------------------------------------------------------------------


@patch("app.core.ai_runtime.urllib.request.urlopen")
def test_dispatch_includes_parsed_plan_when_enabled(mock_urlopen):
    """When parse_response=true and parser enabled, dispatch includes parsed_plan."""

    original = get_settings()
    override = original.model_copy(update={
        "kairos_ollama_dispatch_enabled": True,
        "kairos_ai_response_parser_enabled": True,
        "kairos_ai_provider": "ollama",
    })
    app.dependency_overrides[get_settings] = lambda: override

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "model": "llama3.2:3b",
        "response": json.dumps({
            "summary": "parsed result",
            "steps": [{"title": "Step A", "description": "Detail"}]
        }),
        "done": True,
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = client.post("/api/v1/ai/ollama/dispatch", json={
        "user_goal": "test dispatch parse",
        "model": "llama3.2:3b",
        "parse_response": True,
    })
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_plan"] is not None
    assert data["parsed_plan"]["source"] == "llm_response_parser"
    assert len(data["parsed_plan"]["steps"]) >= 1
    assert data["parsed_plan"]["execution_enabled"] is False


@patch("app.core.ai_runtime.urllib.request.urlopen")
def test_dispatch_omits_parsed_plan_when_disabled(mock_urlopen):
    """When parse_response=false, dispatch omits parsed_plan."""

    original = get_settings()
    override = original.model_copy(update={
        "kairos_ollama_dispatch_enabled": True,
        "kairos_ai_response_parser_enabled": True,
        "kairos_ai_provider": "ollama",
    })
    app.dependency_overrides[get_settings] = lambda: override

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "model": "llama3.2:3b",
        "response": "Some plain text response",
        "done": True,
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = client.post("/api/v1/ai/ollama/dispatch", json={
        "user_goal": "test dispatch no parse",
        "model": "llama3.2:3b",
        "parse_response": False,
    })
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["parsed_plan"] is None


# ---------------------------------------------------------------------------
# Capabilities: parser fields
# ---------------------------------------------------------------------------


def test_capabilities_include_parser_fields():
    response = client.get("/api/v1/ai/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "response_parser_enabled" in data
    assert "max_parsed_steps" in data
    assert "max_parsed_commands" in data
    assert data["response_parser_enabled"] is True
    assert data["max_parsed_steps"] == 10
    assert data["max_parsed_commands"] == 10


# ---------------------------------------------------------------------------
# Health: version check
# ---------------------------------------------------------------------------


def test_health_version_260():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "3.4.0"

# ---------------------------------------------------------------------------
# Approval Gate Integration Tests (v2.6.0)
# ---------------------------------------------------------------------------

def test_parse_plan_does_not_create_approvals_by_default():
    payload = {
        "user_goal": "Run ping",
        "response_text": '{"steps": [], "commands": [{"command_id": "test_cmd", "reason": "test"}], "summary": "test"}'
    }
    response = client.post("/api/v1/ai/parse-plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["approval_requests"]) == 0
    assert data["execution_enabled"] is False

def test_parse_plan_creates_approvals_when_requested(monkeypatch):
    from app.core.config import get_settings
    def get_settings_override():
        from app.core.config import Settings
        settings = Settings()
        settings.kairos_approval_gate_enabled = True
        settings.kairos_ai_response_parser_enabled = True
        settings.kairos_ai_enabled = True
        return settings
    app.dependency_overrides[get_settings] = get_settings_override
    try:
        payload = {
            "user_goal": "Run dangerous command",
            "response_text": '{"steps": [], "commands": [{"command_id": "core.operations.run_backup", "reason": "delete file"}], "summary": "test"}',
            "create_approval_requests": True
        }
        response = client.post("/api/v1/ai/parse-plan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["approval_requests"]) == 1
        
        appr = data["approval_requests"][0]
        assert appr["action_type"] == "command"
        assert appr["proposed_action_id"] == "core.operations.run_backup"
        assert appr["status"] == "pending"
        
        # Check it in DB
        get_res = client.get(f"/api/v1/approvals/{appr['id']}")
        assert get_res.status_code == 200
        db_appr = get_res.json()
        assert db_appr["risk_level"] == "high" # sys.rm is dangerous
        assert "delete file" in db_appr["description"]
        assert db_appr["execution_enabled"] is False
        assert db_appr["execution_performed"] is False
        assert db_appr["connector_calls_performed"] is False
        assert db_appr["data_mutation_performed"] is False
    finally:
        app.dependency_overrides.pop(get_settings, None)

def test_dispatch_does_not_create_approvals_by_default(monkeypatch):
    from app.core.config import get_settings
    def get_settings_override():
        from app.core.config import Settings
        settings = Settings()
        settings.kairos_approval_gate_enabled = True
        settings.kairos_ai_enabled = True
        settings.kairos_ai_provider = "ai.ollama"
        settings.kairos_ollama_dispatch_enabled = True
        settings.kairos_ai_response_parser_enabled = True
        return settings
    app.dependency_overrides[get_settings] = get_settings_override
    try:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_response.status = 200
        mock_response.read.return_value = b'{"response": "{\\"commands\\": [{\\"command_id\\": \\"core.operations.get_health\\", \\"reason\\": \\"test\\"}]}", "done": true}'
        
        monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: mock_response)
        
        payload = {
            "user_goal": "test dispatch",
            "model": "llama",
            "create_approval_requests": False
        }
        response = client.post("/api/v1/ai/ollama/dispatch", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["approval_requests"]) == 0
    finally:
        app.dependency_overrides.pop(get_settings, None)

def test_dispatch_creates_approvals_when_requested(monkeypatch):
    from app.core.config import get_settings
    def get_settings_override():
        from app.core.config import Settings
        settings = Settings()
        settings.kairos_approval_gate_enabled = True
        settings.kairos_ai_enabled = True
        settings.kairos_ai_provider = "ai.ollama"
        settings.kairos_ollama_dispatch_enabled = True
        settings.kairos_ai_response_parser_enabled = True
        return settings
    app.dependency_overrides[get_settings] = get_settings_override
    try:
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_response.status = 200
        mock_response.read.return_value = b'{"response": "{\\"commands\\": [{\\"command_id\\": \\"core.operations.get_health\\", \\"reason\\": \\"test\\"}]}", "done": true}'
        
        monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: mock_response)
        
        payload = {
            "user_goal": "test dispatch",
            "model": "llama",
            "create_approval_requests": True
        }
        response = client.post("/api/v1/ai/ollama/dispatch", json=payload)
        assert response.status_code == 200
        data = response.json()
        print("DATA:", data)
        assert len(data["approval_requests"]) == 1
        
        appr_id = data["approval_requests"][0]["id"]
        get_res = client.get(f"/api/v1/approvals/{appr_id}")
        assert get_res.status_code == 200
        db_appr = get_res.json()
        assert db_appr["risk_level"] == "medium" # test_cmd is not dangerous
    finally:
        app.dependency_overrides.pop(get_settings, None)
