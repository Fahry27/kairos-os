import pytest
from typing import Any, Dict, Optional

from app.core.authentication import AuthenticationResult, AuthenticationAdapter
from app.core.auth_platform import (
    AuthenticationManager,
    AuthenticationRegistry,
    CredentialProvider,
    SessionStore,
    TokenStore,
    AuthenticationEvent
)
from app.core.provider_session import ProviderSession, ProviderIdentity, ProviderCredential


class MockCredentialProvider(CredentialProvider):
    def __init__(self):
        self.creds = {}

    def get_credentials(self, identity_id: str, provider_id: str, settings: Any) -> Optional[Dict[str, Any]]:
        return self.creds.get(f"{identity_id}:{provider_id}")

    def save_credentials(self, identity_id: str, provider_id: str, credentials: Dict[str, Any], settings: Any) -> bool:
        self.creds[f"{identity_id}:{provider_id}"] = credentials
        return True


class MockSessionStore(SessionStore):
    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id: str) -> Optional[ProviderSession]:
        return self.sessions.get(session_id)
        
    def save_session(self, session: ProviderSession) -> None:
        self.sessions[session.session_id] = session
        
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


class MockTokenStore(TokenStore):
    def __init__(self):
        self.tokens = {}

    def get_token(self, session_id: str) -> Optional[str]:
        return self.tokens.get(session_id)
        
    def store_token(self, session_id: str, token: str, expires_in: int) -> None:
        self.tokens[session_id] = token
        
    def revoke_token(self, session_id: str) -> bool:
        if session_id in self.tokens:
            del self.tokens[session_id]
            return True
        return False


class MockAdapter(AuthenticationAdapter):
    @property
    def provider_id(self) -> str:
        return "ai.mock"

    def authenticate(self, credentials: Dict[str, Any], settings: Any) -> AuthenticationResult:
        if credentials.get("fail"):
            return AuthenticationResult(provider_id=self.provider_id, is_authenticated=False, error="Failed")
        
        session = ProviderSession(
            session_id="session.123",
            provider_id=self.provider_id,
            identity=ProviderIdentity(user_id="user"),
            credential=ProviderCredential(auth_type="api_key"),
            state="active"
        )
        return AuthenticationResult(
            provider_id=self.provider_id, 
            is_authenticated=True, 
            session=session,
            metadata={"access_token": "token123"}
        )

    def validate_session(self, session: ProviderSession, settings: Any) -> bool:
        return session.state == "active"

    def refresh_session(self, session: ProviderSession, settings: Any) -> AuthenticationResult:
        return AuthenticationResult(provider_id=self.provider_id, is_authenticated=False)

    def logout(self, session: ProviderSession, settings: Any) -> bool:
        session.state = "revoked"
        return True


from app.core.authentication import AuthenticationResult, AuthenticationAdapter, AuthenticationProvider

def create_mock_provider_info():
    return AuthenticationProvider(
        provider_id="ai.mock",
        name="Mock Provider",
        capabilities=[],
        requires_network=False
    )

def test_auth_manager_authenticate():
    registry = AuthenticationRegistry()
    registry.register(MockAdapter(), create_mock_provider_info())
    
    cred_prov = MockCredentialProvider()
    cred_prov.save_credentials("user1", "ai.mock", {"token": "secret"}, None)
    
    sess_store = MockSessionStore()
    tok_store = MockTokenStore()
    
    manager = AuthenticationManager(registry, cred_prov, sess_store, tok_store)
    
    # Test unmapped provider
    with pytest.raises(ValueError):
        manager.authenticate_identity("ai.unknown", "user1", None)
        
    # Test missing credentials
    res = manager.authenticate_identity("ai.mock", "user2", None)
    assert res.is_authenticated is False
    assert "No credentials" in res.error
    
    # Test success
    res = manager.authenticate_identity("ai.mock", "user1", None)
    assert res.is_authenticated is True
    assert sess_store.get_session("session.123") is not None
    assert tok_store.get_token("session.123") == "token123"


def test_auth_manager_validate_session():
    registry = AuthenticationRegistry()
    registry.register(MockAdapter(), create_mock_provider_info())
    
    sess_store = MockSessionStore()
    session = ProviderSession(
        session_id="session.123",
        provider_id="ai.mock",
        identity=ProviderIdentity(user_id="user"),
        credential=ProviderCredential(auth_type="api_key"),
        state="active"
    )
    sess_store.save_session(session)
    
    manager = AuthenticationManager(registry, MockCredentialProvider(), sess_store, MockTokenStore())
    
    assert manager.validate_session("session.123", None) is True
    assert manager.validate_session("session.unknown", None) is False
    
    # Invalidate session
    session.state = "expired"
    assert manager.validate_session("session.123", None) is False
    # Validate it wrote back state
    assert sess_store.get_session("session.123").state == "expired"


def test_auth_manager_logout():
    registry = AuthenticationRegistry()
    registry.register(MockAdapter(), create_mock_provider_info())
    
    sess_store = MockSessionStore()
    session = ProviderSession(
        session_id="session.123",
        provider_id="ai.mock",
        identity=ProviderIdentity(user_id="user"),
        credential=ProviderCredential(auth_type="api_key"),
        state="active"
    )
    sess_store.save_session(session)
    
    tok_store = MockTokenStore()
    tok_store.store_token("session.123", "token123", 3600)
    
    manager = AuthenticationManager(registry, MockCredentialProvider(), sess_store, tok_store)
    
    assert manager.logout("session.123", None) is True
    
    assert sess_store.get_session("session.123") is None
    assert tok_store.get_token("session.123") is None


def test_authentication_event():
    event = AuthenticationEvent(
        event_id="evt.123",
        session_id="sess.123",
        provider_id="ai.mock",
        identity_id="user1",
        event_type="login_success",
        status="success"
    )
    assert event.event_id == "evt.123"
    assert event.status == "success"
    assert event.event_type == "login_success"
