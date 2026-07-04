import datetime
import pytest

from app.core.codex_compatibility import (
    SessionMetadata,
    SessionExpiry,
    CodexSession,
    SessionValidator,
    CodexCompatibilityInterface
)
from app.core.provider_session import ProviderSession


def test_session_expiry():
    now = datetime.datetime.utcnow()
    # Active
    expiry = SessionExpiry(expires_at=now + datetime.timedelta(hours=1))
    assert expiry.is_expired() is False
    
    # Expired
    expiry = SessionExpiry(expires_at=now - datetime.timedelta(hours=1))
    assert expiry.is_expired() is True
    
    # Revoked
    expiry = SessionExpiry(expires_at=now + datetime.timedelta(hours=1), is_revoked=True)
    assert expiry.is_expired() is True


def test_codex_session_to_provider_session():
    now = datetime.datetime.utcnow()
    metadata = SessionMetadata(workspace_id="ws_123", client_id="client_1")
    expiry = SessionExpiry(expires_at=now + datetime.timedelta(hours=1))
    
    session = CodexSession(
        access_token="tok_123",
        refresh_token="ref_123",
        expiry=expiry,
        metadata=metadata
    )
    
    provider_session = session.to_provider_session("sess_001")
    assert isinstance(provider_session, ProviderSession)
    assert provider_session.session_id == "sess_001"
    assert provider_session.provider_id == "ai.openai.codex"
    assert provider_session.identity.user_id == "ws_123"
    assert provider_session.credential.token_value == "tok_123"
    assert provider_session.state == "active"
    
    # Test expired state translation
    session.expiry.expires_at = now - datetime.timedelta(hours=1)
    provider_session = session.to_provider_session("sess_002")
    assert provider_session.state == "expired"
    
    # Test revoked state translation
    session.expiry.is_revoked = True
    provider_session = session.to_provider_session("sess_003")
    assert provider_session.state == "revoked"


class MockCodexInterface(CodexCompatibilityInterface):
    def read_session(self):
        return None
        
    def write_session(self, session):
        return True


class MockSessionValidator(SessionValidator):
    def validate(self, session, settings):
        return not session.expiry.is_expired()


def test_interfaces_instantiation():
    interface = MockCodexInterface()
    assert interface.read_session() is None
    
    validator = MockSessionValidator()
    metadata = SessionMetadata()
    expiry = SessionExpiry(expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1))
    session = CodexSession(access_token="tok", expiry=expiry, metadata=metadata)
    assert validator.validate(session, None) is True
