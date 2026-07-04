import pytest
from app.core.authentication import ProviderAuthenticationRegistry, AuthenticationError
from app.core.openai_codex_auth import OpenAICodexAuthenticationAdapter, register_openai_codex_adapter
from app.core.provider_session import ProviderSession, ProviderIdentity, ProviderCredential


def test_openai_codex_adapter_registration():
    registry = ProviderAuthenticationRegistry()
    register_openai_codex_adapter(registry)
    
    adapter = registry.get_adapter("ai.openai.codex")
    assert isinstance(adapter, OpenAICodexAuthenticationAdapter)
    
    info = registry.get_provider_info("ai.openai.codex")
    assert info is not None
    assert info.name == "OpenAI Codex"
    assert info.requires_network is True


def test_openai_codex_authenticate_success():
    adapter = OpenAICodexAuthenticationAdapter()
    res = adapter.authenticate({"api_key": "sk-12345"}, None)
    
    assert res.is_authenticated is True
    assert res.session is not None
    assert res.session.provider_id == "ai.openai.codex"
    assert res.session.credential.token_value == "sk-12345"
    assert res.metadata["auth_method"] == "api_key_or_token"


def test_openai_codex_authenticate_missing_credentials():
    adapter = OpenAICodexAuthenticationAdapter()
    
    with pytest.raises(AuthenticationError) as exc:
        adapter.authenticate({}, None)
        
    assert exc.value.error_code == "missing_credentials"


def test_openai_codex_validate_session():
    adapter = OpenAICodexAuthenticationAdapter()
    session = ProviderSession(
        session_id="test",
        provider_id="ai.openai.codex",
        identity=ProviderIdentity(user_id="user"),
        credential=ProviderCredential(auth_type="api_key", token_value="sk-123"),
        state="active"
    )
    assert adapter.validate_session(session, None) is True
    
    session.state = "expired"
    assert adapter.validate_session(session, None) is False


def test_openai_codex_refresh_session():
    adapter = OpenAICodexAuthenticationAdapter()
    session = ProviderSession(
        session_id="test",
        provider_id="ai.openai.codex",
        identity=ProviderIdentity(user_id="user"),
        credential=ProviderCredential(auth_type="api_key", token_value="sk-123"),
        state="active"
    )
    res = adapter.refresh_session(session, None)
    assert res.is_authenticated is False
    assert "Cannot refresh static API key" in res.error

    session.credential.auth_type = "oauth2"
    res2 = adapter.refresh_session(session, None)
    assert res2.is_authenticated is False
    assert "Codex token refresh not yet implemented" in res2.error


def test_openai_codex_logout():
    adapter = OpenAICodexAuthenticationAdapter()
    session = ProviderSession(
        session_id="test",
        provider_id="ai.openai.codex",
        identity=ProviderIdentity(user_id="user"),
        credential=ProviderCredential(auth_type="api_key", token_value="sk-123"),
        state="active"
    )
    assert adapter.logout(session, None) is True
    assert session.state == "revoked"
