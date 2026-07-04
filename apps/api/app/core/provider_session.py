import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ProviderIdentity(BaseModel):
    user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = Field(default_factory=list)


class SecretReference(BaseModel):
    """Abstraction for pointing to a secret stored in environment or secure settings."""
    secret_key: str

    def resolve(self, settings) -> Optional[str]:
        # Attempt to resolve from settings object, then environment
        val = getattr(settings, self.secret_key.lower(), None)
        if not val:
            import os
            val = os.environ.get(self.secret_key)
        return val


class ProviderCredential(BaseModel):
    auth_type: str  # "api_key", "oauth", "none"
    secret_ref: Optional[SecretReference] = None
    token_value: Optional[str] = None

    def get_token(self, settings) -> Optional[str]:
        if self.auth_type == "none":
            return None
        if self.secret_ref:
            return self.secret_ref.resolve(settings)
        return self.token_value


class ProviderSession(BaseModel):
    session_id: str
    provider_id: str
    identity: ProviderIdentity
    credential: ProviderCredential
    state: str = "active"  # "active", "expired", "revoked"
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    expires_at: Optional[datetime.datetime] = None

    def is_valid(self, settings) -> bool:
        if self.state != "active":
            return False
        if self.expires_at and datetime.datetime.utcnow() > self.expires_at:
            return False
        if self.credential.auth_type != "none":
            if not self.credential.get_token(settings):
                return False
        return True


class ProviderSessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, ProviderSession] = {}

    def register(self, session: ProviderSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Optional[ProviderSession]:
        return self._sessions.get(session_id)

    def list_by_provider(self, provider_id: str) -> list[ProviderSession]:
        return [s for s in self._sessions.values() if s.provider_id == provider_id]

    def remove(self, session_id: str) -> Optional[ProviderSession]:
        return self._sessions.pop(session_id, None)

    def clear(self) -> None:
        self._sessions.clear()


provider_session_registry = ProviderSessionRegistry()


def get_session_for_provider(provider_id: str, settings) -> Optional[ProviderSession]:
    # 1. Check registry first
    sessions = provider_session_registry.list_by_provider(provider_id)
    active_sessions = [s for s in sessions if s.is_valid(settings)]
    if active_sessions:
        return active_sessions[0]

    # 2. Local-only auto-session for Ollama
    if provider_id == "ai.ollama":
        return ProviderSession(
            session_id="session.ollama.local",
            provider_id="ai.ollama",
            identity=ProviderIdentity(user_id="local_operator", username="local"),
            credential=ProviderCredential(auth_type="none"),
            state="active"
        )

    # 3. Environment fallback sessions for OpenAI
    if provider_id == "ai.openai":
        import os
        if os.environ.get("OPENAI_API_KEY"):
            return ProviderSession(
                session_id="session.openai.auto",
                provider_id="ai.openai",
                identity=ProviderIdentity(user_id="auto_operator", username="auto"),
                credential=ProviderCredential(
                    auth_type="api_key",
                    secret_ref=SecretReference(secret_key="OPENAI_API_KEY")
                ),
                state="active"
            )

    # 4. Environment fallback sessions for Gemini
    if provider_id == "ai.gemini":
        import os
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("KAIROS_GEMINI_API_KEY")
        if api_key:
            key_name = "GEMINI_API_KEY" if os.environ.get("GEMINI_API_KEY") else "KAIROS_GEMINI_API_KEY"
            return ProviderSession(
                session_id="session.gemini.auto",
                provider_id="ai.gemini",
                identity=ProviderIdentity(user_id="auto_operator", username="auto"),
                credential=ProviderCredential(
                    auth_type="api_key",
                    secret_ref=SecretReference(secret_key=key_name)
                ),
                state="active"
            )

    return None
