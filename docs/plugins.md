# Plugin & Extension Framework Foundation

Welcome to the Kairos Plugin Framework Foundation (v1.8.0). This document describes the modular extension and command registry schemas designed to support local-first AI operating system operations.

---

## Architecture Design

### 1. Metadata-Only Command Registry
To preserve security and sandbox stability in homelabs, **this release does not execute third-party code dynamically**. Instead, it introduces:
- A standardized **Plugin manifest** loading schema.
- A standardized **Command manifest** registry detailing operational system interfaces.

These represent built-in capabilities and custom modular manifests, mapping permission sets, input/output schemas, categories, and safety indicators into queryable metadata resources.

---

## Manifest Schemas

### 1. Plugin Manifest Schema (`PluginManifest`)
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
| `entry_type` | `str` | `"builtin"` | Extension load strategy (`"builtin"` or `"external"`). |
| `entry_ref` | `str` | *Required* | Python package path or local directory path reference. |
| `permissions`| `list[str]`| `[]` | Access scopes required by the plugin. |
| `config_schema`| `dict` | `{}` | JSON schema describing configuration params. |
| `metadata` | `dict` | `{}` | Extra metadata (authors, links, tier levels). |
| `commands` | `list` | `[]` | Commands exposed by the plugin (`CommandManifest`). |

### 2. Command Manifest Schema (`CommandManifest`)
Commands represent specific actions exposed by extensions. They are declared under the `commands` list field in the plugin manifest:

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `id` | `str` | *Required* | Unique command identifier (e.g. `core.projects.create_project`). |
| `plugin_id` | `str` | *Required* | Owner plugin ID (e.g. `core.projects`). |
| `name` | `str` | *Required* | User-friendly command name. |
| `description`| `str` | *Required* | Functional explanation of the command. |
| `category` | `str` | *Required* | Operation category (`read`, `write`, `admin`). |
| `input_schema`| `dict` | `{}` | JSON schema validating command argument payloads. |
| `output_schema`| `dict` | `{}` | JSON schema representing return values. |
| `permissions`| `list[str]`| `[]` | Security permissions needed to execute the command. |
| `enabled` | `bool` | `true` | Command state toggle. |
| `dangerous` | `bool` | `false` | Marks if the command triggers critical actions (e.g., delete, backup). |
| `metadata` | `dict` | `{}` | Telemetry or UI indicators. |

---

## Directory Scanner Loading Behavior

1. **Scan Path**: Parses `.json` files in the directory path defined by `KAIROS_PLUGINS_DIR` (defaults to `data/plugins/` inside Docker volume bounds).
2. **Conflict Resolution**:
   - Built-in IDs (`core.projects`, `core.tasks`, `core.memories`, `core.operations`) always take precedence. If an external plugin declares a duplicate built-in ID, it is skipped with a `WARNING` log.
   - If an external plugin declares a duplicate ID of an already registered external plugin, it is skipped with a `WARNING` log.
3. **Robust Safety**: Invalid JSON structures or missing required properties trigger `WARNING` logs and are skipped without crashing the system startup process.

---

## API Usage Examples

### 1. Retrieve all commands
- **Endpoint**: GET `/api/v1/commands`
- **Optional parameter**: `include_disabled=true` (defaults to `false`)
- **Headers**:
  ```text
  X-Kairos-API-Key: <your-key-here>
  ```
- **Response**:
  ```json
  [
    {
      "id": "core.operations.run_backup",
      "plugin_id": "core.operations",
      "name": "Run Database Backup",
      "description": "Manually trigger an automated timestamped backup copy of the SQLite database. [RESTRICTED]",
      "category": "admin",
      "input_schema": {},
      "output_schema": { "type": "object" },
      "permissions": ["admin:backup"],
      "enabled": true,
      "dangerous": true,
      "metadata": {}
    }
  ]
  ```

### 2. Fetch a specific command
- **Endpoint**: GET `/api/v1/commands/core.operations.run_backup`
- **Response**:
  ```json
  {
    "id": "core.operations.run_backup",
    "plugin_id": "core.operations",
    "name": "Run Database Backup",
    "description": "Manually trigger an automated timestamped backup copy of the SQLite database. [RESTRICTED]",
    "category": "admin",
    "input_schema": {},
    "output_schema": { "type": "object" },
    "permissions": ["admin:backup"],
    "enabled": true,
    "dangerous": true,
    "metadata": {}
  }
  ```

---

## How to Add a Local Metadata Plugin

1. Create a JSON manifest file (e.g. `my-plugin.json`) in your `data/plugins/` directory:
   ```json
   {
     "id": "custom.weather",
     "name": "Custom Weather extension",
     "version": "1.0.0",
     "description": "Fetches local weather reports using coordinates.",
     "category": "utility",
     "enabled": true,
     "entry_type": "external",
     "entry_ref": "data/plugins/weather",
     "commands": [
       {
         "id": "custom.weather.get_report",
         "plugin_id": "custom.weather",
         "name": "Get Weather Report",
         "description": "Exposes temperature readings.",
         "category": "read",
         "input_schema": {
           "type": "object",
           "properties": {
             "zipcode": { "type": "string" }
           },
           "required": ["zipcode"]
         }
       }
     ]
   }
   ```
2. Restart the containers. The scanner will parse the metadata and register the endpoints automatically.
