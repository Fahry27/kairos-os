from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import mock_data, project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.list_records(mock_data.PROJECTS, offset, limit)
    return project_service.list_projects(db, offset=offset, limit=limit)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.create_record(mock_data.PROJECTS, payload)
    return project_service.create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        project = mock_data.get_record(mock_data.PROJECTS, project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        project = mock_data.get_record(mock_data.PROJECTS, project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return mock_data.update_record(project, payload)
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project_service.update_project(db, project, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        project = mock_data.get_record(mock_data.PROJECTS, project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        mock_data.delete_record(mock_data.PROJECTS, project)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    project = project_service.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project_service.delete_project(db, project)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
