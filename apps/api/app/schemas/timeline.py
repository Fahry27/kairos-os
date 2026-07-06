from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TimelineAttachment(BaseModel):
    kind: str = "text"
    ref_id: str | None = None
    label: str = ""
    inline: str | None = None


class TimelineActor(BaseModel):
    kind: str = "user"
    id: str | None = None
    label: str = ""


class TimelineSource(BaseModel):
    kind: str = "shell"
    reference: str | None = None


class TimelineEventCreate(BaseModel):
    type: str
    title: str
    description: str | None = None
    actor: TimelineActor | None = None
    source: TimelineSource | None = None
    scope: str = "global"
    severity: str = "info"
    mission_id: str | None = None
    workspace_id: str | None = None
    memory_id: str | None = None
    decision_id: str | None = None
    attachments: list[TimelineAttachment] | None = Field(default_factory=list)


class TimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    description: str | None = None
    timestamp: datetime
    actor_kind: str | None = None
    actor_id: str | None = None
    actor_label: str | None = None
    source_kind: str | None = None
    source_reference: str | None = None
    scope: str = "global"
    severity: str = "info"
    mission_id: str | None = None
    workspace_id: str | None = None
    memory_id: str | None = None
    decision_id: str | None = None
    attachments: list | None = None
    created_at: datetime
