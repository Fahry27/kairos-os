from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.schemas.memory import MemoryCreate, MemoryUpdate


def list_memories(db: Session, offset: int = 0, limit: int = 100) -> list[Memory]:
    statement = select(Memory).offset(offset).limit(limit).order_by(Memory.created_at.desc())
    return list(db.scalars(statement).all())


def get_memory(db: Session, memory_id: UUID) -> Memory | None:
    return db.get(Memory, memory_id)


def _memory_create_data(payload: MemoryCreate) -> dict:
    data = payload.model_dump(exclude={"source"})
    if payload.source:
        data["source_kind"] = payload.source.kind
        data["source_id"] = payload.source.source_id
        data["source_label"] = payload.source.label
    return data


def create_memory(db: Session, payload: MemoryCreate) -> Memory:
    memory = Memory(**_memory_create_data(payload))
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def _memory_update_data(payload: MemoryUpdate) -> dict:
    data = payload.model_dump(exclude_unset=True, exclude={"source"})
    if payload.source is not None:
        data["source_kind"] = payload.source.kind if payload.source else None
        data["source_id"] = payload.source.source_id if payload.source else None
        data["source_label"] = payload.source.label if payload.source else None
    return data


def update_memory(db: Session, memory: Memory, payload: MemoryUpdate) -> Memory:
    for key, value in _memory_update_data(payload).items():
        setattr(memory, key, value)
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory


def delete_memory(db: Session, memory: Memory) -> None:
    db.delete(memory)
    db.commit()
