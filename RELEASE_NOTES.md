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
