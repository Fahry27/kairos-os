from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.approval import Approval
from app.models.workflow_run import WorkflowRun
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalRequestCreate,
    ApprovalStatus,
    WorkflowRunStatus,
    WorkflowRunTargetType,
    WorkflowRunTriggerRequest,
)


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


def _approval_workflow_type(approval: Approval) -> str | None:
    if approval.proposed_action_id == WorkflowRunTargetType.n8n_webhook.value:
        return WorkflowRunTargetType.n8n_webhook.value
    payload_summary = approval.payload_summary or {}
    workflow_type = payload_summary.get("workflow_type")
    if workflow_type == WorkflowRunTargetType.n8n_webhook.value:
        return WorkflowRunTargetType.n8n_webhook.value
    return None


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc).isoformat()
    return value.astimezone(timezone.utc).isoformat()


def _build_n8n_request_summary(approval: Approval, started_at: datetime) -> dict[str, str | None]:
    return {
        "source": "kairos",
        "event": "approval.trigger_n8n",
        "approval_id": str(approval.id),
        "target_type": WorkflowRunTargetType.n8n_webhook.value,
        "action_type": approval.action_type,
        "workflow_type": WorkflowRunTargetType.n8n_webhook.value,
        "proposed_action_id": approval.proposed_action_id,
        "approved_at": _isoformat(approval.decided_at),
        "triggered_at": _isoformat(started_at),
    }


def _build_response_summary(response: httpx.Response, result: str) -> dict[str, int | str]:
    return {
        "result": result,
        "body_bytes": len(response.content),
    }


def _latest_n8n_runs(db: Session, approval_id: UUID) -> list[WorkflowRun]:
    statement = (
        select(WorkflowRun)
        .where(
            WorkflowRun.approval_id == approval_id,
            WorkflowRun.target_type == WorkflowRunTargetType.n8n_webhook.value,
        )
        .order_by(WorkflowRun.started_at.desc())
    )
    return list(db.scalars(statement).all())


def _validate_trigger_state(
    approval: Approval,
    existing_runs: list[WorkflowRun],
    payload: WorkflowRunTriggerRequest,
) -> None:
    if approval.status != ApprovalStatus.approved.value:
        raise HTTPException(
            status_code=409,
            detail="Only approved workflow approvals can trigger n8n.",
        )
    if approval.action_type != "workflow":
        raise HTTPException(
            status_code=409,
            detail="Only workflow approvals can trigger n8n.",
        )
    if _approval_workflow_type(approval) != WorkflowRunTargetType.n8n_webhook.value:
        raise HTTPException(
            status_code=409,
            detail="Only n8n webhook workflow approvals can trigger n8n.",
        )
    if any(run.status == WorkflowRunStatus.succeeded.value for run in existing_runs):
        raise HTTPException(
            status_code=409,
            detail="This approval has already triggered n8n successfully.",
        )
    if any(run.status == WorkflowRunStatus.running.value for run in existing_runs):
        raise HTTPException(
            status_code=409,
            detail="This approval already has an n8n trigger in progress.",
        )
    if existing_runs and not payload.retry_failed:
        raise HTTPException(
            status_code=409,
            detail="Previous n8n trigger failed. Set retry_failed=true to retry explicitly.",
        )


def trigger_n8n_webhook(
    db: Session,
    approval_id: UUID,
    payload: WorkflowRunTriggerRequest,
    trigger_enabled: bool,
    webhook_url: str,
    timeout_seconds: int,
) -> WorkflowRun:
    expire_pending_requests(db)

    approval = db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if not trigger_enabled:
        raise HTTPException(status_code=403, detail="n8n webhook triggering is disabled.")
    if not webhook_url.strip():
        raise HTTPException(status_code=503, detail="n8n webhook triggering is not configured.")

    existing_runs = _latest_n8n_runs(db, approval_id)
    _validate_trigger_state(approval, existing_runs, payload)

    started_at = _now()
    request_summary = _build_n8n_request_summary(approval, started_at)
    run = WorkflowRun(
        approval_id=approval.id,
        target_type=WorkflowRunTargetType.n8n_webhook.value,
        status=WorkflowRunStatus.running.value,
        started_at=started_at,
        request_summary=request_summary,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        response = httpx.post(webhook_url, json=request_summary, timeout=timeout_seconds)
    except httpx.TimeoutException:
        run.status = WorkflowRunStatus.failed.value
        run.finished_at = _now()
        run.sanitized_error = "n8n_webhook_timeout"
        run.response_summary = {"result": "timeout"}
    except httpx.RequestError:
        run.status = WorkflowRunStatus.failed.value
        run.finished_at = _now()
        run.sanitized_error = "n8n_webhook_request_error"
        run.response_summary = {"result": "request_error"}
    else:
        run.http_status_code = response.status_code
        run.finished_at = _now()
        if 200 <= response.status_code < 300:
            run.status = WorkflowRunStatus.succeeded.value
            run.response_summary = _build_response_summary(response, "succeeded")
        else:
            run.status = WorkflowRunStatus.failed.value
            run.sanitized_error = "n8n_webhook_non_2xx_response"
            run.response_summary = _build_response_summary(response, "non_2xx")

    db.add(run)
    db.commit()
    db.refresh(run)
    return run
