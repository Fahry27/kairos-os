from collections.abc import Generator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None
_engine_url: str | None = None


def _create_engine_options(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
            sqlite_path = database_url.removeprefix("sqlite:///")
            Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


def _resolve_database_url() -> str:
    from app.core.config import get_settings
    get_settings.cache_clear()
    return get_settings().database_url


def _build_engine(url: str) -> Engine:
    return create_engine(url, **_create_engine_options(url))


def _build_sessionmaker(eng: Engine) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


def _ensure_resolved() -> tuple[Engine, sessionmaker[Session]]:
    global _engine, _engine_url, _SessionLocal
    current_url = _resolve_database_url()
    if _engine is None or _engine_url != current_url:
        if _engine is not None:
            _engine.dispose()
        _engine = _build_engine(current_url)
        _engine_url = current_url
        _SessionLocal = _build_sessionmaker(_engine)
    eng = _engine
    sl = _SessionLocal
    if sl is None:
        sl = _build_sessionmaker(eng)
        _SessionLocal = sl
    return eng, sl


def get_db() -> Generator[Session, None, None]:
    _, sl = _ensure_resolved()
    db = sl()
    try:
        yield db
    finally:
        db.close()


def reset_engine() -> None:
    """Reset cached engine. Call when DATABASE_URL changes between tests."""
    global _engine, _SessionLocal, _engine_url
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    _engine_url = None


# ---------------------------------------------------------------------------
# Lazy compat accessors — preserve backward compat for callers that import
# engine / SessionLocal as module-level globals without calling reset_engine.
# ---------------------------------------------------------------------------

class _LazyEngineProxy:
    """Proxy that resolves the real engine on every access."""
    def __getattr__(self, name: str):
        eng, _ = _ensure_resolved()
        return getattr(eng, name)
    def __repr__(self) -> str:
        eng, _ = _ensure_resolved()
        return repr(eng)
    def __hash__(self) -> int:
        eng, _ = _ensure_resolved()
        return hash(eng)
    def __eq__(self, other: object) -> bool:
        eng, _ = _ensure_resolved()
        return eng == other


class _LazySessionLocalProxy:
    """Proxy that calls the real sessionmaker on every invocation."""
    def __call__(self, *args, **kwargs):
        _, sl = _ensure_resolved()
        return sl(*args, **kwargs)
    def __getattr__(self, name: str):
        _, sl = _ensure_resolved()
        return getattr(sl, name)


engine: Engine = _LazyEngineProxy()  # type: ignore[assignment]
SessionLocal: sessionmaker[Session] = _LazySessionLocalProxy()  # type: ignore[assignment]
