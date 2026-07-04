import pytest
from typing import Any, Dict

from app.core.authentication import (
    AuthenticationCapability,
    AuthenticationError,
    AuthenticationResult,
    AuthenticationProvider,
    AuthenticationAdapter,
    ProviderAuthenticationRegistry,
)
from app.core.provider_session import ProviderSession, ProviderIdentity, ProviderCredential


class MockAdapter(AuthenticationAdapter):
    @property
    def provider_id(self) -> str:
        return "ai.mock"

    def authenticate(self, credentials: Dict[str, Any], settings: Any) -> AuthenticationResult:
        if credentials.get("fail"):
            raise AuthenticationError("Auth failed", self.provider_id, "mock_err")
        return AuthenticationResult(provider_id=self.provider_id, is_authenticated=True)

    def validate_session(self, session: ProviderSession, settings: Any) -> bool:
        return session.state == "active"

    def refresh_session(self, session: ProviderSession, settings: Any) -> AuthenticationResult:
        return AuthenticationResult(provider_id=self.provider_id, is_authenticated=True, session=session)

    def logout(self, session: ProviderSession, settings: Any) -> bool:
        return True


def test_authentication_capability_enum():
    assert AuthenticationCapability.API_KEY == "api_key"
    assert AuthenticationCapability.OAUTH2 == "oauth2"
    assert AuthenticationCapability.LOCAL_NONE == "local_none"


def test_authentication_error():
    err = AuthenticationError("Invalid token", "ai.openai", "invalid_token")
    assert str(err) == "Invalid token"
    assert err.provider_id == "ai.openai"
    assert err.error_code == "invalid_token"


def test_authentication_result():
    res = AuthenticationResult(provider_id="ai.ollama", is_authenticated=True)
    assert res.provider_id == "ai.ollama"
    assert res.is_authenticated is True
    assert res.session is None
    assert res.metadata == {}


def test_authentication_provider_model():
    provider = AuthenticationProvider(
        provider_id="ai.google",
        name="Google",
        capabilities=[AuthenticationCapability.OAUTH2],
        requires_network=True,
        supported_scopes=["ai.read"]
    )
    assert provider.provider_id == "ai.google"
    assert AuthenticationCapability.OAUTH2 in provider.capabilities
    assert provider.requires_network is True
    assert "ai.read" in provider.supported_scopes


def test_provider_authentication_registry():
    registry = ProviderAuthenticationRegistry()
    adapter = MockAdapter()
    provider_info = AuthenticationProvider(
        provider_id="ai.mock",
        name="Mock Provider",
        capabilities=[AuthenticationCapability.API_KEY],
        requires_network=False,
    )

    registry.register(adapter, provider_info)

    assert registry.get_adapter("ai.mock") is adapter
    assert registry.get_provider_info("ai.mock") == provider_info
    assert len(registry.list_providers()) == 1
    assert registry.get_adapter("ai.unknown") is None


def test_mock_adapter_behavior():
    adapter = MockAdapter()
    res = adapter.authenticate({"token": "123"}, None)
    assert res.is_authenticated is True

    with pytest.raises(AuthenticationError) as exc:
        adapter.authenticate({"fail": True}, None)
    
    assert exc.value.provider_id == "ai.mock"
    assert exc.value.error_code == "mock_err"
    assert exc.value.message == "Auth failed"
