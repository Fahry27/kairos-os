from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


DECISION_PLAN_SCHEMA_VERSION = "decision_plan.v1"


class DecisionPlanStatus(str, Enum):
    draft = "draft"
    generating = "generating"
    validating = "validating"
    proposed = "proposed"


class DecisionCapabilityRefType(str, Enum):
    plugin = "plugin"
    command = "command"
    connector = "connector"
    workflow = "workflow"


class DecisionRiskSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DecisionCapabilityRef(BaseModel):
    type: DecisionCapabilityRefType
    id: str = Field(min_length=1, max_length=255)


class DecisionPath(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=2000)
    steps: list[str] = Field(min_length=1, max_length=12)
    capability_refs: list[DecisionCapabilityRef] = Field(default_factory=list, max_length=20)


class DecisionEvidence(BaseModel):
    source: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1, max_length=1000)
    reference_id: str | None = Field(default=None, max_length=255)


class DecisionRisk(BaseModel):
    severity: DecisionRiskSeverity
    description: str = Field(min_length=1, max_length=1000)
    mitigation: str | None = Field(default=None, max_length=1000)


class DecisionProviderTrace(BaseModel):
    provider_id: str | None = None
    model: str | None = None
    dispatch_used: bool = False
    fallback_used: bool = False
    warnings: list[str] = Field(default_factory=list)


class DecisionSafetyFlags(BaseModel):
    execution_enabled: Literal[False] = False
    approval_mutation_performed: Literal[False] = False
    approval_requests_created: Literal[False] = False
    workflow_triggered: Literal[False] = False
    workflow_runs_created: Literal[False] = False
    connector_calls_performed: Literal[False] = False
    data_mutation_performed: Literal[False] = False


class DecisionPlanBase(BaseModel):
    schema_version: Literal["decision_plan.v1"] = DECISION_PLAN_SCHEMA_VERSION
    goal: str = Field(min_length=1, max_length=2000)
    status: DecisionPlanStatus = DecisionPlanStatus.draft
    revision: int = Field(default=1, ge=1)
    root_decision_id: UUID | None = None
    parent_decision_plan_id: UUID | None = None
    workspace_session_id: str | None = Field(default=None, max_length=255)
    primary_path: DecisionPath
    alternatives: list[DecisionPath] = Field(default_factory=list, max_length=5)
    rationale: str = Field(min_length=1, max_length=4000)
    evidence: list[DecisionEvidence] = Field(min_length=1, max_length=20)
    confidence: float = Field(ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    risks: list[DecisionRisk] = Field(default_factory=list, max_length=20)
    constraints: list[str] = Field(default_factory=list, max_length=20)
    success_definition: str = Field(min_length=1, max_length=2000)
    provider_trace: DecisionProviderTrace = Field(default_factory=DecisionProviderTrace)
    safety_flags: DecisionSafetyFlags = Field(default_factory=DecisionSafetyFlags)
    approval_request_id: UUID | None = None

    @model_validator(mode="after")
    def validate_decision_plan_invariants(self) -> "DecisionPlanBase":
        primary_key = (self.primary_path.title.strip(), self.primary_path.summary.strip())
        for alternative in self.alternatives:
            alternative_key = (alternative.title.strip(), alternative.summary.strip())
            if alternative_key == primary_key:
                raise ValueError("alternatives must not duplicate the primary path")
        return self


class DecisionPlanCreate(DecisionPlanBase):
    pass


class DecisionPlanRead(DecisionPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
