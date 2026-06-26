from functools import lru_cache
import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]


def resolve_env_file() -> Path:
    for parent in (API_ROOT, *API_ROOT.parents):
        if (parent / ".env").exists() or (parent / ".env.example").exists():
            return parent / ".env"
    return API_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="kairos-api", validation_alias="APP_NAME")
    app_version: str = Field(default="0.1.0", validation_alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    database_url: str = Field(
        default="postgresql+psycopg://kairos:kairos_dev_password@localhost:5432/kairos",
        validation_alias="DATABASE_URL",
    )
    create_tables_on_startup: bool = Field(
        default=True,
        validation_alias="CREATE_TABLES_ON_STARTUP",
    )
    cors_origins: str = Field(
        default="",
        validation_alias="CORS_ORIGINS",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip().startswith("["):
            parsed = json.loads(self.cors_origins)
            return [str(origin).strip() for origin in parsed if str(origin).strip()]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
