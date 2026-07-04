import abc
import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from app.core.provider_session import ProviderSession, ProviderIdentity, ProviderCredential


class SessionMetadata(BaseModel):
    """Metadata extracted from a Codex auth.json session."""
    client_id: Optional[str] = None
    workspace_id: Optional[str] = None
    models_allowed: List[str] = Field(default_factory=list)
    raw_claims: Dict[str, Any] = Field(default_factory=dict)


class SessionExpiry(BaseModel):
    """Represents the expiration constraints of a Codex session."""
    expires_at: datetime.datetime
    refresh_deadline: Optional[datetime.datetime] = None
    is_revoked: bool = False

    def is_expired(self) -> bool:
        if self.is_revoked:
            return True
        return datetime.datetime.utcnow() >= self.expires_at


class CodexSession(BaseModel):
    """
    Representation of an active Codex session parsed from an external 
    auth.json or existing authenticated state.
    """
    access_token: str
    refresh_token: Optional[str] = None
    expiry: SessionExpiry
    metadata: SessionMetadata

    def to_provider_session(self, session_id: str) -> ProviderSession:
        """Converts the Codex session into a standard Kairos ProviderSession."""
        state = "active" if not self.expiry.is_expired() else "expired"
        if self.expiry.is_revoked:
            state = "revoked"

        return ProviderSession(
            session_id=session_id,
            provider_id="ai.openai.codex",
            identity=ProviderIdentity(
                user_id=self.metadata.workspace_id or "codex_user", 
                username="codex"
            ),
            credential=ProviderCredential(
                auth_type="oauth2", 
                token_value=self.access_token
            ),
            state=state,
            expires_at=self.expiry.expires_at
        )


class SessionValidator(abc.ABC):
    """Interface to validate the health and constraints of a Codex session."""
    
    @abc.abstractmethod
    def validate(self, session: CodexSession, settings: Any) -> bool:
        """Validate whether the token is structurally sound and unrevoked."""
        pass


class CodexCompatibilityInterface(abc.ABC):
    """
    Integration boundary for reading and managing external Codex sessions.
    This interface bridges Kairos to an external environment (e.g., auth.json on disk)
    without dictating how the credentials are acquired or requiring browser login.
    """

    @abc.abstractmethod
    def read_session(self) -> Optional[CodexSession]:
        """Attempt to read and parse the existing Codex session from the environment."""
        pass

    @abc.abstractmethod
    def write_session(self, session: CodexSession) -> bool:
        """Write an updated (e.g., refreshed) Codex session back to the environment."""
        pass
