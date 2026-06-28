# Kairos v2.1.0 Release Notes

Welcome to Kairos v2.1.0, introducing the safe **Ollama Provider Readiness Check**.

## Kairos v2.1.0
**Date:** June 2026

This release adds a safe, prompt-free readiness check to verify if the configured local Ollama service is reachable.

### Features
- **Ollama Readiness Check**: Verifies Ollama availability without generating text or executing commands.
- **Configurable Settings**: `KAIROS_OLLAMA_READINESS_ENABLED`, `KAIROS_OLLAMA_BASE_URL`, `KAIROS_OLLAMA_TAGS_PATH`, and `KAIROS_OLLAMA_TIMEOUT_SECONDS` provide full control over the check.
- **Readiness Endpoints**: `/api/v1/ai/providers/{provider_id}/readiness` and `/api/v1/ai/readiness`.
- **Capability Integration**: `GET /api/v1/ai/capabilities` now returns `provider_reachable`, `provider_checked`, and `provider_readiness_message` fields.
- **Dashboard UI Update**: The AI Runtime card displays the Ollama readiness status and model count when reachable.
- **Strict Safety**: Safe timeout handling, no raw exceptions exposed, and no LLM generation executed.

---

# Kairos v2.0.0 Release Notes

Welcome to Kairos v2.0.0, introducing the **AI Runtime Interface** — a safe, metadata-only AI layer with provider registry, capability summaries, and a deterministic planning endpoint.

## Kairos v2.0.0
**Date:** June 2026

This release establishes the full AI runtime API contract and safety model before actual LLM integration begins in a future milestone.

### Features
- **AI Provider Registry**: Built-in `AIProviderManifest` models for `ai.ollama` (enabled, local-first), `ai.openai_codex` (disabled — user has access, no calls implemented), `ai.openai` (disabled), and `ai.openrouter` (disabled). Anthropic is excluded by design.
- **AI Capability Summary**: `GET /api/v1/ai/capabilities` returns live registry counts (plugins, commands, connectors, dangerous commands) alongside AI runtime state.
- **Deterministic Planner**: `POST /api/v1/ai/plan` accepts a `user_goal` and returns a rule-based advisory plan using keyword matching against the live command registry. No LLM is called.
- **Hard-Gated Execution**: The planner always returns `execution_enabled=false` regardless of `KAIROS_AI_EXECUTION_ENABLED`. The config flag is reserved for future milestones.
- **Dangerous Command Surfacing**: Commands marked `dangerous=true` are flagged in planning responses with explicit safety notes.
- **AI Runtime Dashboard Card**: New `AIRuntimeCard` showing enabled status, provider, model, planning state, execution lock, and registry counts.
- **Six New Config Variables**: `KAIROS_AI_ENABLED`, `KAIROS_AI_PROVIDER`, `KAIROS_AI_MODEL`, `KAIROS_AI_BASE_URL`, `KAIROS_AI_PLANNING_ENABLED`, `KAIROS_AI_EXECUTION_ENABLED`.
- **AI Runtime Documentation**: Full architecture, security model, provider table, endpoint reference, and roadmap in `docs/ai-runtime.md`.

### Safety Guarantees
- Zero outbound network calls in `ai_runtime.py`.
- No API keys, tokens, or secrets stored or returned.
- OpenClaw remains a `ConnectorManifest` — not an OAuth bridge.
- All planning responses carry `execution_enabled=false` and `requires_approval=true`.

---

# Kairos v1.9.0 Release Notes

Welcome to Kairos v1.9.0, introducing the metadata-only External Service Connector Registry Foundation.

## Kairos v1.9.0
**Date:** June 2026

This release integrates a safe metadata-only connector registry, mapping external services as discoverable homelab components without initiating direct outbound API networking or credential caching.

### Features
- **Pydantic Connector Registry**: Created `ConnectorManifest` representing coordinates, types, scopes, and pings for local network nodes.
- **Pre-configured Homelab Services**: Added built-in connectors mapping Ollama, Open WebUI, n8n, Tailscale, Uptime Kuma, Portainer, DeepSeek OCR, OpenClaw, and Plex server configurations.
- **Dynamic External Scanning**: Scans `.json` manifests inside `KAIROS_CONNECTORS_DIR` (defaults to `data/connectors/`), initializing the path automatically.
- **Connector API Routers**: Added GET `/api/v1/connectors` and GET `/api/v1/connectors/{connector_id}` query endpoints.
- **Connectors Dashboard Widget**: Added a dedicated scrollable `ConnectorsCard` in the main layout grid showcasing active integrations and categories.
- **Safe Example Profiles**: Created n8n, Ollama, and Uptime Kuma connection reference files under `docs/examples/connectors/`.
- **Registry Documentation**: Authored `docs/connectors.md` to detail separation from plugins, local files configuration, and Zima OS mappings.

