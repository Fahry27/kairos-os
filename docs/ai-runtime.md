# AI Runtime Interface

Kairos OS v2.5.0
================

Kairos OS currently ships with a **metadata-only AI Runtime**. 

> **Important**: In version 2.5.0, the AI Runtime supports local dispatch and response parsing.
> - **No commands are executed.**
> - **No connectors are called.**
> - **No data is mutated.**
> - The prompt package is built deterministically based on registry metadata and context limits.
> - The response parser operates entirely in-memory and never persists raw LLM text.

## Prompt Dry-Run, Local Dispatch & Response Parser

The `POST /api/v1/ai/prompt/dry-run` endpoint deterministically assembles a prompt package.
The `POST /api/v1/ai/ollama/dispatch` endpoint (disabled by default) dispatches the prompt to local Ollama.
The `POST /api/v1/ai/parse-plan` endpoint (v2.5.0) converts raw LLM text into structured planning output without calling any network. 

This contract enforces:
1. Max context limits for commands, plugins, and connectors.
2. Complete omission of secrets, credentials, tokens, and raw environment values.
3. System instructions emphasizing read-only operation and explicit human approval for execution.

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

1. **Safe Readiness, Discovery, Dispatch & Parsing** — Network calls are limited to local Ollama paths (`/api/tags`, `/api/generate`). The response parser makes zero network calls.
2. **No secrets stored or returned** — Provider manifests carry `auth_type` metadata only. No API keys, tokens, or passwords are ever stored or returned.
3. **Hard-gated execution** — The planner response always contains `execution_enabled=false` regardless of the `KAIROS_AI_EXECUTION_ENABLED` environment setting. This flag is a forward-looking placeholder only.
4. **API key authentication** — All `/api/v1/ai/*` endpoints require `X-Kairos-API-Key` when `KAIROS_API_KEY` is configured.
5. **Dangerous command surfacing** — Commands marked `dangerous=true` (e.g. `core.operations.run_backup`) are clearly flagged in planning and parser responses.
6. **No persistence of raw LLM text** — The parser processes LLM responses in-memory only. Raw text is never written to the database, filesystem, or application logs.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KAIROS_AI_ENABLED` | `true` | Master switch. Set `false` to disable all AI endpoints. |
| `KAIROS_AI_PROVIDER` | `ollama` | Active provider identifier. Used in capability summary. |
| `KAIROS_AI_MODEL` | *(empty)* | Model name to display (e.g. `llama3.2`). Not used to call any API. |
| `KAIROS_AI_BASE_URL` | *(empty)* | Provider base URL override. Not used to make calls in v2.1. |
| `KAIROS_AI_PLANNING_ENABLED` | `true` | Enables the `POST /api/v1/ai/plan` endpoint. |
| `KAIROS_AI_EXECUTION_ENABLED` | `false` | Reserved for future milestone. **Planner ignores this and always returns `false`**. |
| `KAIROS_OLLAMA_READINESS_ENABLED` | `true` | Enables the safe Ollama readiness and model discovery checks. |
| `KAIROS_OLLAMA_BASE_URL` | `http://localhost:11434` | Base URL used specifically for the Ollama readiness check. |
| `KAIROS_OLLAMA_TAGS_PATH` | `/api/tags` | Path used to check Ollama model availability safely. |
| `KAIROS_OLLAMA_TIMEOUT_SECONDS` | `2` | Short timeout for the readiness check. |
| `KAIROS_OLLAMA_DISPATCH_ENABLED` | `false` | Enables manual local prompt dispatch to Ollama (v2.4.0). |
| `KAIROS_OLLAMA_GENERATE_PATH` | `/api/generate` | Path used to generate responses safely without execution. |
| `KAIROS_OLLAMA_REQUEST_TIMEOUT_SECONDS` | `30` | Timeout for the dispatch generate call. |
| `KAIROS_OLLAMA_MAX_PROMPT_CHARS` | `12000` | Max characters allowed for the compiled dispatch prompt string. |
| `KAIROS_OLLAMA_MAX_RESPONSE_CHARS` | `8000` | Max characters allowed for the generated model response. |
| `KAIROS_AI_RESPONSE_PARSER_ENABLED` | `true` | Enables the LLM response parser (v2.5.0). |
| `KAIROS_AI_MAX_PARSED_STEPS` | `10` | Max plan steps the parser will extract. |
| `KAIROS_AI_MAX_PARSED_COMMANDS` | `10` | Max command suggestions the parser will extract. |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/ai` | High-level AI runtime status |
| `GET` | `/api/v1/ai/providers` | List enabled AI provider manifests |
| `GET` | `/api/v1/ai/providers/{provider_id}` | Single provider detail |
| `GET` | `/api/v1/ai/providers/{provider_id}/readiness` | Single provider readiness check |
| `GET` | `/api/v1/ai/providers/{provider_id}/models` | Single provider model discovery |
| `GET` | `/api/v1/ai/readiness` | Current provider readiness check |
| `GET` | `/api/v1/ai/models` | Current provider model discovery |
| `GET` | `/api/v1/ai/capabilities` | Full runtime capability summary including discovery |
| `POST` | `/api/v1/ai/plan` | Generate a deterministic advisory plan |
| `POST` | `/api/v1/ai/prompt/dry-run` | Builds a deterministic prompt payload for future LLM execution without sending it |
| `POST` | `/api/v1/ai/ollama/dispatch` | Safely dispatch a compiled prompt to local Ollama (no execution) |
| `POST` | `/api/v1/ai/parse-plan` | Parse raw LLM text into a structured plan (no network, no execution) |

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
| **v2.0** | Metadata-only AI Runtime Interface. Deterministic planner. No LLM calls. |
| **v2.1** | Ollama connectivity self-check (health probe only, no inference). |
| **v2.2** *(current)* | Ollama Model Discovery — enumerate local models via `/api/tags` safely. |
| **v2.3** | Local LLM planning — route `POST /ai/plan` through Ollama for natural language goal understanding. |
| **v3.0** | Agent loop — Kairos autonomously plans, executes, and observes via plugin + connector pipelines. |
