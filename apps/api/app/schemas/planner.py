from typing import Any

from pydantic import BaseModel, Field

from app.schemas.decision_plan import DecisionPlanRead


class PlannerRequest(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)
    context: dict[str, Any] = Field(default_factory=dict)
    provider_id: str | None = None
    model: str | None = None
    workspace_session_id: str | None = Field(default=None, max_length=255)
    fallback_enabled: bool | None = None


class PlannerResponse(BaseModel):
    decision_plan: DecisionPlanRead
    provider_attempts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    persisted: bool = True


class PlannerConfig(BaseModel):
    enabled: bool = True
    max_provider_response_chars: int = Field(default=8000, gt=0)
