from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


SENSITIVE_SUMMARY_KEYS = {
    "api_key",
    "authorization",
    "body",
    "credential",
    "credentials",
    "env",
    "environment",
    "password",
    "raw",
    "raw_body",
    "raw_llm_response",
    "raw_n8n_response",
    "raw_response",
    "response_body",
    "secret",
    "token",
    "url",
    "webhook_url",
}


def _is_sensitive_summary_key(key: str) -> bool:
    normalized = key.lower()
    return normalized in SENSITIVE_SUMMARY_KEYS or any(
        fragment in normalized for fragment in ("token", "secret", "credential", "password")
    )


def sanitize_summary(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if _is_sensitive_summary_key(str(key)) else sanitize_summary(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_summary(item) for item in value]
    return value


class ApprovalActionType(str, Enum):
    command = "command"
    connector = "connector"
    workflow = "workflow"
    memory = "memory"
    project = "project"
    task = "task"
    generic = "generic"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class ApprovalRiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class WorkflowRunTargetType(str, Enum):
    n8n_webhook = "n8n_webhook"


class WorkflowRunStatus(str, Enum):
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class ApprovalRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    action_type: ApprovalActionType
    proposed_action_id: str | None = None
    source: str = Field(min_length=1, max_length=255)
    risk_level: ApprovalRiskLevel = ApprovalRiskLevel.medium
    requires_manual_review: bool = True
    payload_summary: dict[str, Any] | None = None
    safety_notes: list[str] = Field(default_factory=list)
    expires_in_minutes: int | None = None


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    action_type: ApprovalActionType
    proposed_action_id: str | None = None
    source: str
    risk_level: ApprovalRiskLevel
    requires_manual_review: bool
    payload_summary: dict[str, Any] | None = None
    safety_notes: list[str]
    status: ApprovalStatus
    created_at: datetime
    expires_at: datetime
    decided_at: datetime | None = None
    decision_reason: str | None = None
    
    # Non-executing safety flags (hard-gated False for now)
    execution_enabled: bool = False
    execution_performed: bool = False
    connector_calls_performed: bool = False
    data_mutation_performed: bool = False


class ApprovalDecisionRequest(BaseModel):
    reason: str | None = None


class WorkflowRunTriggerRequest(BaseModel):
    retry_failed: bool = False


class WorkflowRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    approval_id: UUID
    target_type: WorkflowRunTargetType
    status: WorkflowRunStatus
    started_at: datetime
    finished_at: datetime | None = None
    http_status_code: int | None = None
    sanitized_error: str | None = None
    request_summary: dict[str, Any] | None = None
    response_summary: dict[str, Any] | None = None

    @field_validator("request_summary", "response_summary", mode="before")
    @classmethod
    def sanitize_run_summary(cls, value: Any) -> Any:
        return sanitize_summary(value)
