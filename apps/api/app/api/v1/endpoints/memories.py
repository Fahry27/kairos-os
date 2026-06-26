from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.schemas.memory import MemoryCreate, MemoryRead, MemoryUpdate
from app.services import memory_service

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("", response_model=list[MemoryRead])
def list_memories(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return memory_service.list_memories(db, offset=offset, limit=limit)


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
def create_memory(payload: MemoryCreate, db: Session = Depends(get_db)):
    return memory_service.create_memory(db, payload)


@router.get("/{memory_id}", response_model=MemoryRead)
def get_memory(memory_id: UUID, db: Session = Depends(get_db)):
    memory = memory_service.get_memory(db, memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory


@router.patch("/{memory_id}", response_model=MemoryRead)
def update_memory(memory_id: UUID, payload: MemoryUpdate, db: Session = Depends(get_db)):
    memory = memory_service.get_memory(db, memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    return memory_service.update_memory(db, memory, payload)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: UUID, db: Session = Depends(get_db)):
    memory = memory_service.get_memory(db, memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
    memory_service.delete_memory(db, memory)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
