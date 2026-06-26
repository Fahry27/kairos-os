# Kairos Core API

Kairos Core API v0.1 is a FastAPI service for the first Kairos domain modules:

- Projects
- Tasks
- Memories

The service uses SQLAlchemy with PostgreSQL and environment-based
configuration.

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

Start local infrastructure from the repository root:

```sh
docker compose -f infra/docker-compose.dev.yml up -d postgres
```

Run the API from `apps/api/`:

```sh
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests from `apps/api/`:

```sh
pytest
```

## Environment Variables

- `APP_NAME`: service name, default `kairos-api`.
- `APP_VERSION`: service version, default `0.1.0`.
- `API_V1_PREFIX`: versioned API prefix, default `/api/v1`.
- `DATABASE_URL`: SQLAlchemy PostgreSQL URL.
- `CORS_ORIGINS`: comma-separated list of allowed browser origins.
- `CREATE_TABLES_ON_STARTUP`: create tables automatically for v0.1.
  Defaults to `true`.

Local PostgreSQL default:

```text
postgresql+psycopg://kairos:kairos_dev_password@localhost:5432/kairos
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
