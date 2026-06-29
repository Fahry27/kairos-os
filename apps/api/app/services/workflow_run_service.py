from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow_run import WorkflowRun


def list_workflow_runs(
    db: Session,
    status: str | None = None,
    approval_id: UUID | None = None,
    target_type: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[WorkflowRun]:
    statement = select(WorkflowRun)
    if status:
        statement = statement.where(WorkflowRun.status == status)
    if approval_id:
        statement = statement.where(WorkflowRun.approval_id == approval_id)
    if target_type:
        statement = statement.where(WorkflowRun.target_type == target_type)
    statement = statement.order_by(WorkflowRun.started_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


def get_workflow_run(db: Session, run_id: UUID) -> WorkflowRun | None:
    return db.get(WorkflowRun, run_id)
