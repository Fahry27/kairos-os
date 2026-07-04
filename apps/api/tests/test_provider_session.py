import os
from unittest.mock import MagicMock
import pytest
from app.core.provider_session import (
    ProviderIdentity,
    SecretReference,
    ProviderCredential,
    ProviderSession,
    provider_session_registry,
    get_session_for_provider
)


def test_provider_identity():
    identity = ProviderIdentity(user_id="operator_1", username="alice", email="alice@test.com", scopes=["read", "write"])
    assert identity.user_id == "operator_1"
    assert identity.username == "alice"
    assert identity.scopes == ["read", "write"]


def test_secret_reference(monkeypatch):
    # Test resolving from settings first
    settings = MagicMock()
    settings.test_key = "settings_value"
    ref = SecretReference(secret_key="TEST_KEY")
    assert ref.resolve(settings) == "settings_value"

    # Test resolving from environment when settings doesn't have it
    settings_no_key = MagicMock()
    del settings_no_key.test_key
    monkeypatch.setenv("TEST_KEY", "env_value")
    assert ref.resolve(settings_no_key) == "env_value"


def test_provider_credential_api_key():
    ref = SecretReference(secret_key="API_KEY")
    settings = MagicMock()
    settings.api_key = "my_api_key"
    cred = ProviderCredential(auth_type="api_key", secret_ref=ref)
    assert cred.get_token(settings) == "my_api_key"


def test_provider_credential_none():
    cred = ProviderCredential(auth_type="none")
    assert cred.get_token(MagicMock()) is None


def test_provider_session_validation(monkeypatch):
    ref = SecretReference(secret_key="API_KEY")
    cred = ProviderCredential(auth_type="api_key", secret_ref=ref)
    identity = ProviderIdentity(user_id="user")
    
    session = ProviderSession(
        session_id="session_1",
        provider_id="ai.openai",
        identity=identity,
        credential=cred,
        state="active"
    )

    settings = MagicMock()
    settings.api_key = "some_key"
    assert session.is_valid(settings) is True

    # Test expired state
    session.state = "expired"
    assert session.is_valid(settings) is False
    session.state = "active"

    # Test missing credentials
    settings_missing = MagicMock()
    settings_missing.api_key = None
    assert session.is_valid(settings_missing) is False


def test_provider_session_registry():
    provider_session_registry.clear()
    identity = ProviderIdentity(user_id="user")
    cred = ProviderCredential(auth_type="none")
    
    session = ProviderSession(
        session_id="test_sess",
        provider_id="ai.ollama",
        identity=identity,
        credential=cred
    )

    provider_session_registry.register(session)
    assert provider_session_registry.get("test_sess") == session
    
    sessions = provider_session_registry.list_by_provider("ai.ollama")
    assert len(sessions) == 1
    assert sessions[0] == session

    provider_session_registry.remove("test_sess")
    assert provider_session_registry.get("test_sess") is None
    provider_session_registry.clear()


def test_get_session_for_provider(monkeypatch):
    provider_session_registry.clear()
    settings = MagicMock()
    settings.openai_api_key = None
    settings.gemini_api_key = None
    settings.kairos_gemini_api_key = None
    
    # Ollama should auto-resolve
    ollama_sess = get_session_for_provider("ai.ollama", settings)
    assert ollama_sess is not None
    assert ollama_sess.provider_id == "ai.ollama"

    # OpenAI without environment key should be None
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert get_session_for_provider("ai.openai", settings) is None

    # OpenAI with environment key should auto-resolve
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    openai_sess = get_session_for_provider("ai.openai", settings)
    assert openai_sess is not None
    assert openai_sess.provider_id == "ai.openai"
    assert openai_sess.credential.get_token(settings) == "sk-test"
