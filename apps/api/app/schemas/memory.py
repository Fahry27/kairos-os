from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MemoryTag(BaseModel):
    id: str = ""
    name: str = ""
    category: str | None = None


def _normalize_tags(v: Any) -> list[MemoryTag] | None:
    if v is None:
        return None
    result: list[MemoryTag] = []
    for item in v:
        if isinstance(item, str):
            result.append(MemoryTag(id=item, name=item))
        elif isinstance(item, dict):
            result.append(MemoryTag(**item))
        elif isinstance(item, MemoryTag):
            result.append(item)
    return result


class MemorySource(BaseModel):
    kind: str = "user"
    source_id: str | None = None
    label: str = ""


class MemoryBase(BaseModel):
    project_id: UUID | None = None
    title: str | None = None
    type: str = "note"
    content: str = Field(min_length=1)
    source: MemorySource | None = None
    tags: list[MemoryTag] | None = None
    importance: str = "normal"
    visibility: str = "mission"
    status: str = "active"
    is_pinned: bool = False


class MemoryCreate(MemoryBase):
    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[MemoryTag] | None:
        return _normalize_tags(v)


class MemoryUpdate(BaseModel):
    project_id: UUID | None = None
    title: str | None = None
    type: str | None = None
    content: str | None = Field(default=None, min_length=1)
    source: MemorySource | None = None
    tags: list[MemoryTag] | None = None
    importance: str | None = None
    visibility: str | None = None
    status: str | None = None
    is_pinned: bool | None = None

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[MemoryTag] | None:
        return _normalize_tags(v)


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID | None = None
    title: str | None = None
    type: str = "note"
    content: str = ""
    source: MemorySource | None = None
    tags: list[MemoryTag] | None = None
    importance: str = "normal"
    visibility: str = "mission"
    status: str = "active"
    is_pinned: bool = False
    created_at: datetime
    updated_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[MemoryTag] | None:
        return _normalize_tags(v)
