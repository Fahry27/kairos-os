from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, verify_api_key
from app.core.config import Settings, get_settings
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalRequest,
    ApprovalRequestCreate,
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
):
    """
    Reject a pending request.
    """
    _check_gate_enabled(settings)
    return approval_service.reject_request(db, approval_id, payload)
