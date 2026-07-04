import abc
import enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from app.core.provider_session import ProviderSession


class AuthenticationCapability(str, enum.Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    LOCAL_NONE = "local_none"
    BASIC_AUTH = "basic_auth"
    WORKLOAD_IDENTITY = "workload_identity"


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""
    def __init__(self, message: str, provider_id: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.provider_id = provider_id
        self.error_code = error_code


class AuthenticationResult(BaseModel):
    """Result of an authentication attempt."""
    provider_id: str
    is_authenticated: bool
    session: Optional[ProviderSession] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthenticationProvider(BaseModel):
    """Metadata describing a provider's authentication capabilities."""
    provider_id: str
    name: str
    capabilities: List[AuthenticationCapability]
    requires_network: bool
    supported_scopes: List[str] = Field(default_factory=list)


class AuthenticationAdapter(abc.ABC):
    """Interface for provider-specific authentication logic."""
    
    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        """The ID of the provider this adapter handles."""
        pass

    @abc.abstractmethod
    def authenticate(self, credentials: Dict[str, Any], settings: Any) -> AuthenticationResult:
        """Authenticate using the provided credentials and return a session result."""
        pass

    @abc.abstractmethod
    def validate_session(self, session: ProviderSession, settings: Any) -> bool:
        """Validate if the given session is still valid and active."""
        pass

    @abc.abstractmethod
    def refresh_session(self, session: ProviderSession, settings: Any) -> AuthenticationResult:
        """Attempt to refresh an expired session."""
        pass

    @abc.abstractmethod
    def logout(self, session: ProviderSession, settings: Any) -> bool:
        """Terminate and revoke the session."""
        pass


class ProviderAuthenticationRegistry:
    """Registry for managing and resolving Authentication Adapters."""
    
    def __init__(self) -> None:
        self._adapters: dict[str, AuthenticationAdapter] = {}
        self._providers: dict[str, AuthenticationProvider] = {}

    def register(self, adapter: AuthenticationAdapter, provider_info: AuthenticationProvider) -> None:
        """Register an adapter and its metadata."""
        self._adapters[adapter.provider_id] = adapter
        self._providers[provider_info.provider_id] = provider_info

    def get_adapter(self, provider_id: str) -> Optional[AuthenticationAdapter]:
        """Retrieve the adapter for a given provider."""
        return self._adapters.get(provider_id)

    def get_provider_info(self, provider_id: str) -> Optional[AuthenticationProvider]:
        """Retrieve the metadata for a given provider."""
        return self._providers.get(provider_id)

    def list_providers(self) -> List[AuthenticationProvider]:
        """List all registered provider metadata."""
        return list(self._providers.values())
