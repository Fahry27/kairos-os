# External Service Connector Registry

Welcome to the Kairos Connector Registry Guide (v1.9.0). This document describes how Kairos discovers, models, and exposes external services hosted inside homelabs or Zima OS environments.

---

## Architecture Design

### 1. Metadata-Only Foundation
To maintain zero runtime security overhead, **this release does not make outbound network connections to external services**. Instead, it manages discovery templates:
- Stores basic endpoint coordinates (like `base_url`).
- Stores connectivity types (like `service_type` and `auth_type`).
- Exposes capabilities without executing operations.

### 2. Difference Between Plugins and Connectors

- **Plugins**: Extend internal OS operational logic, custom routers, state machine checks, or SQLite telemetry trackers.
- **Connectors**: Map external services running outside Kairos (e.g. Home Assistant, Ollama, Plex) so that future AI layers can understand where to send API actions.

---

## Manifest Schema (`ConnectorManifest`)
Custom service manifests are parsed from JSON files matching the following schema properties:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `str` | *Required* | Unique service identifier (e.g. `connector.ollama`). |
| `name` | `str` | *Required* | User-friendly service name. |
| `version` | `str` | *Required* | Semver version of the service template. |
| `description`| `str` | *Required* | Purpose description. |
| `category` | `str` | *Required* | Broad class (e.g. `ai`, `automation`, `media`). |
| `enabled` | `bool` | `true` | Activity toggle. |
| `service_type`| `str` | *Required* | Underlying engine type (e.g. `ai_inference`). |
| `base_url` | `str` | `null` | IP address or local DNS domain of the service. |
| `auth_type` | `str` | *Required* | Auth scheme (`none`, `api_key`, `basic_auth`, `plex_token`). |
| `capabilities`| `list` | `[]` | Exposed actions supported by the engine. |
| `health_endpoint`| `str` | `null` | Ping subpath to check endpoint connectivity. |
| `docs_url` | `str` | `null` | Reference URL for help configurations. |
| `tags` | `list` | `[]` | Discovery tags. |
| `metadata` | `dict` | `{}` | Additional structural parameters. |

---

## Known Zima OS Service Mappings

The following pre-configured built-ins map out popular homelab services:

1. **Ollama (`connector.ollama`)**: `ai_inference` matching `http://localhost:11434` endpoints.
2. **Open WebUI (`connector.open_webui`)**: `ai_webui` dashboard wrapper.
3. **n8n (`connector.n8n`)**: `workflow_engine` trigger manager on port `5678`.
4. **Tailscale (`connector.tailscale`)**: Mesh routing mesh networks.
5. **Uptime Kuma (`connector.uptime_kuma`)**: Status monitoring checking.
6. **Portainer (`connector.portainer`)**: Docker orchestration checking.
7. **DeepSeek OCR (`connector.deepseek_ocr`)**: Optical character vision engine.
8. **OpenClaw (`connector.openclaw`)**: Simulated gaming logic checker.
9. **Plex (`connector.plex`)**: Personal media server indexing.

---

## Security Model

1. **Gate Guard**: Connector endpoints (`/api/v1/connectors`) require active LAN API keys (`X-Kairos-API-Key`) when authentication is configured.
2. **No Secret Storage**: Connectors are metadata descriptors. **Do not put passwords, auth secrets, or credentials directly in your manifest templates**. In future updates, secrets will be loaded dynamically using secure local environment variables or credential databases.
3. **Toggle Control**: Set `KAIROS_CONNECTORS_ENABLED=false` to completely disable the registry.

---

## How to Add a Custom Connector Manifest

To register a custom service, place a JSON file (e.g. `home-assistant.json`) in your `data/connectors/` directory:

```json
{
  "id": "custom.home-assistant",
  "name": "Home Assistant Node",
  "version": "1.0.0",
  "description": "Smart home hub controlling local IoT nodes.",
  "category": "iot",
  "enabled": true,
  "service_type": "smart_home",
  "base_url": "http://192.168.1.50:8123",
  "auth_type": "api_key",
  "capabilities": ["toggle_lights", "read_sensors"],
  "health_endpoint": "/api/",
  "docs_url": "https://www.home-assistant.io",
  "tags": ["iot", "smart_home", "local"]
}
```

Restart the API service container, and the scanner will load it automatically into the registry.
