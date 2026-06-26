# Kairos OS Development

## Prerequisites

- Git
- Python 3.12 or newer
- Docker Desktop or a compatible Docker Engine
- Docker Compose v2

The API runtime lives in `apps/api/`. The dashboard has not been implemented
yet.

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
docker compose -f infra/docker-compose.dev.yml up -d
```

Start the API and PostgreSQL only:

```sh
docker compose -f infra/docker-compose.dev.yml up -d --build kairos-api
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
{"status":"ok","service":"Kairos API","version":"0.2.0"}
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
`.env` file. For direct local Python development, `DATABASE_URL` should point at
PostgreSQL on `localhost`. Docker Compose overrides it to use
`postgresql+psycopg://...@postgres:5432/...` inside the Compose network.

Verify the health endpoint:

```sh
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

## Application Directories

The following directories are reserved for future implementation work:

- `apps/dashboard/`

Do not add Next.js application code until the dashboard implementation scope has
been defined.

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
