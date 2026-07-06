from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import WorkspaceState
from app.schemas.workspace import WorkspaceStateCreate, WorkspaceStateUpdate


def list_workspaces(db: Session, offset: int = 0, limit: int = 100) -> list[WorkspaceState]:
    statement = select(WorkspaceState).offset(offset).limit(limit).order_by(WorkspaceState.created_at.desc())
    return list(db.scalars(statement).all())


def get_workspace(db: Session, workspace_id: UUID) -> WorkspaceState | None:
    return db.get(WorkspaceState, workspace_id)


def create_workspace(db: Session, payload: WorkspaceStateCreate) -> WorkspaceState:
    ws = WorkspaceState(**payload.model_dump())
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def update_workspace(db: Session, ws: WorkspaceState, payload: WorkspaceStateUpdate) -> WorkspaceState:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ws, key, value)
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def delete_workspace(db: Session, ws: WorkspaceState) -> None:
    db.delete(ws)
    db.commit()
