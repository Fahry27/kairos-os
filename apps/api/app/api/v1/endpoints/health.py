from fastapi import APIRouter, Depends, Request, Response, status

from app.core.config import Settings, get_settings
from app.core.monitoring import check_db_health, get_uptime, is_docker, metrics_tracker

router = APIRouter(tags=["health"])


@router.get("/health")
def read_health(settings: Settings = Depends(get_settings)) -> dict:
    db_status = check_db_health(settings.use_mock_data)
    return {
        "status": "ok" if db_status in ("connected", "mock") else "error",
        "service": settings.app_name,
        "version": settings.app_version,
        "uptime": get_uptime(),
        "database": db_status,
        "docker_mode": is_docker(),
    }


@router.get("/ready")
def read_ready(
    request: Request, response: Response, settings: Settings = Depends(get_settings)
) -> dict:
    selfchecks = getattr(request.app.state, "selfchecks", {})
    db_status = check_db_health(settings.use_mock_data)
    all_ok = all(selfchecks.values()) and db_status in ("connected", "mock")
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "database": db_status,
            "checks": selfchecks,
        }
    return {
        "status": "ready",
        "database": db_status,
        "checks": selfchecks,
    }


@router.get("/metrics")
def read_metrics(settings: Settings = Depends(get_settings)) -> dict:
    db_status = check_db_health(settings.use_mock_data)
    return {
        "uptime_seconds": get_uptime(),
        "database_status": db_status,
        "docker_mode": is_docker(),
        "http_requests_total": metrics_tracker.total_requests,
        "http_response_status_codes": metrics_tracker.status_codes,
    }
