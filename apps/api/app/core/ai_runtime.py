"""
Kairos AI Runtime — metadata-only AI provider registry, capability summary, and
deterministic rule-based planner.

SAFETY CONTRACT (v2.0.0):
  - No outbound network calls are made anywhere in this module.
  - No LLM APIs are invoked.
  - No credentials, tokens, or secrets are stored or returned.
  - The planner response always carries execution_enabled=false regardless of
    the KAIROS_AI_EXECUTION_ENABLED configuration setting. That flag is a
    forward-looking placeholder for a future milestone.
  - OpenClaw remains a ConnectorManifest (connector registry) — it is not
    touched here and is not an OAuth bridge.
"""

import logging
import json
import time
import urllib.request
import urllib.error
from urllib.parse import urljoin
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class AIProviderManifest(BaseModel):
    id: str
    name: str
    provider_type: str  # e.g. "local", "cloud", "router"
    enabled: bool = True
    base_url: str | None = None
    default_model: str | None = None
    supports_chat: bool = False
    supports_tools: bool = False
    supports_embeddings: bool = False
    supports_vision: bool = False
    supports_local: bool = False
    auth_type: str = "none"  # none | api_key | oauth2
    metadata: dict = Field(default_factory=dict)


class AIProviderReadiness(BaseModel):
    provider_id: str
    reachable: bool | None = None
    checked: bool = False
    base_url_configured: str | None = None
    latency_ms: int | None = None
    model_count: int | None = None
    error_type: str | None = None
    message: str | None = None


class AICapabilities(BaseModel):
    ai_enabled: bool
    provider: str
    model: str | None
    planning_enabled: bool
    # execution_enabled is always False in v2.0 — hard-gated at the planner level
    execution_enabled: bool = False
    available_plugins: int
    available_commands: int
    available_connectors: int
    dangerous_commands: int
    
    # Readiness fields (added in v2.1.0)
    provider_reachable: bool | None = None
    provider_checked: bool = False
    provider_readiness_message: str | None = None


class PlannedCommand(BaseModel):
    command_id: str
    command_name: str
    description: str
    category: str
    # Safety fields — always set by the planner; never overridden by config
    execution_required: bool = False
    requires_approval: bool = True
    dangerous: bool = False


class PlanStep(BaseModel):
    step: int
    action: str
    rationale: str
    commands: list[PlannedCommand] = Field(default_factory=list)


class PlanResponse(BaseModel):
    goal: str
    summary: str
    available_context: dict
    suggested_steps: list[PlanStep]
    suggested_commands: list[PlannedCommand]
    safety_notes: list[str]
    # Hard-gated: planner always emits False regardless of KAIROS_AI_EXECUTION_ENABLED
    execution_enabled: bool = False
    requires_approval: bool = True


# ---------------------------------------------------------------------------
# Built-in AI provider manifests
# ---------------------------------------------------------------------------

