from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, JSON, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft", index=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium", index=True)
    # Mission lifecycle extensions (v3.4.0)
    trigger_kind: Mapped[str | None] = mapped_column(String(50), nullable=True, default="user")
    trigger_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trigger_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    plans: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    active_plan_version: Mapped[int | None] = mapped_column(nullable=True)
    approvals: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    step_executions: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    artifacts: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    outcome: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    tasks = relationship("Task", back_populates="project", passive_deletes=True)
