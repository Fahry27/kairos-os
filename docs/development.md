# Kairos OS Development

## Prerequisites

- Git
- Docker Desktop or a compatible Docker Engine
- Docker Compose v2

No application runtime is required yet because API and dashboard code have not
been implemented.

## Initial Setup

Copy the example environment file:

```sh
cp .env.example .env
```

Review and adjust local values as needed. The defaults are safe for local
development.

## Local Infrastructure

Start local services:

```sh
docker compose -f infra/docker-compose.dev.yml up -d
```

Stop local services:

```sh
docker compose -f infra/docker-compose.dev.yml down
```

Remove local service data:

```sh
docker compose -f infra/docker-compose.dev.yml down -v
```

## Application Directories

The following directories are reserved for future implementation work:

- `apps/api/`
- `apps/dashboard/`

Do not add FastAPI or Next.js application code until the implementation scope
has been defined.

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

The Docker Compose command requires Docker Compose to be installed locally.