BUILTIN_AI_PROVIDERS: dict[str, AIProviderManifest] = {
    "ai.ollama": AIProviderManifest(
        id="ai.ollama",
        name="Ollama (Local LLM Engine)",
        provider_type="local",
        enabled=True,
        base_url="http://localhost:11434",
        default_model="",  # user-configurable via KAIROS_AI_MODEL
        supports_chat=True,
        supports_tools=True,
        supports_embeddings=True,
        supports_vision=True,
        supports_local=True,
        auth_type="none",
        metadata={
            "tier": "primary",
            "note": "Primary local-first LLM engine. Not called in v2.0 — metadata only.",
            "docs": "https://github.com/ollama/ollama",
        },
    ),
    # --- Optional disabled metadata stubs ---
    # User has Codex access. No OAuth, no token storage, no API calls, no code execution.
    "ai.openai_codex": AIProviderManifest(
        id="ai.openai_codex",
        name="OpenAI Codex (Code Generation)",
        provider_type="cloud",
        enabled=False,
        base_url=None,
        default_model="code-davinci-002",
        supports_chat=False,
        supports_tools=True,
        supports_embeddings=False,
        supports_vision=False,
        supports_local=False,
        auth_type="api_key",
        metadata={
            "tier": "optional",
            "note": (
                "User has Codex access. Disabled in v2.0. "
                "No OAuth, no token storage, no API calls, no coding execution implemented."
            ),
            "docs": "https://platform.openai.com/docs/models/codex",
        },
    ),
    "ai.openai": AIProviderManifest(
        id="ai.openai",
        name="OpenAI (GPT)",
        provider_type="cloud",
        enabled=False,
        base_url=None,
        default_model="gpt-4o",
        supports_chat=True,
        supports_tools=True,
        supports_embeddings=True,
        supports_vision=True,
        supports_local=False,
        auth_type="api_key",
        metadata={
            "tier": "optional",
            "note": "Disabled in v2.0. No token storage or API calls implemented.",
            "docs": "https://platform.openai.com/docs",
        },
    ),
    "ai.openrouter": AIProviderManifest(
        id="ai.openrouter",
        name="OpenRouter (Multi-Model Router)",
        provider_type="router",
        enabled=False,
        base_url="https://openrouter.ai/api/v1",
        default_model=None,
        supports_chat=True,
        supports_tools=True,
        supports_embeddings=False,
        supports_vision=False,
        supports_local=False,
        auth_type="api_key",
        metadata={
            "tier": "optional",
            "note": "Disabled in v2.0. No token storage or API calls implemented.",
            "docs": "https://openrouter.ai/docs",
        },
    ),
}


# ---------------------------------------------------------------------------
# Keyword → command category mapping for the deterministic planner
# ---------------------------------------------------------------------------

_GOAL_KEYWORD_MAP: dict[str, list[str]] = {
    "project": ["core.projects.create_project", "core.projects.list_projects"],
    "task": ["core.tasks.create_task", "core.tasks.list_tasks"],
    "memory": ["core.memories.create_memory", "core.memories.search_memories"],
    "remember": ["core.memories.create_memory", "core.memories.search_memories"],
    "note": ["core.memories.create_memory"],
    "search": ["core.memories.search_memories"],
    "backup": ["core.operations.run_backup"],
    "health": ["core.operations.get_health"],
    "metric": ["core.operations.get_metrics"],
    "status": ["core.operations.get_health"],
    "monitor": ["core.operations.get_health", "core.operations.get_metrics"],
}

_SAFETY_NOTES_BASE = [
    "All suggested commands require human approval before execution.",
    "Command execution is disabled in v2.0 — this plan is advisory only.",
    "No LLM was consulted to produce this plan. Suggestions are rule-based metadata matching.",
    "Dangerous commands (e.g. backups, admin actions) are clearly flagged and require explicit confirmation.",
]


# ---------------------------------------------------------------------------
# AIRuntime
# ---------------------------------------------------------------------------


