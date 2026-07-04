from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
import datetime

from app.core.provider_session import provider_session_registry
from app.core.codex_compatibility import CodexSession, SessionExpiry, SessionMetadata

router = APIRouter(prefix="/auth", tags=["auth"])

class ConnectedProviderResponse(BaseModel):
    provider_id: str
    status: str
    session_id: str

@router.get("/sessions", response_model=List[ConnectedProviderResponse])
async def get_sessions():
    """Returns currently connected provider sessions."""
    sessions = []
    # Using the existing registry for now as a surrogate for SessionStore
    for provider_id in ["ai.openai.codex", "ai.google", "ai.ollama", "ai.openai"]:
        prov_sessions = provider_session_registry.list_by_provider(provider_id)
        for s in prov_sessions:
            sessions.append(ConnectedProviderResponse(
                provider_id=s.provider_id,
                status=s.state,
                session_id=s.session_id
            ))
    return sessions

@router.post("/providers/ai.openai.codex/connect")
async def connect_codex():
    """
    Stub endpoint to simulate a successful Codex OAuth flow.
    It creates a mocked active Codex session and bridges it to ProviderSession.
    """
    # Create mock proprietary CodexSession as if parsed from auth.json
    now = datetime.datetime.utcnow()
    codex_session = CodexSession(
        access_token="mock_codex_token_123",
        expiry=SessionExpiry(expires_at=now + datetime.timedelta(days=7)),
        metadata=SessionMetadata(workspace_id="user_ws_123")
    )
    
    # Bridge to standard ProviderSession
    session_id = f"session.openai.codex.mock.{int(now.timestamp())}"
    provider_session = codex_session.to_provider_session(session_id)
    
    # Register in the global registry (simulating SessionStore for this slice)
    provider_session_registry.register(provider_session)
    
    return {"status": "success", "session_id": session_id}
