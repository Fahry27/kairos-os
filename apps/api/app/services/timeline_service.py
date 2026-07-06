from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.timeline import TimelineEvent
from app.schemas.timeline import TimelineEventCreate


def list_events(db: Session, offset: int = 0, limit: int = 100, mission_id: str | None = None) -> list[TimelineEvent]:
    statement = select(TimelineEvent).order_by(TimelineEvent.timestamp.desc())
    if mission_id:
        statement = statement.where(TimelineEvent.mission_id == mission_id)
    statement = statement.offset(offset).limit(limit)
    return list(db.scalars(statement).all())


def get_event(db: Session, event_id: UUID) -> TimelineEvent | None:
    return db.get(TimelineEvent, event_id)


def create_event(db: Session, payload: TimelineEventCreate) -> TimelineEvent:
    data = {
        "type": payload.type,
        "title": payload.title,
        "description": payload.description,
        "scope": payload.scope,
        "severity": payload.severity,
        "mission_id": payload.mission_id,
        "workspace_id": payload.workspace_id,
        "memory_id": payload.memory_id,
        "decision_id": payload.decision_id,
        "attachments": [a.model_dump() for a in payload.attachments] if payload.attachments else [],
    }
    if payload.actor:
        data["actor_kind"] = payload.actor.kind
        data["actor_id"] = payload.actor.id
        data["actor_label"] = payload.actor.label
    if payload.source:
        data["source_kind"] = payload.source.kind
        data["source_reference"] = payload.source.reference
    event = TimelineEvent(**data)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
