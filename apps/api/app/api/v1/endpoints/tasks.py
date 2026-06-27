from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services import mock_data, task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.list_records(mock_data.TASKS, offset, limit)
    return task_service.list_tasks(db, offset=offset, limit=limit)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.create_record(mock_data.TASKS, payload)
    return task_service.create_task(db, payload)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        task = mock_data.get_record(mock_data.TASKS, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return task
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        task = mock_data.get_record(mock_data.TASKS, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return mock_data.update_record(task, payload)
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task_service.update_task(db, task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        task = mock_data.get_record(mock_data.TASKS, task_id)
        if task is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        mock_data.delete_record(mock_data.TASKS, task)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    task = task_service.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task_service.delete_task(db, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
