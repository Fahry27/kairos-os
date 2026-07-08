from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_prompt_dry_run_success():
    payload = {
        "user_goal": "Turn on the living room lights",
        "preferred_model": "llama3:latest",
        "include_commands": True,
        "include_plugins": True,
        "include_connectors": True
    }
    
    response = client.post("/api/v1/ai/prompt/dry-run", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["dry_run"] is True
    assert data["execution_enabled"] is False
    assert data["network_call_performed"] is False
    assert data["user_goal"] == "Turn on the living room lights"
    assert data["model"] == "llama3:latest"
    assert data["provider_id"] == "ai.openrouter"
    
    assert isinstance(data["system_instructions"], list)
    assert len(data["system_instructions"]) > 0
    assert "You are operating in DRY-RUN mode." in data["system_instructions"]
    
    assert "included_commands" in data
    assert "included_plugins" in data
    assert "included_connectors" in data
    
    # Check max limits are respected (20 is default)
    assert len(data["included_commands"]) <= 20
    assert len(data["included_plugins"]) <= 20
    assert len(data["included_connectors"]) <= 20
    
    # Check safety notes
    assert isinstance(data["safety_policy"], list)
    assert "No command execution permitted." in data["safety_policy"]

def test_prompt_dry_run_empty_goal():
    payload = {
        "user_goal": "   ",
        "include_commands": True
    }
    
    response = client.post("/api/v1/ai/prompt/dry-run", json=payload)
    assert response.status_code == 422
    assert "user_goal cannot be empty" in response.json()["detail"]
