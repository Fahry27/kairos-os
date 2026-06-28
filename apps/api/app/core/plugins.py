import logging
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CommandManifest(BaseModel):
    id: str
    plugin_id: str
    name: str
    description: str
    category: str
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    enabled: bool = True
    dangerous: bool = False
    metadata: dict = Field(default_factory=dict)


class PluginManifest(BaseModel):
    id: str
    name: str
    version: str
    description: str
    category: str
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)
    entry_type: str = "builtin"
    entry_ref: str
    permissions: list[str] = Field(default_factory=list)
    config_schema: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    commands: list[CommandManifest] = Field(default_factory=list)


BUILTIN_PLUGINS: dict[str, PluginManifest] = {
    "core.projects": PluginManifest(
        id="core.projects",
        name="Core Projects Extension",
        version="1.8.0",
        description="Core project management capabilities including project tracking and progress analysis.",
        category="core",
        enabled=True,
        capabilities=["project_management", "analytics"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.projects",
        permissions=["read:projects", "write:projects"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
        commands=[
            CommandManifest(
                id="core.projects.create_project",
                plugin_id="core.projects",
                name="Create Project",
                description="Create a new workspace project within the local system store.",
                category="write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    },
                    "required": ["name"],
                },
                output_schema={"type": "object"},
                permissions=["write:projects"],
            ),
            CommandManifest(
                id="core.projects.list_projects",
                plugin_id="core.projects",
                name="List Projects",
                description="List existing projects matching filter conditions.",
                category="read",
                input_schema={},
                output_schema={"type": "array"},
                permissions=["read:projects"],
            ),
        ],
    ),
    "core.tasks": PluginManifest(
        id="core.tasks",
        name="Core Tasks Extension",
        version="1.8.0",
        description="Core task management capabilities supporting subtasks, priorities, and status transitions.",
        category="core",
        enabled=True,
        capabilities=["task_management"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.tasks",
        permissions=["read:tasks", "write:tasks"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
        commands=[
            CommandManifest(
                id="core.tasks.create_task",
                plugin_id="core.tasks",
                name="Create Task",
                description="Create a new task under a project or category.",
                category="write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "project_id": {"type": "string"},
                    },
                    "required": ["title"],
                },
                output_schema={"type": "object"},
                permissions=["write:tasks"],
            ),
            CommandManifest(
                id="core.tasks.list_tasks",
                plugin_id="core.tasks",
                name="List Tasks",
                description="Retrieve all registered tasks with filtering tags.",
                category="read",
                input_schema={},
                output_schema={"type": "array"},
                permissions=["read:tasks"],
            ),
        ],
    ),
    "core.memories": PluginManifest(
        id="core.memories",
        name="Core Memories Extension",
        version="1.8.0",
        description="Core context memory store supporting semantic search references and system notes.",
        category="core",
        enabled=True,
        capabilities=["knowledge_base", "semantic_reference"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.memories",
        permissions=["read:memories", "write:memories"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
        commands=[
            CommandManifest(
                id="core.memories.create_memory",
                plugin_id="core.memories",
                name="Create Memory",
                description="Add notes or semantic memories linked to active projects.",
                category="write",
                input_schema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "project_id": {"type": "string"},
                    },
                    "required": ["content"],
                },
                output_schema={"type": "object"},
                permissions=["write:memories"],
            ),
            CommandManifest(
                id="core.memories.search_memories",
                plugin_id="core.memories",
                name="Search Memories",
                description="Query stored context memories using search parameters.",
                category="read",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "array"},
                permissions=["read:memories"],
            ),
        ],
    ),
    "core.operations": PluginManifest(
        id="core.operations",
        name="Core Operations Extension",
        version="1.8.0",
        description="Production operations metrics, readiness checks, self-checks, and telemetry auditing.",
        category="core",
        enabled=True,
        capabilities=["monitoring", "telemetry"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.health",
        permissions=["read:metrics", "read:ready"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
        commands=[
            CommandManifest(
                id="core.operations.run_backup",
                plugin_id="core.operations",
                name="Run Database Backup",
                description="Manually trigger an automated timestamped backup copy of the SQLite database. [RESTRICTED]",
                category="admin",
                input_schema={},
                output_schema={"type": "object"},
                permissions=["admin:backup"],
                dangerous=True,
            ),
            CommandManifest(
                id="core.operations.get_health",
                plugin_id="core.operations",
                name="Get System Health",
                description="Fetch API status and SQLite engine availability indicators.",
                category="read",
                input_schema={},
                output_schema={"type": "object"},
                permissions=["read:health"],
            ),
            CommandManifest(
                id="core.operations.get_metrics",
                plugin_id="core.operations",
                name="Get System Metrics",
                description="Fetch request count distributions, uptime, and Docker mode environment metrics.",
                category="read",
                input_schema={},
                output_schema={"type": "object"},
                permissions=["read:metrics"],
            ),
        ],
    ),
}


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginManifest] = dict(BUILTIN_PLUGINS)

    def get_plugin(self, plugin_id: str) -> PluginManifest | None:
        return self._plugins.get(plugin_id)

    def get_all_plugins(self, include_disabled: bool = False) -> list[PluginManifest]:
        if include_disabled:
            return list(self._plugins.values())
        return [p for p in self._plugins.values() if p.enabled]

    def load_external_plugins(self, plugins_dir: Path):
        """Scans plugins_dir for custom .json manifest files.

        Validates against PluginManifest. Conflicting or duplicate IDs are skipped.
        """
        # Reset to built-ins on reload to ensure clean states
        self._plugins = dict(BUILTIN_PLUGINS)

        if not plugins_dir.exists():
            try:
                plugins_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created plugins directory: {plugins_dir}")
            except Exception as e:
                logger.error(f"Failed to create plugins directory {plugins_dir}: {e}")
                return

        # Scan folder for .json manifest files
        for p_file in plugins_dir.glob("*.json"):
            try:
                content = p_file.read_text(encoding="utf-8")
                manifest = PluginManifest.model_validate_json(content)
                manifest.entry_type = "external"

                # Reject duplicate built-in IDs
                if manifest.id in BUILTIN_PLUGINS:
                    logger.warning(
                        f"Skip loading external plugin '{manifest.id}' from {p_file.name}: "
                        "ID conflicts with built-in capability."
                    )
                    continue

                # Reject duplicate custom IDs
                if manifest.id in self._plugins:
                    logger.warning(
                        f"Skip loading external plugin '{manifest.id}' from {p_file.name}: "
                        "Duplicate plugin ID already registered."
                    )
                    continue

                # Enforce command mapping logic
                for cmd in manifest.commands:
                    cmd.plugin_id = manifest.id

                self._plugins[manifest.id] = manifest
                logger.info(f"Loaded external plugin manifest: {manifest.id} ({manifest.name})")
            except Exception as e:
                logger.warning(f"Failed to load plugin manifest from {p_file.name}: {e}")


plugin_registry = PluginRegistry()