class AIRuntime:
    """Metadata-only AI runtime for Kairos v2.0.

    Safety guarantees:
      - No network calls.
      - No LLM invocations.
      - No credentials stored or returned.
      - Planner hard-gates execution_enabled=False in every response.
    """

    def __init__(self):
        self._providers: dict[str, AIProviderManifest] = dict(BUILTIN_AI_PROVIDERS)

    def initialize(self, settings) -> None:
        """Called once on FastAPI lifespan startup. Logs AI runtime state."""
        if settings.kairos_ai_enabled:
            logger.info(
                f"AI Runtime enabled | provider={settings.kairos_ai_provider} "
                f"| model={settings.kairos_ai_model or '(not configured)'} "
                f"| planning={settings.kairos_ai_planning_enabled} "
                f"| execution={settings.kairos_ai_execution_enabled} "
                "(hard-gated False in planner)"
            )
        else:
            logger.info("AI Runtime disabled (KAIROS_AI_ENABLED=false)")

    def get_provider(self, provider_id: str) -> AIProviderManifest | None:
        return self._providers.get(provider_id)

    def get_all_providers(self, include_disabled: bool = False) -> list[AIProviderManifest]:
        if include_disabled:
            return list(self._providers.values())
        return [p for p in self._providers.values() if p.enabled]

    def get_capabilities(self, settings, plugin_registry, connector_registry) -> AICapabilities:
        """Produces a runtime capability summary from live registry state.
        In v2.1.0, includes a safe, prompt-free readiness check if enabled and provider is local.
        """
        all_commands = []
        for plugin in plugin_registry.get_all_plugins(include_disabled=False):
            all_commands.extend(plugin.commands)

        dangerous_count = sum(1 for cmd in all_commands if getattr(cmd, "dangerous", False))

        caps = AICapabilities(
            ai_enabled=settings.kairos_ai_enabled,
            provider=settings.kairos_ai_provider,
            model=settings.kairos_ai_model or None,
            planning_enabled=settings.kairos_ai_planning_enabled,
            execution_enabled=False,  # always False in v2.0/v2.1
            available_plugins=len(plugin_registry.get_all_plugins(include_disabled=False)),
            available_commands=len(all_commands),
            available_connectors=len(connector_registry.get_all_connectors(include_disabled=False)),
            dangerous_commands=dangerous_count,
            provider_reachable=None,
            provider_checked=False,
            provider_readiness_message=None,
        )

        if caps.ai_enabled and caps.provider == "ollama":
            readiness = self.check_ollama_readiness(settings)
            caps.provider_checked = readiness.checked
            caps.provider_reachable = readiness.reachable
            caps.provider_readiness_message = readiness.message
            if readiness.model_count is not None and not caps.model:
                caps.provider_readiness_message += f" ({readiness.model_count} models available)"
        elif caps.ai_enabled and caps.provider != "ollama":
            caps.provider_checked = False
            caps.provider_reachable = None
            caps.provider_readiness_message = "Metadata only provider; no readiness check available"

        return caps

    def check_ollama_readiness(self, settings) -> AIProviderReadiness:
        """
        Safe, prompt-free readiness check for Ollama.
        Only calls GET KAIROS_OLLAMA_TAGS_PATH to check if service is up.
        Never sends generate/chat requests. Never executes commands.
        """
        base_url = settings.kairos_ollama_base_url
        tags_path = settings.kairos_ollama_tags_path
        timeout = settings.kairos_ollama_timeout_seconds
        
        if not settings.kairos_ollama_readiness_enabled:
            return AIProviderReadiness(
                provider_id="ai.ollama",
                checked=False,
                reachable=None,
                base_url_configured=base_url,
                message="Readiness check is disabled in configuration.",
            )
            
        url = urljoin(base_url, tags_path)
        
        start_time = time.time()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status != 200:
                    return AIProviderReadiness(
                        provider_id="ai.ollama",
                        checked=True,
                        reachable=False,
                        base_url_configured=base_url,
                        latency_ms=latency_ms,
                        error_type="http_error",
                        message=f"HTTP {response.status}",
                    )
                
                try:
                    data = json.loads(response.read().decode("utf-8"))
                    model_count = len(data.get("models", []))
                    return AIProviderReadiness(
                        provider_id="ai.ollama",
                        checked=True,
                        reachable=True,
                        base_url_configured=base_url,
                        latency_ms=latency_ms,
                        model_count=model_count,
                        message="Ollama is reachable.",
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return AIProviderReadiness(
                        provider_id="ai.ollama",
                        checked=True,
                        reachable=False,
                        base_url_configured=base_url,
                        latency_ms=latency_ms,
                        error_type="parse_error",
                        message="Invalid response format from Ollama.",
                    )
                    
        except urllib.error.URLError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            reason = str(e.reason) if hasattr(e, "reason") else str(e)
            return AIProviderReadiness(
                provider_id="ai.ollama",
                checked=True,
                reachable=False,
                base_url_configured=base_url,
                latency_ms=latency_ms,
                error_type="connection_error",
                message=f"Failed to connect: {reason}",
            )
        except TimeoutError:
            return AIProviderReadiness(
                provider_id="ai.ollama",
                checked=True,
                reachable=False,
                base_url_configured=base_url,
                latency_ms=int((time.time() - start_time) * 1000),
                error_type="timeout",
                message=f"Connection timed out after {timeout}s.",
            )
        except Exception:
            # Catch-all for safety, avoiding exposing raw exceptions
            return AIProviderReadiness(
                provider_id="ai.ollama",
                checked=True,
                reachable=False,
                base_url_configured=base_url,
                latency_ms=int((time.time() - start_time) * 1000),
                error_type="unknown_error",
                message="An unexpected error occurred during readiness check.",
            )

    def generate_plan(
        self,
        user_goal: str,
        context: dict | None,
        settings,
        plugin_registry,
        connector_registry,
    ) -> PlanResponse:
        """Deterministic, rule-based planner.

        - Performs keyword matching against user_goal.
        - Looks up matching CommandManifest entries from the live plugin registry.
        - NEVER calls an LLM, NEVER executes a command, NEVER makes a network call.
        - execution_enabled is ALWAYS False in the response, regardless of config.
        """
        goal_lower = user_goal.lower()

        # Collect all commands from registry for lookup
        command_lookup: dict[str, object] = {}
        for plugin in plugin_registry.get_all_plugins(include_disabled=False):
            for cmd in plugin.commands:
                command_lookup[cmd.id] = cmd

        # Match keywords → command IDs
        matched_command_ids: list[str] = []
        for keyword, cmd_ids in _GOAL_KEYWORD_MAP.items():
            if keyword in goal_lower:
                for cid in cmd_ids:
                    if cid not in matched_command_ids:
                        matched_command_ids.append(cid)

        # Build PlannedCommand list
        planned_commands: list[PlannedCommand] = []
        for cid in matched_command_ids:
            cmd = command_lookup.get(cid)
            if cmd:
                planned_commands.append(
                    PlannedCommand(
                        command_id=cmd.id,
                        command_name=cmd.name,
                        description=cmd.description,
                        category=cmd.category,
                        execution_required=False,  # always False
                        requires_approval=True,
                        dangerous=getattr(cmd, "dangerous", False),
                    )
                )

        # Determine summary
        if planned_commands:
            summary = (
                f"Based on your goal, {len(planned_commands)} relevant system command(s) "
                "were identified from the Kairos registry. Review and approve each before execution."
            )
        else:
            summary = (
                "No specific commands were matched for this goal. "
                "Review available plugins and commands to identify the right operations manually."
            )

        # Build steps
        steps: list[PlanStep] = []
        if planned_commands:
            steps.append(
                PlanStep(
                    step=1,
                    action="Review matched commands",
                    rationale="Verify each suggested command aligns with your intent before approving.",
                    commands=planned_commands,
                )
            )
            steps.append(
                PlanStep(
                    step=2,
                    action="Approve and execute manually",
                    rationale=(
                        "Command execution is disabled in v2.0. "
                        "Use the API directly or wait for a future milestone with execution support."
                    ),
                    commands=[],
                )
            )
        else:
            steps.append(
                PlanStep(
                    step=1,
                    action="Clarify your goal",
                    rationale=(
                        "The system could not match your goal to known commands. "
                        "Try rephrasing using keywords like 'project', 'task', 'memory', 'backup', or 'health'."
                    ),
                    commands=[],
                )
            )

        # Safety notes — add dangerous warning if applicable
        safety_notes = list(_SAFETY_NOTES_BASE)
        if any(pc.dangerous for pc in planned_commands):
            safety_notes.insert(
                0,
                "⚠️ One or more suggested commands are marked DANGEROUS. "
                "These require explicit administrator approval and should not be run automatically.",
            )

        # Build available_context
        all_commands_list = list(command_lookup.values())
        dangerous_count = sum(1 for c in all_commands_list if getattr(c, "dangerous", False))
        available_context = {
            "plugins": len(plugin_registry.get_all_plugins(include_disabled=False)),
            "commands": len(all_commands_list),
            "connectors": len(connector_registry.get_all_connectors(include_disabled=False)),
            "dangerous_commands": dangerous_count,
        }

        return PlanResponse(
            goal=user_goal,
            summary=summary,
            available_context=available_context,
            suggested_steps=steps,
            suggested_commands=planned_commands,
            safety_notes=safety_notes,
            execution_enabled=False,  # hard gate — never True in v2.0
            requires_approval=True,
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

ai_runtime = AIRuntime()
