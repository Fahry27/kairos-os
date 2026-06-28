# Plugin & Extension Framework Foundation

Welcome to the Kairos Plugin Framework Foundation (v1.7.0). This document describes the modular extension schema designed to support local-first AI operating system modules.

---

## Architecture Design

### 1. Metadata-Only Phase (Current State)
To preserve security and sandbox stability in homelabs, **this release does not execute third-party code dynamically**. Instead, it introduces a standardized manifest definition mapping existing Kairos capabilities as structured, queryable extensions:
- `core.projects`
- `core.tasks`
- `core.memories`
- `core.operations`

These represent built-in capabilities, mapping permission sets, config schemas, categories, and entry points into queryable metadata resources.

### 2. Manifest Schema (`PluginManifest`)
Each extension registers using a JSON manifest matching the following Pydantic-validated fields:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `str` | *Required* | Unique dot-spaced identifier (e.g. `core.projects`). |
| `name` | `str` | *Required* | User-friendly name. |
| `version` | `str` | *Required* | Semver version of the extension. |
| `description`| `str` | *Required* | Description explaining functionality. |
| `category` | `str` | *Required* | Classification category (e.g. `core`, `utility`, `ai`). |
| `enabled` | `bool` | `true` | Active status in the registry. |
| `capabilities`| `list[str]`| `[]` | Supported core capabilities (e.g. `task_management`). |
| `entry_type` | `str` | `"builtin"` | Extension load strategy (currently `"builtin"`). |
| `entry_ref` | `str` | *Required* | Python package path or route handler reference. |
| `permissions`| `list[str]`| `[]` | Access scopes required by the plugin. |
| `config_schema`| `dict` | `{}` | JSON schema describing configuration params. |
| `metadata` | `dict` | `{}` | Extra metadata (authors, links, tier levels). |

---

## Security Model

1. **Authentication Gate**: All plugin routes under `/api/v1/plugins` require active LAN API key headers (`X-Kairos-API-Key`) when authentication is configured.
2. **Deactivation**: If `KAIROS_PLUGINS_ENABLED=false` is configured in the environment:
   - GET `/api/v1/plugins` returns a clean, empty list (`[]`).
   - GET `/api/v1/plugins/{plugin_id}` raises `404 Not Found`.

---

## API Usage Examples

### 1. Retrieve all active extensions
- **Endpoint**: GET `/api/v1/plugins`
- **Optional parameter**: `include_disabled=true` (defaults to `false`)
- **Headers**:
  ```text
  X-Kairos-API-Key: <your-key-here>
  ```
- **Response**:
  ```json
  [
    {
      "id": "core.projects",
      "name": "Core Projects Extension",
      "version": "1.7.0",
      "description": "Core project management capabilities including project tracking and progress analysis.",
      "category": "core",
      "enabled": true,
      "capabilities": ["project_management", "analytics"],
      "entry_type": "builtin",
      "entry_ref": "app.api.v1.endpoints.projects",
      "permissions": ["read:projects", "write:projects"],
      "config_schema": {},
      "metadata": {
        "author": "Kairos Core Team",
        "tier": "system"
      }
    }
  ]
  ```

### 2. Fetch a specific plugin
- **Endpoint**: GET `/api/v1/plugins/core.tasks`
- **Response**:
  ```json
  {
    "id": "core.tasks",
    "name": "Core Tasks Extension",
    "version": "1.7.0",
    "description": "Core task management capabilities supporting subtasks, priorities, and status transitions.",
    "category": "core",
    "enabled": true,
    "capabilities": ["task_management"],
    "entry_type": "builtin",
    "entry_ref": "app.api.v1.endpoints.tasks",
    "permissions": ["read:tasks", "write:tasks"],
    "config_schema": {},
    "metadata": {
      "author": "Kairos Core Team",
      "tier": "system"
    }
  }
  ```

---

## Future Extensions Direction

In future milestones, the framework will scale to support user-defined custom plugins loaded dynamically from `data/plugins/`:
- **Python-based runtime plugins** using standard entry-point hooks.
- **Client-side UI dashboard extensions** loaded dynamically via iframe widgets.
- **Access control sandboxing** to limit file system/database actions using declared permissions list configurations.
