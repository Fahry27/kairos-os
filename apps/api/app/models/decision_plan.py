import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.schemas.decision_plan import (
    DECISION_PLAN_SCHEMA_VERSION,
    DecisionPlanStatus,
)


def _load_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _load_json_array(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


class DecisionPlan(Base):
    __tablename__ = "decision_plans"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    schema_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DECISION_PLAN_SCHEMA_VERSION,
    )
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DecisionPlanStatus.draft.value,
        index=True,
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    root_decision_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    parent_decision_plan_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    workspace_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    _primary_path: Mapped[str] = mapped_column("primary_path", Text, nullable=False)
    _alternatives: Mapped[str] = mapped_column("alternatives", Text, nullable=False, default="[]")
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    _evidence: Mapped[str] = mapped_column("evidence", Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    _assumptions: Mapped[str] = mapped_column("assumptions", Text, nullable=False, default="[]")
    _risks: Mapped[str] = mapped_column("risks", Text, nullable=False, default="[]")
    _constraints: Mapped[str] = mapped_column("constraints", Text, nullable=False, default="[]")
    success_definition: Mapped[str] = mapped_column(Text, nullable=False)
    _provider_trace: Mapped[str] = mapped_column("provider_trace", Text, nullable=False)
    _safety_flags: Mapped[str] = mapped_column("safety_flags", Text, nullable=False)
    approval_request_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def primary_path(self) -> dict[str, Any]:
        return _load_json_object(self._primary_path)

    @primary_path.setter
    def primary_path(self, value: dict[str, Any]) -> None:
        self._primary_path = json.dumps(value)

    @property
    def alternatives(self) -> list[Any]:
        return _load_json_array(self._alternatives)

    @alternatives.setter
    def alternatives(self, value: list[Any] | None) -> None:
        self._alternatives = json.dumps(value or [])

    @property
    def evidence(self) -> list[Any]:
        return _load_json_array(self._evidence)

    @evidence.setter
    def evidence(self, value: list[Any]) -> None:
        self._evidence = json.dumps(value)

    @property
    def assumptions(self) -> list[Any]:
        return _load_json_array(self._assumptions)

    @assumptions.setter
    def assumptions(self, value: list[Any] | None) -> None:
        self._assumptions = json.dumps(value or [])

    @property
    def risks(self) -> list[Any]:
        return _load_json_array(self._risks)

    @risks.setter
    def risks(self, value: list[Any] | None) -> None:
        self._risks = json.dumps(value or [])

    @property
    def constraints(self) -> list[Any]:
        return _load_json_array(self._constraints)

    @constraints.setter
    def constraints(self, value: list[Any] | None) -> None:
        self._constraints = json.dumps(value or [])

    @property
    def provider_trace(self) -> dict[str, Any]:
        return _load_json_object(self._provider_trace)

    @provider_trace.setter
    def provider_trace(self, value: dict[str, Any]) -> None:
        self._provider_trace = json.dumps(value)

    @property
    def safety_flags(self) -> dict[str, Any]:
        return _load_json_object(self._safety_flags)

    @safety_flags.setter
    def safety_flags(self, value: dict[str, Any]) -> None:
        self._safety_flags = json.dumps(value)
