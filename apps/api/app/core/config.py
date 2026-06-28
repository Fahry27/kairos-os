from functools import lru_cache
import json
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]

if len(API_ROOT.parents) >= 2 and API_ROOT.name == "api" and API_ROOT.parent.name == "apps":
    REPO_ROOT = API_ROOT.parents[1]
    LOCAL_SQLITE_PATH = REPO_ROOT / "data" / "kairos-local.sqlite3"
else:
    LOCAL_SQLITE_PATH = API_ROOT / "data" / "kairos-local.sqlite3"


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
    app_version: str = Field(default="1.4.0", validation_alias="APP_VERSION")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    kairos_api_key: str | None = Field(default=None, validation_alias="KAIROS_API_KEY")
    database_url: str = Field(
        default=f"sqlite:///{LOCAL_SQLITE_PATH}",
        validation_alias="DATABASE_URL",
    )
    create_tables_on_startup: bool = Field(
        default=True,
        validation_alias="CREATE_TABLES_ON_STARTUP",
    )
    use_mock_data: bool = Field(
        default=False,
        validation_alias="USE_MOCK_DATA",
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
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
