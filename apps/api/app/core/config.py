from functools import lru_cache
import json
from pathlib import Path

from pydantic import Field, model_validator
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
    app_version: str = Field(default="2.5.0", validation_alias="APP_VERSION")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    root_path: str = Field(default="", validation_alias="ROOT_PATH")
    kairos_api_key: str | None = Field(default=None, validation_alias="KAIROS_API_KEY")
    kairos_plugins_enabled: bool = Field(default=True, validation_alias="KAIROS_PLUGINS_ENABLED")
    kairos_plugins_dir: str = Field(default="", validation_alias="KAIROS_PLUGINS_DIR")
    kairos_connectors_enabled: bool = Field(default=True, validation_alias="KAIROS_CONNECTORS_ENABLED")
    kairos_connectors_dir: str = Field(default="", validation_alias="KAIROS_CONNECTORS_DIR")
    # AI Runtime settings (v2.2.0)
    kairos_ai_enabled: bool = Field(default=True, validation_alias="KAIROS_AI_ENABLED")
    kairos_ai_provider: str = Field(default="ollama", validation_alias="KAIROS_AI_PROVIDER")
    kairos_ai_model: str = Field(default="", validation_alias="KAIROS_AI_MODEL")
    kairos_ai_base_url: str = Field(default="", validation_alias="KAIROS_AI_BASE_URL")
    kairos_ai_planning_enabled: bool = Field(default=True, validation_alias="KAIROS_AI_PLANNING_ENABLED")
    # execution_enabled defaults False; the planner hard-gates this regardless of config
    kairos_ai_execution_enabled: bool = Field(default=False, validation_alias="KAIROS_AI_EXECUTION_ENABLED")
    
    # Prompt Dry-Run (v2.3.0)
    kairos_ai_dry_run_enabled: bool = Field(default=True, validation_alias="KAIROS_AI_DRY_RUN_ENABLED")
    kairos_ai_max_context_commands: int = Field(default=20, validation_alias="KAIROS_AI_MAX_CONTEXT_COMMANDS")
    kairos_ai_max_context_connectors: int = Field(default=20, validation_alias="KAIROS_AI_MAX_CONTEXT_CONNECTORS")
    kairos_ai_max_context_plugins: int = Field(default=20, validation_alias="KAIROS_AI_MAX_CONTEXT_PLUGINS")
    
    # Ollama Readiness
    kairos_ollama_readiness_enabled: bool = Field(default=True, validation_alias="KAIROS_OLLAMA_READINESS_ENABLED")
    kairos_ollama_base_url: str = Field(default="http://localhost:11434", validation_alias="KAIROS_OLLAMA_BASE_URL")
    kairos_ollama_tags_path: str = Field(default="/api/tags", validation_alias="KAIROS_OLLAMA_TAGS_PATH")
    kairos_ollama_timeout_seconds: int = Field(default=2, validation_alias="KAIROS_OLLAMA_TIMEOUT_SECONDS")
    
    # Ollama Local Dispatch (v2.4.0)
    kairos_ollama_dispatch_enabled: bool = Field(default=False, validation_alias="KAIROS_OLLAMA_DISPATCH_ENABLED")
    kairos_ollama_generate_path: str = Field(default="/api/generate", validation_alias="KAIROS_OLLAMA_GENERATE_PATH")
    kairos_ollama_request_timeout_seconds: int = Field(default=30, validation_alias="KAIROS_OLLAMA_REQUEST_TIMEOUT_SECONDS")
    kairos_ollama_max_prompt_chars: int = Field(default=12000, validation_alias="KAIROS_OLLAMA_MAX_PROMPT_CHARS")
    kairos_ollama_max_response_chars: int = Field(default=8000, validation_alias="KAIROS_OLLAMA_MAX_RESPONSE_CHARS")
    
    # Response Parser (v2.5.0)
    kairos_ai_response_parser_enabled: bool = Field(default=True, validation_alias="KAIROS_AI_RESPONSE_PARSER_ENABLED")
    kairos_ai_max_parsed_steps: int = Field(default=10, validation_alias="KAIROS_AI_MAX_PARSED_STEPS")
    kairos_ai_max_parsed_commands: int = Field(default=10, validation_alias="KAIROS_AI_MAX_PARSED_COMMANDS")
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

    @property
    def resolved_plugins_dir(self) -> Path:
        if self.kairos_plugins_dir:
            return Path(self.kairos_plugins_dir)
        if len(API_ROOT.parents) >= 2 and API_ROOT.name == "api" and API_ROOT.parent.name == "apps":
            return API_ROOT.parents[1] / "data" / "plugins"
        return API_ROOT / "data" / "plugins"

    @property
    def resolved_connectors_dir(self) -> Path:
        if self.kairos_connectors_dir:
            return Path(self.kairos_connectors_dir)
        if len(API_ROOT.parents) >= 2 and API_ROOT.name == "api" and API_ROOT.parent.name == "apps":
            return API_ROOT.parents[1] / "data" / "connectors"
        return API_ROOT / "data" / "connectors"

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        # 1. Validate APP_ENV
        if self.app_env not in ("development", "production", "test"):
            raise ValueError(
                f"Invalid APP_ENV: {self.app_env}. Must be one of: development, production, test."
            )

        # 2. Validate DATABASE_URL scheme
        if not (self.database_url.startswith("sqlite://") or self.database_url.startswith("postgresql")):
            raise ValueError(
                f"Invalid DATABASE_URL scheme: {self.database_url}. Must be SQLite or PostgreSQL."
            )

        # 3. Validate ROOT_PATH
        if self.root_path:
            if not self.root_path.startswith("/"):
                raise ValueError("ROOT_PATH must start with '/'")
            if self.root_path.endswith("/") and self.root_path != "/":
                raise ValueError("ROOT_PATH must not have a trailing slash except '/'")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

