import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    approval_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("approvals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, default="n8n_webhook")
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sanitized_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    _request_summary: Mapped[str | None] = mapped_column("request_summary", Text, nullable=True)
    _response_summary: Mapped[str | None] = mapped_column("response_summary", Text, nullable=True)

    approval = relationship("Approval", back_populates="workflow_runs")

    @property
    def request_summary(self) -> dict[str, Any] | None:
        if self._request_summary:
            try:
                return json.loads(self._request_summary)
            except json.JSONDecodeError:
                return None
        return None

    @request_summary.setter
    def request_summary(self, value: dict[str, Any] | None) -> None:
        self._request_summary = json.dumps(value) if value is not None else None

    @property
    def response_summary(self) -> dict[str, Any] | None:
        if self._response_summary:
            try:
                return json.loads(self._response_summary)
            except json.JSONDecodeError:
                return None
        return None

    @response_summary.setter
    def response_summary(self, value: dict[str, Any] | None) -> None:
        self._response_summary = json.dumps(value) if value is not None else None
