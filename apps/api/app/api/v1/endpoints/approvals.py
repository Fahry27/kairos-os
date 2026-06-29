from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key, verify_operator_token
from app.core.config import Settings, get_settings
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalRequest,
    ApprovalRequestCreate,
    WorkflowRunRead,
    WorkflowRunTriggerRequest,
)
from app.services import approval_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _check_gate_enabled(settings: Settings) -> None:
    if not settings.kairos_approval_gate_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Approval gate is disabled. Enable KAIROS_APPROVAL_GATE_ENABLED in configuration.",
        )


@router.get("", response_model=list[ApprovalRequest])
def list_approvals(
    status: str | None = None,
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    _check_gate_enabled(settings)
    return approval_service.list_approvals(db, status=status, offset=offset, limit=limit)


@router.post("", response_model=ApprovalRequest, status_code=status.HTTP_201_CREATED)
def create_approval(
    payload: ApprovalRequestCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    _check_gate_enabled(settings)
    return approval_service.create_approval(
        db,
        payload,
        default_ttl_minutes=settings.kairos_approval_default_ttl_minutes,
        max_pending=settings.kairos_approval_max_pending,
    )


@router.get("/{approval_id}", response_model=ApprovalRequest)
def get_approval(
    approval_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
):
    _check_gate_enabled(settings)
    approval = approval_service.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")
    return approval


@router.post("/{approval_id}/approve", response_model=ApprovalRequest)
def approve_request(
    approval_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
    __: str = Depends(verify_operator_token),
):
    """
    Approve a pending request.
    SAFETY NOTE: This only changes the status to 'approved'. It does NOT execute the command.
    """
    _check_gate_enabled(settings)
    return approval_service.approve_request(db, approval_id)


@router.post("/{approval_id}/reject", response_model=ApprovalRequest)
def reject_request(
    approval_id: UUID,
    payload: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
    __: str = Depends(verify_operator_token),
):
    """
    Reject a pending request.
    """
    _check_gate_enabled(settings)
    return approval_service.reject_request(db, approval_id, payload)


@router.post("/{approval_id}/trigger-n8n", response_model=WorkflowRunRead)
def trigger_n8n(
    approval_id: UUID,
    payload: WorkflowRunTriggerRequest | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: str = Depends(verify_api_key),
    __: str = Depends(verify_operator_token),
):
    """
    Trigger the configured n8n webhook for an already-approved workflow approval.
    SAFETY NOTE: This only performs one synchronous n8n webhook POST. It does
    not execute local commands, call connectors, trigger Hermes/OpenClaw, call
    cloud providers, run autonomous agents, or store raw LLM/n8n responses.
    """
    _check_gate_enabled(settings)
    return approval_service.trigger_n8n_webhook(
        db,
        approval_id,
        payload or WorkflowRunTriggerRequest(),
        trigger_enabled=settings.n8n_webhook_trigger_enabled,
        webhook_url=settings.n8n_webhook_url,
        timeout_seconds=settings.n8n_webhook_timeout_seconds,
    )
