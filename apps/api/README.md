# Kairos Core API

Kairos Core API (v2.8.0) is a FastAPI service for Kairos domain and control-plane modules:

- Projects
- Tasks
- Memories
- Approval requests
- Controlled n8n webhook trigger history

The service uses SQLAlchemy with environment-based configuration. Direct local
runs use persistent SQLite storage by default. Docker Compose runs still use
PostgreSQL inside the Compose network.

## Setup

From `apps/api/`:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Copy the root environment example if needed:

```sh
cp ../../.env.example ../../.env
```

## Docker Compose

Start the API and its PostgreSQL dependency through Docker Compose from the
repository root:

```sh
docker compose -f infra/docker-compose.dev.yml up -d --build kairos-api
```

The API container uses the Docker-internal hostname `postgres` for
`DATABASE_URL`:

```text
postgresql+psycopg://kairos:kairos_dev_password@postgres:5432/kairos
```

View API logs:

```sh
docker compose -f infra/docker-compose.dev.yml logs -f kairos-api
```

Verify the Dockerized API:

```sh
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/projects
```

## Manual Uvicorn Run

Run the API directly from `apps/api/` when you do not want to use Docker:

```sh
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The default local database file is:

```text
data/kairos-local.sqlite3
```

On startup, the API creates the database tables automatically and seeds the
default Kairos project, task, and memory only when the database is empty.

Run tests from `apps/api/`:

```sh
pytest
```

## Environment Variables

- `APP_NAME`: service name.
- `APP_VERSION`: service version.
- `API_V1_PREFIX`: versioned API prefix, default `/api/v1`.
- `DATABASE_URL`: SQLAlchemy database URL.
- `CORS_ORIGINS`: comma-separated list of allowed browser origins.
- `CREATE_TABLES_ON_STARTUP`: create tables automatically for local
  development.
  Defaults to `true`.
- `USE_MOCK_DATA`: serve in-memory local mock data instead of the configured
  database. Defaults to `false`.
- `KAIROS_OPERATOR_TOKEN`: optional server-side operator token. When set,
  approve, reject, and trigger-n8n require `X-Kairos-Operator-Token`.
- `N8N_WEBHOOK_TRIGGER_ENABLED`: enable the controlled n8n trigger endpoint.
  Defaults to `false`.
- `N8N_WEBHOOK_URL`: server-side configured n8n webhook URL. Never returned
  by API responses or stored in workflow run history.
- `N8N_WEBHOOK_TIMEOUT_SECONDS`: timeout for the single synchronous n8n POST.
  Defaults to `10`.

Direct local SQLite default:

```text
sqlite:///.../data/kairos-local.sqlite3
```

## Endpoints

- `GET /health`
- `GET /api/v1/health`
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`
- `GET /api/v1/tasks`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `PATCH /api/v1/tasks/{task_id}`
- `DELETE /api/v1/tasks/{task_id}`
- `GET /api/v1/memories`
- `POST /api/v1/memories`
- `GET /api/v1/memories/{memory_id}`
- `PATCH /api/v1/memories/{memory_id}`
- `DELETE /api/v1/memories/{memory_id}`
- `POST /api/v1/approvals`
- `GET /api/v1/approvals`
- `GET /api/v1/approvals/{approval_id}`
- `POST /api/v1/approvals/{approval_id}/approve`
- `POST /api/v1/approvals/{approval_id}/reject`
- `POST /api/v1/approvals/{approval_id}/trigger-n8n`
