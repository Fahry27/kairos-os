# AI Runtime Interface

Kairos v2.0.0 introduces the **AI Runtime Interface** — a safe, metadata-only layer that exposes AI provider configurations, capability summaries, and deterministic planning responses.

> **v2.0 is interface-only.** No LLM calls are made. No commands are executed. No external services are contacted. This is a foundation milestone that defines the safety model and API contract before actual AI integration begins.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Kairos AI Runtime              │
│                                             │
│  ┌─────────────┐   ┌────────────────────┐  │
│  │ AI Provider │   │  Capability        │  │
│  │ Registry    │   │  Summary           │  │
│  │ (metadata)  │   │  (live registry)   │  │
│  └─────────────┘   └────────────────────┘  │
│                                             │
│  ┌────────────────────────────────────────┐ │
│  │  Deterministic Planner                 │ │
│  │  (keyword matching → CommandManifest)  │ │
│  │  execution_enabled = FALSE (hard gate) │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
           │                    │
    Plugin Registry      Connector Registry
    (commands)           (external services)
```

### How It Relates to Plugins, Commands, and Connectors

- **Plugins** expose `CommandManifest` entries. The AI planner uses these as its knowledge base of what Kairos *could* do.
- **Commands** are surfaced in planning responses as `suggested_commands`, each flagged `execution_required=false`.
- **Connectors** are counted in the capabilities summary. They describe external services (Ollama, n8n, Plex…) that future AI steps could route to.
- **No plugin code is executed.** No connector is called. The registries are read-only data sources for the planner.

---

## Registered AI Providers

| ID | Name | Type | Enabled | Notes |
|----|------|------|---------|-------|
| `ai.ollama` | Ollama (Local LLM Engine) | `local` | ✅ **true** | Primary local-first provider. Not called in v2.0. |
| `ai.openai_codex` | OpenAI Codex (Code Generation) | `cloud` | ❌ false | User has Codex access. No OAuth, no tokens, no calls. |
| `ai.openai` | OpenAI (GPT) | `cloud` | ❌ false | Metadata stub. No tokens or calls. |
| `ai.openrouter` | OpenRouter (Multi-Model Router) | `router` | ❌ false | Metadata stub. No tokens or calls. |

> **Anthropic is not included** in the provider registry by design.

> **OpenClaw** remains a [`ConnectorManifest`](connectors.md) — it is a metadata-only agent-runtime candidate, not an AI provider or OAuth bridge.

---

## Security Model

1. **No outbound network calls** — `ai_runtime.py` contains zero `httpx`, `requests`, `urllib`, `socket`, or `aiohttp` usage.
2. **No secrets stored or returned** — Provider manifests carry `auth_type` metadata only. No API keys, tokens, or passwords are ever stored or returned.
3. **Hard-gated execution** — The planner response always contains `execution_enabled=false` regardless of the `KAIROS_AI_EXECUTION_ENABLED` environment setting. This flag is a forward-looking placeholder only.
4. **API key authentication** — All `/api/v1/ai/*` endpoints require `X-Kairos-API-Key` when `KAIROS_API_KEY` is configured.
5. **Dangerous command surfacing** — Commands marked `dangerous=true` (e.g. `core.operations.run_backup`) are clearly flagged in planning responses and surfaced with a safety note.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KAIROS_AI_ENABLED` | `true` | Master switch. Set `false` to disable all AI endpoints. |
| `KAIROS_AI_PROVIDER` | `ollama` | Active provider identifier. Used in capability summary. |
| `KAIROS_AI_MODEL` | *(empty)* | Model name to display (e.g. `llama3.2`). Not used to call any API. |
| `KAIROS_AI_BASE_URL` | *(empty)* | Provider base URL override. Not used to make calls in v2.0. |
| `KAIROS_AI_PLANNING_ENABLED` | `true` | Enables the `POST /api/v1/ai/plan` endpoint. |
| `KAIROS_AI_EXECUTION_ENABLED` | `false` | Reserved for future milestone. **Planner ignores this and always returns `false`**. |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/ai` | High-level AI runtime status |
| `GET` | `/api/v1/ai/providers` | List enabled AI provider manifests |
| `GET` | `/api/v1/ai/providers/{provider_id}` | Single provider detail |
| `GET` | `/api/v1/ai/capabilities` | Full runtime capability summary |
| `POST` | `/api/v1/ai/plan` | Generate a deterministic advisory plan |

### Planning Request

```json
POST /api/v1/ai/plan
{
  "user_goal": "I want to back up the database",
  "context": {}
}
```

### Planning Response

```json
{
  "goal": "I want to back up the database",
  "summary": "1 relevant system command identified. Review and approve before execution.",
  "available_context": { "plugins": 4, "commands": 11, "connectors": 9, "dangerous_commands": 1 },
  "suggested_steps": [
    {
      "step": 1,
      "action": "Review matched commands",
      "rationale": "Verify each command aligns with your intent before approving.",
      "commands": [...]
    }
  ],
  "suggested_commands": [
    {
      "command_id": "core.operations.run_backup",
      "command_name": "Run Database Backup",
      "category": "admin",
      "execution_required": false,
      "requires_approval": true,
      "dangerous": true
    }
  ],
  "safety_notes": [
    "⚠️ One or more suggested commands are marked DANGEROUS...",
    "All suggested commands require human approval before execution.",
    "Command execution is disabled in v2.0 — this plan is advisory only.",
    ...
  ],
  "execution_enabled": false,
  "requires_approval": true
}
```

---

## Roadmap

| Milestone | Description |
|-----------|-------------|
| **v2.0** *(current)* | Metadata-only AI Runtime Interface. Deterministic planner. No LLM calls. |
| **v2.1** | Ollama connectivity self-check (health probe only, no inference). |
| **v2.2** | Local LLM planning — route `POST /ai/plan` through Ollama for natural language goal understanding. |
| **v2.3** | Controlled command execution — Ollama-approved steps executed with human confirmation gate. |
| **v3.0** | Agent loop — Kairos autonomously plans, executes, and observes via plugin + connector pipelines. |
