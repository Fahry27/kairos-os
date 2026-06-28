from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader

from app.core.config import get_settings, Settings
from app.db.session import get_db

api_key_header = APIKeyHeader(name="X-Kairos-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.kairos_api_key:
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-Kairos-API-Key header is missing",
            )
        if api_key != settings.kairos_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Kairos-API-Key",
            )


__all__ = ["get_db", "verify_api_key"]
