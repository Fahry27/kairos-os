# Kairos OS Development

## Prerequisites

- Git
- Python 3.12 or newer
- Docker Desktop or a compatible Docker Engine
- Docker Compose v2

The API runtime lives in `apps/api/`. The dashboard runtime lives in
`apps/dashboard/`.

## Initial Setup

Copy the example environment file:

```sh
cp .env.example .env
```

Review and adjust local values as needed. The defaults are safe for local
development.

## Local Infrastructure

Start all local services:

```sh
docker compose up -d --build
```

Stop local services:

```sh
docker compose -f infra/docker-compose.dev.yml down
```

Remove local service data:

```sh
docker compose -f infra/docker-compose.dev.yml down -v
```

## Kairos API via Docker Compose

The recommended development path is Docker Compose. The `kairos-api` service
builds `apps/api`, waits for the `postgres` service health check, mounts the API
source into `/app`, connects to PostgreSQL through the internal Docker hostname
`postgres`, and exposes the API on `http://localhost:8000`.

Start the API:

```sh
docker compose -f infra/docker-compose.dev.yml up -d --build kairos-api
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

Expected response:

```json
{
  "status": "ok",
  "service": "kairos-api",
  "version": "2.1.0",
  "uptime": 12,
  "database": "connected",
  "docker_mode": true
}
```

Stop the API:

```sh
docker compose -f infra/docker-compose.dev.yml stop kairos-api
```

If PostgreSQL was first started before `POSTGRES_DB=kairos` was configured, the
existing Docker volume may not contain the `kairos` database. For a disposable
development reset, stop services and remove volumes:

```sh
docker compose -f infra/docker-compose.dev.yml down -v
docker compose -f infra/docker-compose.dev.yml up -d --build kairos-api
```

This deletes local development database data.

## API Development

For direct local Python development, install API dependencies:

```sh
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Run the API:

```sh
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run API tests:

```sh
pytest
```

The API reads configuration from environment variables and the repository root
`.env` file. For direct local Python development, the default `DATABASE_URL`
points at a persistent SQLite file in `data/kairos-local.sqlite3`. Docker
Compose overrides it to use
`postgresql+psycopg://...@postgres:5432/...` inside the Compose network.
The API creates tables automatically and seeds the default Kairos project, task,
and memory only when the database is empty.

To reset only the direct local SQLite API data, stop the API and remove:

```text
data/kairos-local.sqlite3
```

Verify health, readiness, and metrics:

```sh
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/metrics
```

Verify local SQLite persistence:

```sh
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"Local SQLite Project"}'
curl http://localhost:8000/api/v1/projects
```

## Dashboard Development

The dashboard is a Next.js App Router app that reads from and writes to the
Kairos API at `http://localhost:8000` by default.

Install dashboard dependencies:

```sh
cd apps/dashboard
npm install
```

Run the dashboard:

```sh
npm run dev
```

Open:

```text
http://localhost:3000
```

The dashboard displays API health, projects, tasks, and memories. It also
includes lightweight create actions for those three resources. Override the API
URL with `NEXT_PUBLIC_KAIROS_API_URL` when needed.

Verify the dashboard can read API data:

```sh
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/projects
open http://localhost:3000
```

Verify dashboard write actions by creating one project, task, and memory in the
browser, then checking the API list endpoints again.

## Application Directories

Application code is split by runtime:

- `apps/api/` contains the FastAPI service.
- `apps/dashboard/` contains the read-only Next.js dashboard.

Future dashboard modules beyond the v0.1 read-only surface should stay small,
reviewable, and tied to an explicit implementation task.

## Reserved Support Directories

The following directories are reserved for future non-application support work:

- `data/`
- `data/exports/`
- `data/imports/`
- `data/knowledge/`
- `data/samples/`
- `infra/caddy/`
- `infra/config/`
- `infra/postgres/`
- `infra/qdrant/`
- `infra/redis/`
- `scripts/`

Keep these directories free of committed secrets and host-specific assumptions.
Use them for reviewed, portable project assets only when a later task defines
the contents.

## Production Operations Support

Kairos v2.5.0 includes enhanced operations and monitoring support:

### Structured Logging
API logs are formatted as standard log strings: `[TIMESTAMP] [LEVEL] [LOGGER] MESSAGE`. Time is always formatted in UTC ISO. This is stdout/stderr friendly and automatically handled by Docker's logging driver (e.g., `json-file` limited to `max-size: 10m` in `docker-compose.yml`).

### Monitoring & Readiness Checks
- **Health check (`/health` / `/api/v1/health`)**: Exposes basic health metrics (uptime, database status, docker environment detection).
- **Readiness check (`/ready` / `/api/v1/ready`)**: Performs startup validation checks (SQLite database file availability, backup directory writability, data path writability) and database query responsiveness. Returns `503 Service Unavailable` if unready.
- **Metrics check (`/metrics` / `/api/v1/metrics`)**: Exposes JSON stats including uptime, database status, container mode, and processed HTTP request statistics (by HTTP status class). It does not query database record counts on every request to ensure high responsiveness.

### Reverse Proxy & Portainer Compatibility
- **Root Path Routing**: The API exposes a `ROOT_PATH` setting. If set, FastAPI registers all endpoints relative to the given subpath, which is highly useful when mounting the API behind reverse proxies routing to subfolders.
- **Proxy Headers**: The API is configured to trust proxy-provided headers like `X-Forwarded-Proto`, `X-Forwarded-For`, and `X-Forwarded-Host`. Enable this in Docker/Uvicorn environment by setting `UVICORN_PROXY_HEADERS=true` and `UVICORN_FORWARDED_ALLOW_IPS=*`.
- **Portainer Stacks**: The `docker-compose.yml` supports named volumes mapping by uncommenting the designated blocks for Portainer Stack deployments.

## Documentation Workflow

- Update `docs/architecture.md` when system boundaries or major technical
  decisions change.
- Update this file when local setup, tooling, or developer workflows change.
- Add environment variables to `.env.example` when they become required.

## Verification

For foundation-only changes, verify:

```sh
git status --short
docker compose -f infra/docker-compose.dev.yml config
```

For API changes, also verify:

```sh
cd apps/api
pytest
```

The Docker Compose command requires Docker Compose to be installed locally.
