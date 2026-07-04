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


@router.get("/runtime-status")
def get_runtime_status(settings: Settings = Depends(get_settings)) -> dict:
    from app.core.ai_runtime import ai_runtime
    from app.core.codex_runtime import CodexCliRuntime
    
    # Check Ollama
    ollama_res = ai_runtime.check_ollama_readiness(settings)
    if ollama_res.reachable:
        ollama_status = "connected"
        ollama_msg = "Ollama is ready"
    elif ollama_res.reachable is False:
        ollama_status = "error"
        ollama_msg = ollama_res.message or "Unable to reach Ollama"
    else:
        ollama_status = "offline"
        ollama_msg = "Ollama is not configured or offline"
        
    # Check Codex
    codex_res = CodexCliRuntime().check_readiness()
    if codex_res.reachable:
        codex_status = "connected"
        codex_msg = "Codex CLI is ready"
    elif codex_res.error_type == "not_installed":
        codex_status = "not_installed"
        codex_msg = "Codex CLI is not installed"
    elif codex_res.error_type == "not_authenticated":
        codex_status = "not_authenticated"
        codex_msg = "Codex CLI is not authenticated"
    else:
        codex_status = "error"
        codex_msg = codex_res.message or "Unable to reach Codex CLI"

    return {
        "runtimes": [
            {
                "id": "runtime.codex-cli",
                "name": "Codex CLI",
                "status": codex_status,
                "message": codex_msg
            },
            {
                "id": "runtime.ollama",
                "name": "Ollama",
                "status": ollama_status,
                "message": ollama_msg
            },
            {
                "id": "runtime.gemini",
                "name": "Gemini",
                "status": "coming_soon",
                "message": "Coming soon"
            }
        ]
    }
