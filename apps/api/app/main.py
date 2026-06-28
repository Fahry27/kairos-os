from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.monitoring import (
    check_db_health,
    get_uptime,
    is_docker,
    metrics_tracker,
    run_startup_selfchecks,
)
from app.core.plugins import plugin_registry
from app.db.base import initialize_database

# Initialize logging at import time to capture all early startup logs
setup_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up Kairos Core API...")
    settings = get_settings()

    # Perform startup self-checks
    selfchecks = run_startup_selfchecks(settings)
    app.state.selfchecks = selfchecks

    # Log selfcheck results
    for check_name, check_ok in selfchecks.items():
        if check_ok:
            logger.info(f"Startup self-check passed: {check_name}")
        else:
            logger.error(f"Startup self-check failed: {check_name}")

    # Configuration and Security Audits
    if settings.app_env == "production":
        if not settings.kairos_api_key:
            logger.critical(
                "[SECURITY] Production Mode active (APP_ENV=production), but KAIROS_API_KEY is missing or empty! Startup halted for security."
            )
            raise ValueError(
                "Production Mode active (APP_ENV=production), but KAIROS_API_KEY is missing or empty!"
            )
        
        if "*" in settings.cors_origin_list:
            logger.warning(
                "[SECURITY] CORS wildcard '*' is active when running in production (APP_ENV=production). This exposes your API to all origins!"
            )

    # Load external plugins if enabled
    if settings.kairos_plugins_enabled:
        plugin_registry.load_external_plugins(settings.resolved_plugins_dir)

    if settings.create_tables_on_startup and not settings.use_mock_data:
        initialize_database()

    logger.info("Kairos Core API startup complete.")
    yield
    logger.info("Shutting down Kairos Core API...")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        root_path=settings.root_path,
    )

    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        metrics_tracker.total_requests += 1
        try:
            response = await call_next(request)
            status_code = response.status_code
            if 200 <= status_code < 300:
                metrics_tracker.status_codes["2xx"] += 1
            elif 300 <= status_code < 400:
                metrics_tracker.status_codes["3xx"] += 1
            elif 400 <= status_code < 500:
                metrics_tracker.status_codes["4xx"] += 1
            elif 500 <= status_code < 600:
                metrics_tracker.status_codes["5xx"] += 1
            return response
        except Exception:
            metrics_tracker.status_codes["5xx"] += 1
            raise

    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    def read_root_health() -> dict:
        db_status = check_db_health(settings.use_mock_data)
        return {
            "status": "ok" if db_status in ("connected", "mock") else "error",
            "service": settings.app_name,
            "version": settings.app_version,
            "uptime": get_uptime(),
            "database": db_status,
            "docker_mode": is_docker(),
        }

    @app.get("/ready", tags=["health"])
    def read_root_ready(request: Request, response: Response) -> dict:
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

    @app.get("/metrics", tags=["monitoring"])
    def read_root_metrics() -> dict:
        db_status = check_db_health(settings.use_mock_data)
        return {
            "uptime_seconds": get_uptime(),
            "database_status": db_status,
            "docker_mode": is_docker(),
            "http_requests_total": metrics_tracker.total_requests,
            "http_response_status_codes": metrics_tracker.status_codes,
        }

    return app


app = create_app()
