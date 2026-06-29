from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.schemas.approval import WorkflowRunRead, WorkflowRunStatus, WorkflowRunTargetType
from app.services import workflow_run_service

router = APIRouter(prefix="/workflow-runs", tags=["workflow-runs"])


@router.get("", response_model=list[WorkflowRunRead])
def list_workflow_runs(
    status_filter: WorkflowRunStatus | None = Query(default=None, alias="status"),
    approval_id: UUID | None = None,
    target_type: WorkflowRunTargetType | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    return workflow_run_service.list_workflow_runs(
        db,
        status=status_filter.value if status_filter else None,
        approval_id=approval_id,
        target_type=target_type.value if target_type else None,
        offset=offset,
        limit=limit,
    )


@router.get("/{run_id}", response_model=WorkflowRunRead)
def get_workflow_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    run = workflow_run_service.get_workflow_run(db, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow run not found",
        )
    return run
