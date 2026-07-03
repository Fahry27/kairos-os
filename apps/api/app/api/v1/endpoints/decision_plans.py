from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import Settings, get_settings
from app.schemas.decision_plan import DecisionPlanRead, DecisionPlanStatus
from app.schemas.planner import PlannerRequest
from app.services import decision_plan_service
from app.services.planner_engine import (
    PlannerEngine,
    PlannerEngineError,
    PlannerOutputError,
    PlannerPersistenceError,
    PlannerProviderError,
    PlannerValidationError,
    planner_engine,
)

router = APIRouter(prefix="/decision-plans", tags=["decision-plans"])


class ErrorResponse(BaseModel):
    detail: str


def get_planner_engine() -> PlannerEngine:
    return planner_engine


def _planner_error_to_http(exc: PlannerEngineError) -> HTTPException:
    if isinstance(exc, PlannerValidationError | PlannerOutputError):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, PlannerProviderError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, PlannerPersistenceError):
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post(
    "",
    response_model=DecisionPlanRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        422: {"model": ErrorResponse, "description": "Invalid planning request or provider output"},
        503: {"model": ErrorResponse, "description": "Planner provider unavailable"},
    },
)
def create_decision_plan(
    payload: PlannerRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    engine: PlannerEngine = Depends(get_planner_engine),
):
    try:
        response = engine.plan(db, payload, settings)
    except PlannerEngineError as exc:
        raise _planner_error_to_http(exc) from exc
    return response.decision_plan


@router.get(
    "",
    response_model=list[DecisionPlanRead],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid API key"}},
)
def list_decision_plans(
    status_filter: DecisionPlanStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return decision_plan_service.list_decision_plans(
        db,
        status=status_filter,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{decision_plan_id}",
    response_model=DecisionPlanRead,
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        404: {"model": ErrorResponse, "description": "DecisionPlan not found"},
    },
)
def get_decision_plan(
    decision_plan_id: UUID,
    db: Session = Depends(get_db),
):
    plan = decision_plan_service.get_decision_plan(db, decision_plan_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DecisionPlan not found",
        )
    return plan
