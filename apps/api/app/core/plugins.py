from pydantic import BaseModel, Field


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


BUILTIN_PLUGINS: dict[str, PluginManifest] = {
    "core.projects": PluginManifest(
        id="core.projects",
        name="Core Projects Extension",
        version="1.7.0",
        description="Core project management capabilities including project tracking and progress analysis.",
        category="core",
        enabled=True,
        capabilities=["project_management", "analytics"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.projects",
        permissions=["read:projects", "write:projects"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
    ),
    "core.tasks": PluginManifest(
        id="core.tasks",
        name="Core Tasks Extension",
        version="1.7.0",
        description="Core task management capabilities supporting subtasks, priorities, and status transitions.",
        category="core",
        enabled=True,
        capabilities=["task_management"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.tasks",
        permissions=["read:tasks", "write:tasks"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
    ),
    "core.memories": PluginManifest(
        id="core.memories",
        name="Core Memories Extension",
        version="1.7.0",
        description="Core context memory store supporting semantic search references and system notes.",
        category="core",
        enabled=True,
        capabilities=["knowledge_base", "semantic_reference"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.memories",
        permissions=["read:memories", "write:memories"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
    ),
    "core.operations": PluginManifest(
        id="core.operations",
        name="Core Operations Extension",
        version="1.7.0",
        description="Production operations metrics, readiness checks, self-checks, and telemetry auditing.",
        category="core",
        enabled=True,
        capabilities=["monitoring", "telemetry"],
        entry_type="builtin",
        entry_ref="app.api.v1.endpoints.health",
        permissions=["read:metrics", "read:ready"],
        config_schema={},
        metadata={"author": "Kairos Core Team", "tier": "system"},
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


plugin_registry = PluginRegistry()