---

# Kairos v1.8.0 Release Notes

Welcome to Kairos v1.8.0, introducing the external plugin JSON loading folder scanner and metadata-only Command Registry.

## Kairos v1.8.0
**Date:** June 2026

This release implements dynamic external manifest folder scanning, command capability models, metadata-only command registries, API query endpoints, and extensions dashboard updates.

### Features
- **External Plugin Scanner**: Automatically scans the path defined by `KAIROS_PLUGINS_DIR` (defaults to `data/plugins/`) for custom `.json` extension manifests.
- **Command Registry Manifest**: Introduced `CommandManifest` model containing IDs, input/output schemas, permission tags, categories, and danger warning toggles.
- **Safe Scanning Safeguards**: Skips invalid structures or duplicate external IDs with warning logs, preventing crashes. Built-in system IDs always take precedence.
- **Command REST Routers**: Added GET `/api/v1/commands` and GET `/api/v1/commands/{command_id}` routes matching auth key protections.
- **Visual Dashboard Updates**: Extended the `ExtensionsCard` component to show the sum total of registered commands from active extensions.
- **Sample Local Manifests**: Added `sample-note-plugin.json` and `sample-calendar-plugin.json` under `docs/examples/plugins/` as safe configuration guidelines.

---

# Kairos v1.7.0 Release Notes

Welcome to Kairos v1.7.0, introducing the initial Plugin and Extension Framework Foundation.

## Kairos v1.7.0
**Date:** June 2026

This release integrates a lightweight built-in extension registry, manifest schemas, configuration switches, dynamic endpoints, and visual extensions summary card inside the dashboard.

### Features
- **Plugin Manifest Model**: Defined a lightweight, Pydantic-based plugin manifest schema containing IDs, capabilities, categories, entry points, configuration schemas, permissions, and metadata.
- **Built-in Registry Loader**: Pre-registered existing core capabilities (`core.projects`, `core.tasks`, `core.memories`, `core.operations`) as structured system extensions.
- **Dynamic Registry Endpoints**: Added read-only endpoints GET `/api/v1/plugins` and GET `/api/v1/plugins/{plugin_id}` requiring active API keys when authentication is enabled.
- **Plugins Enable Toggle**: Added the `KAIROS_PLUGINS_ENABLED` environment toggle (defaulting to `true`). If disabled, all plugin endpoints respond with empty listings or clean errors.
- **Dashboard Summary Integration**: Added an OS Registry Extensions count and details card directly in the main layout grid.
- **Plugin Framework Documentation**: Added a dedicated `docs/plugins.md` guide explaining the manifest layout, API usages, and extension roadmap.

---

# Kairos v1.6.0 Release Notes

Welcome to Kairos v1.6.0, introducing configuration validation audits, environment templates, and secrets handling guidelines.

## Kairos v1.6.0
**Date:** June 2026

This release integrates active configuration audits on application startup, full environment templates across services, and dedicated guides for secure secrets configuration.

### Features
- **Startup Configuration Validation**: Added Pydantic and runtime validation checks that assert correct environment settings (`APP_ENV`, `DATABASE_URL`, `ROOT_PATH`), automatically creating SQLite parent directories and running write permission checks.
- **Fail-Fast Security Audits**: Logs critical errors and halts application startup in production (`APP_ENV=production`) if `KAIROS_API_KEY` is missing or empty. Logs warnings for open CORS wildcard configurations.
- **Environment Templates**: Created root-level `.env.example`, `apps/api/.env.example`, and updated `apps/dashboard/.env.example` with safe local development defaults.
- **Secrets Management Documentation**: Created `docs/configuration.md` with guidelines on shared LAN secrets, Portainer variable injections, Zima OS environment placements, and safe key rotation protocols.

---

# Kairos v1.5.0 Release Notes

Welcome to Kairos v1.5.0, enabling reverse proxy readiness, HTTPS/LAN domain support, and Portainer stack deployment compatibility.

## Kairos v1.5.0
**Date:** June 2026

This release brings proxy headers trust, root path routing config, Portainer stack compatibility, and dynamic LAN reverse proxy examples.

