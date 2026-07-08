import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings

client = TestClient(app)

def test_dispatch_disabled_returns_403():
    # Dispatch is disabled by default
    response = client.post("/api/v1/ai/ollama/dispatch", json={"user_goal": "test"})
    assert response.status_code == 403
    assert "Ollama local dispatch is disabled" in response.json()["detail"]

@patch("app.core.ai_runtime.urllib.request.urlopen")
def test_dispatch_success(mock_urlopen):
    # Enable dispatch with Ollama provider
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"kairos_ollama_dispatch_enabled": True, "kairos_ai_provider": "ollama"}
    )
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "model": "llama3.2:3b",
        "created_at": "2026-06-28T00:00:00Z",
        "response": "Here is the plan.",
        "done": True,
        "total_duration": 1000
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_response

    payload = {
        "user_goal": "Do something",
        "model": "llama3.2:3b"
    }
    
    response = client.post("/api/v1/ai/ollama/dispatch", json=payload)
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "ai.ollama"
    assert data["model"] == "llama3.2:3b"
    assert data["prompt_sent"] is True
    assert data["response_text"] == "Here is the plan."
    assert "total_duration" in data["raw_response_metadata"]
    
    # Check strict flags
    assert data["execution_enabled"] is False
    assert data["command_execution_performed"] is False
    assert data["connector_calls_performed"] is False
    assert data["data_mutation_performed"] is False
    assert data["network_call_performed"] is True

@patch("app.core.ai_runtime.urllib.request.urlopen")
def test_dispatch_truncation(mock_urlopen):
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "kairos_ollama_dispatch_enabled": True,
            "kairos_ai_provider": "ollama",
            "kairos_ollama_max_response_chars": 10
        }
    )
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "response": "This is a very long response that should be truncated."
    }).encode("utf-8")
    
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = client.post("/api/v1/ai/ollama/dispatch", json={"user_goal": "test", "model": "test"})
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert data["truncated"] is True
    assert "[WARNING: RESPONSE TRUNCATED" in data["response_text"]

@patch("app.core.ai_runtime.urllib.request.urlopen")
def test_dispatch_timeout(mock_urlopen):
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={"kairos_ollama_dispatch_enabled": True, "kairos_ai_provider": "ollama"}
    )
    mock_urlopen.side_effect = TimeoutError("Timeout")

    response = client.post("/api/v1/ai/ollama/dispatch", json={"user_goal": "test", "model": "test"})
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "Timeout after" in data["raw_response_metadata"]["error"]

def test_dispatch_missing_model():
    app.dependency_overrides[get_settings] = lambda: get_settings().model_copy(
        update={
            "kairos_ollama_dispatch_enabled": True,
            "kairos_ai_provider": "ollama",
            "kairos_ai_model": ""
        }
    )
    
    response = client.post("/api/v1/ai/ollama/dispatch", json={"user_goal": "test"})
    app.dependency_overrides.clear()
    
    assert response.status_code == 400
    assert "No model provided" in response.json()["detail"]
