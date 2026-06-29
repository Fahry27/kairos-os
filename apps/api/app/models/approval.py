import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    proposed_action_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # SQLite JSON storage mapping
    _payload_summary: Mapped[str | None] = mapped_column("payload_summary", Text, nullable=True)
    _safety_notes: Mapped[str | None] = mapped_column("safety_notes", Text, nullable=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def payload_summary(self) -> dict[str, Any] | None:
        if self._payload_summary:
            try:
                return json.loads(self._payload_summary)
            except json.JSONDecodeError:
                return None
        return None

    @payload_summary.setter
    def payload_summary(self, value: dict[str, Any] | None) -> None:
        self._payload_summary = json.dumps(value) if value is not None else None

    @property
    def safety_notes(self) -> list[str]:
        if self._safety_notes:
            try:
                return json.loads(self._safety_notes)
            except json.JSONDecodeError:
                return []
        return []

    @safety_notes.setter
    def safety_notes(self, value: list[str]) -> None:
        self._safety_notes = json.dumps(value) if value else "[]"
