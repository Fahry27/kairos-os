import logging
import os
import time
from pathlib import Path
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Track startup time for uptime metric
START_TIME = time.time()


def get_uptime() -> int:
    """Returns application uptime in seconds."""
    return int(time.time() - START_TIME)


def is_docker() -> bool:
    """Detects if running inside a Docker container."""
    return os.path.exists("/.dockerenv")


def check_db_health(use_mock_data: bool) -> str:
    """Checks the database connectivity.

    Returns "mock", "connected", or "disconnected".
    """
    if use_mock_data:
        return "mock"
    try:
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return "connected"
    except Exception as e:
        logger.error(f"Database health check query failed: {e}")
        return "disconnected"


def run_startup_selfchecks(settings) -> dict[str, bool]:
    """Runs a series of self-checks on startup to verify resource accessibility.

    Checks:
      - SQLite database path accessibility/writability
      - Backup directory presence and writability
      - Common writable paths validation (data directory)
    """
    checks = {}
    from app.core.config import API_ROOT
    if len(API_ROOT.parents) >= 2 and API_ROOT.name == "api" and API_ROOT.parent.name == "apps":
        repo_root = API_ROOT.parents[1]
    else:
        repo_root = API_ROOT

    # 1. SQLite writability
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        sqlite_path = db_url.removeprefix("sqlite:///")
        if ":memory:" in sqlite_path:
            checks["sqlite_writable"] = True
        else:
            db_file = Path(sqlite_path)
            try:
                db_file.parent.mkdir(parents=True, exist_ok=True)
                test_file = db_file.parent / ".kairos_write_test"
                test_file.write_text("test")
                test_file.unlink()
                checks["sqlite_writable"] = True
            except Exception as e:
                logger.error(f"Self-check: SQLite path {db_file.parent} not writable: {e}")
                checks["sqlite_writable"] = False
    else:
        # Non-SQLite (e.g. Postgres) assumes writable if configured
        checks["sqlite_writable"] = True

    # 2. Backup directory writability
    backup_dir = repo_root / "backups"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        test_file = backup_dir / ".backup_write_test"
        test_file.write_text("test")
        test_file.unlink()
        checks["backup_directory_writable"] = True
    except Exception as e:
        logger.error(f"Self-check: backup directory {backup_dir} not writable: {e}")
        checks["backup_directory_writable"] = False

    # 3. Data directory writability
    data_dir = repo_root / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        test_file = data_dir / ".data_write_test"
        test_file.write_text("test")
        test_file.unlink()
        checks["data_directory_writable"] = True
    except Exception as e:
        logger.error(f"Self-check: data directory {data_dir} not writable: {e}")
        checks["data_directory_writable"] = False

    return checks


class RequestMetrics:
    """Tracks HTTP request statistics in-memory."""
    def __init__(self):
        self.total_requests = 0
        self.status_codes = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}

    def clear(self):
        self.total_requests = 0
        self.status_codes = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}


metrics_tracker = RequestMetrics()
