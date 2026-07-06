from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def list_projects(db: Session, offset: int = 0, limit: int = 100) -> list[Project]:
    statement = select(Project).offset(offset).limit(limit).order_by(Project.created_at.desc())
    return list(db.scalars(statement).all())


def get_project(db: Session, project_id: UUID) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: Session, payload: ProjectCreate) -> Project:
    data = payload.model_dump(exclude={"context", "plans", "approvals", "step_executions", "artifacts", "outcome"})
    data["context"] = payload.context.model_dump() if payload.context else {}
    data["plans"] = [p.model_dump() for p in payload.plans] if payload.plans else []
    data["approvals"] = [a.model_dump() for a in payload.approvals] if payload.approvals else []
    data["step_executions"] = [s.model_dump() for s in payload.step_executions] if payload.step_executions else []
    data["artifacts"] = [a.model_dump() for a in payload.artifacts] if payload.artifacts else []
    data["outcome"] = payload.outcome.model_dump() if payload.outcome else None
    data["triggered_at"] = datetime.now(timezone.utc)
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project: Project, payload: ProjectUpdate) -> Project:
    data = payload.model_dump(exclude_unset=True, exclude={"context", "plans", "approvals", "step_executions", "artifacts", "outcome"})
    if payload.context is not None:
        data["context"] = payload.context.model_dump() if payload.context else {}
    if payload.plans is not None:
        data["plans"] = [p.model_dump() for p in payload.plans] if payload.plans else []
    if payload.approvals is not None:
        data["approvals"] = [a.model_dump() for a in payload.approvals] if payload.approvals else []
    if payload.step_executions is not None:
        data["step_executions"] = [s.model_dump() for s in payload.step_executions] if payload.step_executions else []
    if payload.artifacts is not None:
        data["artifacts"] = [a.model_dump() for a in payload.artifacts] if payload.artifacts else []
    if hasattr(payload, "outcome") and payload.outcome is not None:
        data["outcome"] = payload.outcome.model_dump()
    elif hasattr(payload, "outcome"):
        data["outcome"] = None
    for key, value in data.items():
        setattr(project, key, value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
