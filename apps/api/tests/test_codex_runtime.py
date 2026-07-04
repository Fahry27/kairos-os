import pytest
from unittest.mock import patch, MagicMock
from app.core.codex_runtime import CodexCliRuntime
from app.core.ai_runtime import AIOllamaDispatchRequest

@pytest.fixture
def mock_subprocess_run():
    with patch("app.core.codex_runtime.subprocess.run") as mock_run:
        yield mock_run

@pytest.fixture
def mock_shutil_which():
    with patch("app.core.codex_runtime.shutil.which") as mock_which:
        yield mock_which

def test_codex_readiness_not_installed(mock_shutil_which):
    mock_shutil_which.return_value = None
    provider = CodexCliRuntime()
    readiness = provider.check_readiness()
    assert not readiness.reachable
    assert readiness.error_type == "not_installed"

def test_codex_readiness_auth_ok(mock_shutil_which, mock_subprocess_run):
    mock_shutil_which.return_value = "/bin/codex"
    mock_process = MagicMock()
    mock_process.stdout = '{"checks": {"auth.credentials": {"status": "ok", "summary": "auth ok", "details": {"auth mode": "chatgpt"}}}}'
    mock_subprocess_run.return_value = mock_process
    
    provider = CodexCliRuntime()
    readiness = provider.check_readiness()
    
    assert readiness.reachable
    assert "chatgpt" in readiness.message

def test_codex_readiness_auth_fail(mock_shutil_which, mock_subprocess_run):
    mock_shutil_which.return_value = "/bin/codex"
    mock_process = MagicMock()
    mock_process.stdout = '{"checks": {"auth.credentials": {"status": "error"}}}'
    mock_subprocess_run.return_value = mock_process
    
    provider = CodexCliRuntime()
    readiness = provider.check_readiness()
    
    assert not readiness.reachable
    assert readiness.error_type == "auth_error"

@patch("app.core.codex_runtime.ai_runtime.generate_prompt_dry_run")
@patch("app.core.codex_runtime.subprocess.run")
def test_codex_dispatch_success(mock_run, mock_dry_run, mock_shutil_which):
    mock_shutil_which.return_value = "/bin/codex"
    
    # Mock the dry run package
    mock_pkg = MagicMock()
    mock_pkg.system_instructions = ["Be helpful"]
    mock_pkg.safety_policy = ["No commands"]
    mock_pkg.context = {"role": "admin"}
    mock_pkg.user_goal = "say hello"
    mock_dry_run.return_value = mock_pkg
    
    # Mock subprocess run to write to result.json
    def side_effect(cmd, *args, **kwargs):
        # cmd is like: ['/bin/codex', 'exec', '--output-schema', '<path>', '--output-last-message', '<path>', '...']
        result_path = None
        for i, arg in enumerate(cmd):
            if arg == "--output-last-message":
                result_path = cmd[i + 1]
                break
        
        if result_path:
            with open(result_path, "w") as f:
                f.write('{"plan": "Hello World"}')
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "some output"
        mock_proc.stderr = ""
        return mock_proc
        
    mock_run.side_effect = side_effect
    
    provider = CodexCliRuntime()
    request = AIOllamaDispatchRequest(
        model="gpt-5.5",
        user_goal="say hello",
        context={},
        include_commands=False,
        include_plugins=False,
        include_connectors=False
    )
    
    response = provider.dispatch(
        request=request,
        settings=MagicMock(),
        plugin_registry=MagicMock(),
        connector_registry=MagicMock()
    )
    
    assert response.provider_id == "ai.codex"
    assert response.prompt_sent is True
    assert "Hello World" in response.response_text
