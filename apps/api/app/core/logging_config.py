import logging
import sys
import time


def setup_logging() -> None:
    """Configures the standard Python root logger and aligns Uvicorn loggers

    to propagate records with a consistent UTC ISO format.
    """
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    formatter.converter = time.gmtime

    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Disable default handlers for Uvicorn and propagate log events to the root logger
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(logger_name)
        u_logger.handlers = []
        u_logger.propagate = True
