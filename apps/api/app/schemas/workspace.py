from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceStateCreate(BaseModel):
    goal: str = Field(min_length=1, max_length=500)
    status: str = "active"
    context: dict | None = None
    plan_json: list | None = None
    decisions: list | None = None
    notes: str | None = None


class WorkspaceStateUpdate(BaseModel):
    goal: str | None = None
    status: str | None = None
    context: dict | None = None
    plan_json: list | None = None
    decisions: list | None = None
    notes: str | None = None


class WorkspaceStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    goal: str
    status: str
    context: dict | None = None
    plan_json: list | None = None
    decisions: list | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
