from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
