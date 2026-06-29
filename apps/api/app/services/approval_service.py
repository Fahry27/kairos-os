from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.schemas.approval import ApprovalDecisionRequest, ApprovalRequestCreate, ApprovalStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def expire_pending_requests(db: Session) -> None:
    """Check all pending requests and set to expired if expires_at has passed."""
    statement = select(Approval).where(Approval.status == ApprovalStatus.pending.value)
    pending = db.scalars(statement).all()
    now = _now()
    changed = False
    for req in pending:
        req_expires = req.expires_at.replace(tzinfo=timezone.utc) if req.expires_at.tzinfo is None else req.expires_at
        if req_expires <= now:
            req.status = ApprovalStatus.expired.value
            db.add(req)
            changed = True
    if changed:
        db.commit()


def list_approvals(db: Session, status: str | None = None, offset: int = 0, limit: int = 100) -> list[Approval]:
    expire_pending_requests(db)
    
    statement = select(Approval)
    if status:
        statement = statement.where(Approval.status == status)
    statement = statement.order_by(Approval.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(statement).all())


def get_approval(db: Session, approval_id: UUID) -> Approval | None:
    expire_pending_requests(db)
    return db.get(Approval, approval_id)


def create_approval(
    db: Session, payload: ApprovalRequestCreate, default_ttl_minutes: int, max_pending: int
) -> Approval:
    expire_pending_requests(db)

    # Check max pending limit
    statement = select(Approval).where(Approval.status == ApprovalStatus.pending.value)
    current_pending_count = len(db.scalars(statement).all())
    
    if current_pending_count >= max_pending:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum pending approvals ({max_pending}) reached. Please approve or reject existing requests.",
        )

    ttl = payload.expires_in_minutes or default_ttl_minutes
    expires_at = _now() + timedelta(minutes=ttl)

    approval = Approval(
        title=payload.title,
        description=payload.description,
        action_type=payload.action_type.value,
        proposed_action_id=payload.proposed_action_id,
        source=payload.source,
        risk_level=payload.risk_level.value,
        requires_manual_review=payload.requires_manual_review,
        payload_summary=payload.payload_summary,
        safety_notes=payload.safety_notes,
        status=ApprovalStatus.pending.value,
        expires_at=expires_at,
    )
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def approve_request(db: Session, approval_id: UUID) -> Approval:
    expire_pending_requests(db)
    
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != ApprovalStatus.pending.value:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve request in '{approval.status}' state. Only pending requests can be approved.",
        )

    approval.status = ApprovalStatus.approved.value
    approval.decided_at = _now()
    
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    return approval


def reject_request(db: Session, approval_id: UUID, payload: ApprovalDecisionRequest) -> Approval:
    expire_pending_requests(db)
    
    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != ApprovalStatus.pending.value:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject request in '{approval.status}' state. Only pending requests can be rejected.",
        )

    approval.status = ApprovalStatus.rejected.value
    approval.decided_at = _now()
    if payload.reason:
        approval.decision_reason = payload.reason
        
    db.add(approval)
    db.commit()
    db.refresh(approval)
    
    return approval
