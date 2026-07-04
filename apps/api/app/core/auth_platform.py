import abc
import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.authentication import AuthenticationAdapter, AuthenticationResult, ProviderAuthenticationRegistry
from app.core.provider_session import ProviderSession


class CredentialProvider(abc.ABC):
    """Abstraction for acquiring and securely retrieving credentials."""
    
    @abc.abstractmethod
    def get_credentials(self, identity_id: str, provider_id: str, settings: Any) -> Optional[Dict[str, Any]]:
        """Retrieve stored credentials for an identity and provider."""
        pass

    @abc.abstractmethod
    def save_credentials(self, identity_id: str, provider_id: str, credentials: Dict[str, Any], settings: Any) -> bool:
        """Securely store credentials."""
        pass


class SessionStore(abc.ABC):
    """Abstraction for managing the persistence of ProviderSessions."""
    
    @abc.abstractmethod
    def get_session(self, session_id: str) -> Optional[ProviderSession]:
        """Retrieve a session by its ID."""
        pass
        
    @abc.abstractmethod
    def save_session(self, session: ProviderSession) -> None:
        """Save or update a session."""
        pass
        
    @abc.abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass


class TokenStore(abc.ABC):
    """Abstraction for securely storing short-lived access tokens and refresh tokens."""
    
    @abc.abstractmethod
    def get_token(self, session_id: str) -> Optional[str]:
        """Retrieve the active access token for a session."""
        pass
        
    @abc.abstractmethod
    def store_token(self, session_id: str, token: str, expires_in: int) -> None:
        """Store an access token with an expiration time."""
        pass
        
    @abc.abstractmethod
    def revoke_token(self, session_id: str) -> bool:
        """Revoke and delete the token."""
        pass


class AuthenticationEvent(BaseModel):
    """Model representing an authentication lifecycle event (audit log)."""
    event_id: str
    session_id: Optional[str]
    provider_id: str
    identity_id: Optional[str]
    event_type: str  # e.g., "login_attempt", "login_success", "token_refresh", "logout"
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    status: str      # "success", "failure"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationRegistry(ProviderAuthenticationRegistry):
    """
    Core registry for the Authentication Platform. 
    Inherits from the foundational ProviderAuthenticationRegistry.
    """
    pass


class AuthenticationManager:
    """
    Orchestrates the Authentication Platform operations.
    Coordinates between Adapters, Stores, and Providers.
    """
    
    def __init__(
        self,
        registry: AuthenticationRegistry,
        credential_provider: CredentialProvider,
        session_store: SessionStore,
        token_store: TokenStore
    ):
        self.registry = registry
        self.credential_provider = credential_provider
        self.session_store = session_store
        self.token_store = token_store

    def authenticate_identity(self, provider_id: str, identity_id: str, settings: Any) -> AuthenticationResult:
        """Authenticate an identity using stored credentials."""
        adapter = self.registry.get_adapter(provider_id)
        if not adapter:
            raise ValueError(f"No adapter registered for provider: {provider_id}")

        credentials = self.credential_provider.get_credentials(identity_id, provider_id, settings)
        if not credentials:
            return AuthenticationResult(
                provider_id=provider_id, 
                is_authenticated=False, 
                error="No credentials found for identity."
            )
            
        result = adapter.authenticate(credentials, settings)
        
        if result.is_authenticated and result.session:
            self.session_store.save_session(result.session)
            token = result.metadata.get("access_token")
            if token:
                self.token_store.store_token(result.session.session_id, token, 3600)
                
        return result

    def validate_session(self, session_id: str, settings: Any) -> bool:
        """Validate an existing session."""
        session = self.session_store.get_session(session_id)
        if not session:
            return False
            
        adapter = self.registry.get_adapter(session.provider_id)
        if not adapter:
            return False
            
        is_valid = adapter.validate_session(session, settings)
        if not is_valid:
            session.state = "expired"
            self.session_store.save_session(session)
            
        return is_valid

    def logout(self, session_id: str, settings: Any) -> bool:
        """Log out a session."""
        session = self.session_store.get_session(session_id)
        if not session:
            return False
            
        adapter = self.registry.get_adapter(session.provider_id)
        if adapter:
            adapter.logout(session, settings)
            
        self.token_store.revoke_token(session_id)
        self.session_store.delete_session(session_id)
        return True
