import datetime
from typing import Any, Dict

from app.core.authentication import (
    AuthenticationAdapter,
    AuthenticationResult,
    AuthenticationError,
    AuthenticationProvider,
    AuthenticationCapability,
    ProviderAuthenticationRegistry
)
from app.core.provider_session import ProviderSession, ProviderIdentity, ProviderCredential


class OpenAICodexAuthenticationAdapter(AuthenticationAdapter):
    """
    Authentication Adapter for OpenAI Codex / ChatGPT.
    Defines the contract for validating credentials, refreshing tokens, 
    and maintaining sessions, preparing for future OAuth/browser integrations.
    """

    @property
    def provider_id(self) -> str:
        return "ai.openai.codex"

    def authenticate(self, credentials: Dict[str, Any], settings: Any) -> AuthenticationResult:
        """
        Authenticate using either a provided API key or a delegated Codex/ChatGPT token.
        (Browser login and OAuth flow not implemented yet.)
        """
        token = credentials.get("token") or credentials.get("api_key")

        if not token:
            raise AuthenticationError(
                "No valid OpenAI credentials provided.",
                provider_id=self.provider_id,
                error_code="missing_credentials"
            )

        # In a future full implementation, we would validate the token against OpenAI API endpoints here.
        # For now, we establish the authenticated session directly if a credential is discovered.
        session = ProviderSession(
            session_id=f"session.openai.codex.{datetime.datetime.utcnow().timestamp()}",
            provider_id=self.provider_id,
            identity=ProviderIdentity(user_id="openai_user", username="codex_user"),
            credential=ProviderCredential(auth_type="api_key", token_value=token),
            state="active"
        )
        return AuthenticationResult(
            provider_id=self.provider_id,
            is_authenticated=True,
            session=session,
            metadata={"auth_method": "api_key_or_token"}
        )

    def validate_session(self, session: ProviderSession, settings: Any) -> bool:
        """
        Validate if the session is still active and credentials are functional.
        """
        if session.provider_id != self.provider_id:
            return False
        return session.is_valid(settings)

    def refresh_session(self, session: ProviderSession, settings: Any) -> AuthenticationResult:
        """
        Attempt to refresh an expired session (e.g., via OAuth refresh token).
        (OAuth flow not implemented yet.)
        """
        # If it's just an API key, we cannot "refresh" it.
        if session.credential.auth_type == "api_key":
            return AuthenticationResult(
                provider_id=self.provider_id,
                is_authenticated=False,
                error="Cannot refresh static API key.",
                session=session
            )
        
        # Placeholder for future Codex OAuth token refresh logic
        return AuthenticationResult(
            provider_id=self.provider_id,
            is_authenticated=False,
            error="Codex token refresh not yet implemented.",
            session=session
        )

    def logout(self, session: ProviderSession, settings: Any) -> bool:
        """
        Terminate and revoke the session.
        """
        if session.provider_id != self.provider_id:
            return False
        session.state = "revoked"
        return True


def register_openai_codex_adapter(registry: ProviderAuthenticationRegistry) -> None:
    """Register the OpenAI Codex adapter into the provided registry."""
    adapter = OpenAICodexAuthenticationAdapter()
    provider_info = AuthenticationProvider(
        provider_id="ai.openai.codex",
        name="OpenAI Codex",
        capabilities=[AuthenticationCapability.API_KEY, AuthenticationCapability.OAUTH2],
        requires_network=True,
        supported_scopes=["read", "write", "offline_access"]
    )
    registry.register(adapter, provider_info)
