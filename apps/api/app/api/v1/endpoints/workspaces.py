from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.schemas.workspace import WorkspaceStateCreate, WorkspaceStateRead, WorkspaceStateUpdate
from app.services import mock_data, workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceStateRead])
def list_workspaces(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.list_records(mock_data.WORKSPACES, offset, limit)
    return workspace_service.list_workspaces(db, offset=offset, limit=limit)


@router.post("", response_model=WorkspaceStateRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceStateCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.create_record(mock_data.WORKSPACES, payload)
    return workspace_service.create_workspace(db, payload)


@router.get("/{workspace_id}", response_model=WorkspaceStateRead)
def get_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        ws = mock_data.get_record(mock_data.WORKSPACES, workspace_id)
        if ws is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return ws
    ws = workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return ws


@router.patch("/{workspace_id}", response_model=WorkspaceStateRead)
def update_workspace(
    workspace_id: UUID,
    payload: WorkspaceStateUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        ws = mock_data.get_record(mock_data.WORKSPACES, workspace_id)
        if ws is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return mock_data.update_record(ws, payload)
    ws = workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return workspace_service.update_workspace(db, ws, payload)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        ws = mock_data.get_record(mock_data.WORKSPACES, workspace_id)
        if ws is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        mock_data.delete_record(mock_data.WORKSPACES, ws)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    ws = workspace_service.get_workspace(db, workspace_id)
    if ws is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    workspace_service.delete_workspace(db, ws)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
