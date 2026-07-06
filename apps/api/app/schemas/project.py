from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MissionTrigger(BaseModel):
    kind: str = "user"
    source_id: str | None = None
    description: str = ""


class MissionContext(BaseModel):
    related_mission_ids: list[str] = Field(default_factory=list)
    user_notes: str = ""
    constraints: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class MissionPlan(BaseModel):
    version: int = 1
    summary: str = ""
    steps: list = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    success_definition: str = ""
    generated_by: str | None = None
    created_at: str = ""


class MissionApproval(BaseModel):
    id: str
    mission_id: str = ""
    step_id: str | None = None
    title: str = ""
    description: str = ""
    status: str = "pending"
    requested_by: str = ""
    decision_reason: str | None = None
    requested_at: str = ""
    decided_at: str | None = None


class MissionStepExecution(BaseModel):
    id: str
    mission_id: str = ""
    step_id: str = ""
    status: str = "queued"
    started_at: str | None = None
    completed_at: str | None = None
    retry_count: int = 0
    error: str | None = None
    result_summary: str | None = None


class MissionArtifact(BaseModel):
    id: str
    mission_id: str = ""
    step_id: str | None = None
    kind: str = "text"
    title: str = ""
    content_ref: str = ""
    created_at: str = ""


class MissionOutcome(BaseModel):
    status: str = "completed"
    summary: str = ""
    learnings: list[str] = Field(default_factory=list)
    artifacts: list[MissionArtifact] = Field(default_factory=list)
    recorded_at: str = ""


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = "draft"
    priority: str = "medium"
    trigger_kind: str | None = "user"
    trigger_source_id: str | None = None
    trigger_description: str | None = None
    context: MissionContext | None = None
    plans: list[MissionPlan] | None = None
    active_plan_version: int | None = None
    approvals: list[MissionApproval] | None = None
    step_executions: list[MissionStepExecution] | None = None
    artifacts: list[MissionArtifact] | None = None
    outcome: MissionOutcome | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    trigger_kind: str | None = None
    trigger_source_id: str | None = None
    trigger_description: str | None = None
    context: MissionContext | None = None
    plans: list[MissionPlan] | None = None
    active_plan_version: int | None = None
    approvals: list[MissionApproval] | None = None
    step_executions: list[MissionStepExecution] | None = None
    artifacts: list[MissionArtifact] | None = None
    outcome: MissionOutcome | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
    triggered_at: datetime | None = None
