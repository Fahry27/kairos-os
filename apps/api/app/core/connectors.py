import logging
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConnectorManifest(BaseModel):
    id: str
    name: str
    version: str
    description: str
    category: str
    enabled: bool = True
    service_type: str
    base_url: str | None = None
    auth_type: str
    capabilities: list[str] = Field(default_factory=list)
    health_endpoint: str | None = None
    docs_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


BUILTIN_CONNECTORS: dict[str, ConnectorManifest] = {
    "connector.ollama": ConnectorManifest(
        id="connector.ollama",
        name="Ollama LLM Engine",
        version="1.9.0",
        description="Local large language model server serving deep learning weights.",
        category="ai",
        enabled=True,
        service_type="ai_inference",
        base_url="http://localhost:11434",
        auth_type="none",
        capabilities=["text_generation", "embeddings"],
        health_endpoint="/api/tags",
        docs_url="https://github.com/ollama/ollama",
        tags=["ai", "llm", "local"],
        metadata={"author": "Ollama Authors", "tier": "system"},
    ),
    "connector.open_webui": ConnectorManifest(
        id="connector.open_webui",
        name="Open WebUI Dashboard",
        version="1.9.0",
        description="User interface for chatting with local LLMs and agentic networks.",
        category="ui",
        enabled=True,
        service_type="ai_webui",
        base_url="http://localhost:3000",
        auth_type="api_key",
        capabilities=["chat_interface", "multi_user"],
        health_endpoint="/health",
        docs_url="https://openwebui.com",
        tags=["ui", "ai", "dashboard"],
        metadata={"author": "Open WebUI Team", "tier": "system"},
    ),
    "connector.n8n": ConnectorManifest(
        id="connector.n8n",
        name="n8n Workflow Automation",
        version="1.9.0",
        description="Fair-code workflow automation tool to connect homelab events.",
        category="automation",
        enabled=True,
        service_type="workflow_engine",
        base_url="http://localhost:5678",
        auth_type="basic_auth",
        capabilities=["trigger_webhooks", "data_mapping"],
        health_endpoint="/healthz",
        docs_url="https://docs.n8n.io",
        tags=["automation", "workflows"],
        metadata={"author": "n8n.io", "tier": "system"},
    ),
    "connector.tailscale": ConnectorManifest(
        id="connector.tailscale",
        name="Tailscale Mesh VPN",
        version="1.9.0",
        description="Zero config mesh VPN client connecting homelabs securely.",
        category="networking",
        enabled=True,
        service_type="vpn_mesh",
        base_url="https://admin.tailscale.com",
        auth_type="oauth2",
        capabilities=["mesh_routing", "remote_access"],
        health_endpoint=None,
        docs_url="https://tailscale.com/kb",
        tags=["network", "security", "vpn"],
        metadata={"author": "Tailscale Inc.", "tier": "system"},
    ),
    "connector.uptime_kuma": ConnectorManifest(
        id="connector.uptime_kuma",
        name="Uptime Kuma Monitor",
        version="1.9.0",
        description="Self-hosted monitoring tool checking website, port, and ping connectivity states.",
        category="monitoring",
        enabled=True,
        service_type="status_page",
        base_url="http://localhost:3001",
        auth_type="none",
        capabilities=["pings", "incident_notifications"],
        health_endpoint="/status",
        docs_url="https://github.com/louislam/uptime-kuma",
        tags=["monitoring", "status"],
        metadata={"author": "Louis Lam", "tier": "system"},
    ),
    "connector.portainer": ConnectorManifest(
        id="connector.portainer",
        name="Portainer Orchestrator",
        version="1.9.0",
        description="Container management platform checking local stacks and images.",
        category="orchestration",
        enabled=True,
        service_type="docker_management",
        base_url="http://localhost:9000",
        auth_type="jwt_token",
        capabilities=["container_control", "stats_read"],
        health_endpoint="/api/system/status",
        docs_url="https://docs.portainer.io",
        tags=["orchestration", "docker"],
        metadata={"author": "Portainer.io", "tier": "system"},
    ),
    "connector.deepseek_ocr": ConnectorManifest(
        id="connector.deepseek_ocr",
        name="DeepSeek Vision OCR",
        version="1.9.0",
        description="Vision model pipeline extracting structured OCR text blocks.",
        category="vision",
        enabled=True,
        service_type="ocr_engine",
        base_url="http://localhost:8080",
        auth_type="api_key",
        capabilities=["ocr_parse", "image_processing"],
        health_endpoint="/health",
        docs_url="https://github.com/deepseek-ai",
        tags=["vision", "ocr", "ai"],
        metadata={"author": "DeepSeek Team", "tier": "system"},
    ),
    "connector.openclaw": ConnectorManifest(
        id="connector.openclaw",
        name="OpenClaw Simulator",
        version="1.9.0",
        description="Claw simulation testing framework for local automated grab actions.",
        category="gaming",
        enabled=True,
        service_type="claw_simulation",
        base_url="http://localhost:8090",
        auth_type="none",
        capabilities=["simulation_run", "gameplay"],
        health_endpoint="/api/health",
        docs_url="https://github.com/openclaw",
        tags=["gaming", "simulation"],
        metadata={"author": "OpenClaw Team", "tier": "system"},
    ),
    "connector.plex": ConnectorManifest(
        id="connector.plex",
        name="Plex Media Server",
        version="1.9.0",
        description="Personal media library server aggregating movies, shows, and music.",
        category="media",
        enabled=True,
        service_type="media_server",
        base_url="http://localhost:32400",
        auth_type="plex_token",
        capabilities=["media_transcoding", "library_indexing"],
        health_endpoint="/identity",
        docs_url="https://support.plex.tv",
        tags=["media", "streaming"],
        metadata={"author": "Plex Inc.", "tier": "system"},
    ),
}


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, ConnectorManifest] = dict(BUILTIN_CONNECTORS)

    def get_connector(self, connector_id: str) -> ConnectorManifest | None:
        return self._connectors.get(connector_id)

    def get_all_connectors(self, include_disabled: bool = False) -> list[ConnectorManifest]:
        if include_disabled:
            return list(self._connectors.values())
        return [c for c in self._connectors.values() if c.enabled]

    def load_external_connectors(self, connectors_dir: Path):
        """Scans connectors_dir for custom .json manifest files.

        Validates against ConnectorManifest. Conflicting or duplicate IDs are skipped.
        """
        self._connectors = dict(BUILTIN_CONNECTORS)

        if not connectors_dir.exists():
            try:
                connectors_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created connectors directory: {connectors_dir}")
            except Exception as e:
                logger.error(f"Failed to create connectors directory {connectors_dir}: {e}")
                return

        for c_file in connectors_dir.glob("*.json"):
            try:
                content = c_file.read_text(encoding="utf-8")
                manifest = ConnectorManifest.model_validate_json(content)

                if manifest.id in BUILTIN_CONNECTORS:
                    logger.warning(
                        f"Skip loading external connector '{manifest.id}' from {c_file.name}: "
                        "ID conflicts with built-in service definition."
                    )
                    continue

                if manifest.id in self._connectors:
                    logger.warning(
                        f"Skip loading external connector '{manifest.id}' from {c_file.name}: "
                        "Duplicate connector ID already registered."
                    )
                    continue

                self._connectors[manifest.id] = manifest
                logger.info(f"Loaded external connector manifest: {manifest.id} ({manifest.name})")
            except Exception as e:
                logger.warning(f"Failed to load connector manifest from {c_file.name}: {e}")


connector_registry = ConnectorRegistry()
