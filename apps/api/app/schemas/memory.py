from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemoryBase(BaseModel):
    project_id: UUID | None = None
    type: str = "note"
    content: str = Field(min_length=1)
    source: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    importance: str = "normal"


class MemoryCreate(MemoryBase):
    pass


class MemoryUpdate(BaseModel):
    project_id: UUID | None = None
    type: str | None = None
    content: str | None = Field(default=None, min_length=1)
    source: str | None = Field(default=None, max_length=255)
    tags: list[str] | None = None
    importance: str | None = None


class MemoryRead(MemoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