### Features
- **Reverse Proxy Readiness**: Added `ROOT_PATH` environment variable support to mount the API on subpaths, and configured Uvicorn to trust proxy headers (`UVICORN_PROXY_HEADERS=true` and `UVICORN_FORWARDED_ALLOW_IPS=*`).
- **Portainer Stack Compatibility**: Documented how to deploy Kairos as a stack inside Portainer, including environment variables setup and named volume persistency configurations.
- **LAN Domain & HTTPS Setup**: Added dynamic documentation for Caddy and Traefik reverse proxies to secure LAN access (e.g., `kairos.local` and `kairos-api.local`).

---

# Kairos v1.4.0 Release Notes

Welcome to Kairos v1.4.0, introducing production-ready operations and system monitoring support.

## Kairos v1.4.0
**Date:** June 2026

This release integrates structured logging, readiness/metrics monitoring endpoints, automated backups with retention, and Docker logging constraints.

### Features
- **Unified Structured Logging**: Unified Python root and Uvicorn loggers to format stdout logs as `[TIMESTAMP] [LEVEL] [LOGGER] MESSAGE` in UTC.
- **Self-Checks & Readiness Endpoints**: Added startup validations check (checking SQLite write, data dir, and backup path permissions) accessible via `/ready` (returning 503 if unready).
- **System Metrics**: Added root-level `/metrics` returning uptime, database connection status, and HTTP requests status code distributions (JSON format).
- **Backup Script Retention**: Refactored `backup-sqlite.sh` to output structured logs and enforce a strict 14-backup chronological retention policy.
- **Docker Log Rotation**: Restricted container logs in `docker-compose.yml` to `10m` size limits to protect host storage space.

---

# Kairos v1.3.0 Release Notes

Welcome to Kairos v1.3.0, introducing local API key authentication and LAN security hardening.

## Kairos v1.3.0
**Date:** June 2026

This release brings local-first optional API key authentication to secure LAN deployments (e.g., on Zima OS / CasaOS).

### Features
- **Local API Key Authentication**: Protects project, task, and memory endpoints when `KAIROS_API_KEY` is configured.
- **Opt-in Compatibility**: Authentication is disabled by default if `KAIROS_API_KEY` is unset or empty, ensuring smooth local development.
- **Docker Healthcheck**: Added container healthchecks for the API service.
- **Dashboard Forwarding**: The Next.js dashboard automatically authenticates requests using the `NEXT_PUBLIC_KAIROS_API_KEY` environment variable.
- **Public Health Endpoints**: `/health` and `/api/v1/health` remain fully public for container orchestration and status verification.

---

# Kairos v1.0 Release Notes

Welcome to Kairos v1.0.0, the first stable local-first MVP release.

## Kairos v1.0.0
**Date:** June 2026

This release solidifies the foundation of Kairos OS as a local-first personal API and dashboard.

### Features
- **Local Persistence**: Data is saved directly to local SQLite databases without cloud requirements.
- **Projects, Tasks, and Memories**: Full CRUD capabilities for tracking work and context.
- **Search and Filter**: Client-side quick-filtering on text and descriptions.
- **Project Views (Deep Links)**: Focus the dashboard on a single project via `?project_id=<id>`.
- **Stats Overview**: Global and per-project stats, including a visual completion progress bar.
- **Accessibility & Theming**: Clean responsive layouts with Dark Mode support and keyboard navigation improvements.

## Historical Milestones Summary
- **v0.9**: Dashboard responsive polish and basic accessibility improvements.
- **v0.8**: Added dashboard stats overview with global and per-project metrics.
- **v0.7.1**: Fixed SQLite startup migration for `memories.project_id`.
- **v0.7**: Implemented project views and deep links.
- **v0.6**: Implemented simple client-side search and filters.
- **v0.5**: Added lightweight inline edit and delete actions.
- **v0.4**: Implemented lightweight create actions for dashboard.
- **v0.3**: Established persistent local SQLite storage.
- **v0.2**: Dockerized API development environment.
- **v0.1**: Initial foundation layout and FastAPI stub.

## Known Limitations
- Advanced state management or optimistic UI updates are minimal; the dashboard fetches fresh data after mutations.
- No remote sync or multi-user authentication in this local-first version.
- SQLite schema migrations are simple startup checks (not using Alembic yet).

## Next Recommended Milestone
**v1.1**: Dashboard UI polish, custom component refinement, and potentially introducing lightweight tag management or markdown rendering for memory content.
