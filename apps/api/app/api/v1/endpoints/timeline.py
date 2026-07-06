from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.schemas.timeline import TimelineEventCreate, TimelineEventRead
from app.services import mock_data, timeline_service

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("", response_model=list[TimelineEventRead])
def list_events(
    offset: int = 0,
    limit: int = 100,
    mission_id: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.list_records(mock_data.TIMELINE_EVENTS, offset, limit)
    return timeline_service.list_events(db, offset=offset, limit=limit, mission_id=mission_id)


@router.post("", response_model=TimelineEventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        return mock_data.create_record(mock_data.TIMELINE_EVENTS, payload)
    return timeline_service.create_event(db, payload)


@router.get("/{event_id}", response_model=TimelineEventRead)
def get_event(
    event_id: UUID,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.use_mock_data:
        event = mock_data.get_record(mock_data.TIMELINE_EVENTS, event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event
    event = timeline_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
