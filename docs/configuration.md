# Configuration & Secrets Management Guide

This document details all configuration parameters, environment settings, secrets handling, and deployment guidance for Kairos v1.8.0.

---

## Environment Variables Reference

### Required Variables
| Variable | Scope | Default | Description |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_KAIROS_API_URL` | Dashboard | `http://localhost:8000` | The endpoint URL of the API. Must be resolvable by the client browser. |

### Optional / Customization Variables
| Variable | Scope | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | API | `development` | The environment mode: `development`, `production`, or `test`. |
| `KAIROS_API_KEY` | API | *None* | Shared API key to authenticate requests. Required if `APP_ENV=production`. |
| `NEXT_PUBLIC_KAIROS_API_KEY`| Dashboard | *None* | Shared API key sent by the dashboard. Must match `KAIROS_API_KEY`. |
| `KAIROS_PLUGINS_ENABLED` | API | `true` | Enables the lightweight plugin/extensions registry (`true`/`false`). |
| `KAIROS_PLUGINS_DIR` | API | `data/plugins`| Location directory where external JSON manifests are scanned and loaded. |
| `CORS_ORIGINS` | API | `http://localhost:3000,http://127.0.0.1:3000` | Allowed origins for cross-origin requests. Commas or JSON arrays allowed. |
| `ROOT_PATH` | API | *None* | Subpath prefix (e.g. `/api`) if mounting the backend behind folder-based proxies. |
| `DATABASE_URL` | API | SQLite default | Database connection string. Must start with `sqlite://` or `postgresql`. |
| `CREATE_TABLES_ON_STARTUP` | API | `true` | Runs database migrations automatically on startup. |
| `USE_MOCK_DATA` | API | `false` | Seeds the database with mock tasks and projects on startup (development only). |

### AI Runtime & Ollama Readiness Variables
| Variable | Scope | Default | Description |
| :--- | :--- | :--- | :--- |
| `KAIROS_AI_ENABLED` | API | `true` | Master toggle for the AI Runtime capabilities. |
| `KAIROS_AI_PROVIDER` | API | `ollama` | The active AI provider to use. |
| `KAIROS_AI_DRY_RUN_ENABLED` | API | `true` | Enables safe prompt package assembly without outbound LLM calls. |
| `KAIROS_AI_MAX_CONTEXT_COMMANDS` | API | `20` | Max commands to include in dry-run context. |
| `KAIROS_AI_MAX_CONTEXT_CONNECTORS` | API | `20` | Max connectors to include in dry-run context. |
| `KAIROS_AI_MAX_CONTEXT_PLUGINS` | API | `20` | Max plugins to include in dry-run context. |
| `KAIROS_OLLAMA_READINESS_ENABLED` | API | `true` | Enables the safe Ollama readiness and model discovery checks. |
| `KAIROS_OLLAMA_BASE_URL` | API | `http://localhost:11434` | Base URL used specifically for the Ollama readiness check. |
| `KAIROS_OLLAMA_TAGS_PATH` | API | `/api/tags` | Path used to check Ollama model availability safely. |
| `KAIROS_OLLAMA_TIMEOUT_SECONDS` | API | `2` | Short timeout for the readiness check. |

---

## API Key Authentication & Secrets Warning

> [!IMPORTANT]
> - **Shared LAN Secret**: `KAIROS_API_KEY` acts as a shared secret key for LAN (Local Area Network) deployments. It is **not** a full multi-user authentication system (there are no user accounts, passwords, or role permissions).
> - **Client-side exposure**: Because the Next.js dashboard is compiled and runs client-side inside the user's web browser, the `NEXT_PUBLIC_KAIROS_API_KEY` is transmitted in HTTP headers and is visible in browser network inspector panels.
> - **Exposure Recommendation**: For private LAN (e.g. Zima OS/homelabs), this shared secret is sufficient to prevent unauthorized local queries. However, **do not expose Kairos ports directly to the public internet** or configure public DNS forwarding without wrapping access behind a secure VPN (like Tailscale) or proxy gate (like Authelia, Cloudflare Tunnels, or basic auth gates).

---

## Startup Environment Validation

Kairos v1.6.0 includes active configuration checks on startup:
1. **Invalid Schemes**: If `DATABASE_URL` is set to an unsupported database scheme (e.g., `mysql`), the app will fail to start.
2. **Path Validation**: `ROOT_PATH` must begin with `/` and must not have a trailing slash except `/`.
3. **Writability Check**: If SQLite is used, the system verifies that the target parent database folder exists (or creates it) and checks write permissions.
4. **Production Fail-Fast**: If `APP_ENV=production` and `KAIROS_API_KEY` is missing or empty, **the API will log a critical error and halt startup immediately** to prevent unauthenticated data exposure.
5. **CORS Warnings**: If `APP_ENV=production` and `CORS_ORIGINS` includes a wildcard (`*`), the backend logs a security warning.

---

## Deployment Guidance

### 1. Zima OS / CasaOS env Placement
For Zima OS (CasaOS), place environment files inside the dedicated AppData directory:
- Path: `/DATA/AppData/kairos/.env`
- Ensure file permissions restrict read access to authorized system users:
  ```sh
  chmod 600 /DATA/AppData/kairos/.env
  ```
- Use the `env_file:` declaration or load the file directly when launching via docker compose.

### 2. Portainer Stack env setup
In Portainer:
- Do **not** write raw secrets inside the compose template.
- Define `KAIROS_API_KEY` and `NEXT_PUBLIC_KAIROS_API_KEY` in the **Environment variables** section below the Web Editor stack container. Portainer injects these values securely into the container runtime.

---

## Safe Secret Rotation Steps

If you need to rotate or change your API key:
1. **Stop the Application**: Run `docker compose down` (or stop the Portainer Stack / CasaOS app).
2. **Update Configurations**: Edit the key value in `/DATA/AppData/kairos/.env` or inside Portainer Environment Variables. Ensure `KAIROS_API_KEY` and `NEXT_PUBLIC_KAIROS_API_KEY` match.
3. **Restart the Application**: Run `docker compose up -d` (or restart the stack).
4. **Verify**: Verify that requests return authenticated content successfully, and no authentication warning logs appear in container stdout.
