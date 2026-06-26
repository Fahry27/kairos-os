# Kairos OS Architecture

## Overview

Kairos OS is planned as a modular system with an API service, a dashboard
experience, shared documentation, and supporting infrastructure. Kairos Core API
v0.1 is the first implemented application component.

## Repository Boundaries

```text
apps/api/        FastAPI service code.
apps/dashboard/  Future Next.js dashboard code.
data/            Reserved data workspace.
docs/            Architecture, development, and product documentation.
infra/           Infrastructure definitions and local service orchestration.
infra/config/    Portable infrastructure configuration.
scripts/         Development and operations helper scripts.
```

The `apps/dashboard/` directory is intentionally empty until dashboard
implementation begins.

## Planned Components

### API

The API is implemented with FastAPI and SQLAlchemy. It exposes health checks and
basic CRUD modules for Projects, Tasks, and Memories. PostgreSQL is the primary
database target, configured through environment variables.

### Dashboard

The dashboard is reserved for the future Next.js user interface. No Next.js
application code, build system, or routing layer has been added in this
foundation phase.

### Infrastructure

Infrastructure starts with Docker Compose definitions for services that future
application code is likely to need:

- PostgreSQL for relational persistence.
- Redis for caching, queues, or coordination.

These services are available for development convenience and as a portable base
for production-style home-server deployment.

The `infra/config/` directory is reserved for host-portable configuration that
can be shared across MacBook development, ZimaOS hosting, and a possible Ubuntu
Server LTS migration.

### Data

The `data/` directory is reserved for future seed data, fixtures, exports, and
local runtime data workflows. It should not become a hidden dependency for the
foundation repository.

### Scripts

The `scripts/` directory is reserved for future helper scripts that make
development, maintenance, backup, restore, or deployment tasks repeatable. No
scripts have been added in this foundation phase.

## Host Strategy

- Development machine: MacBook.
- Initial production/home-server host: ZimaOS.
- Optional long-term migration target: Ubuntu Server LTS.

ZimaOS is the initial host layer, not the Kairos core. Kairos should remain
Docker Compose based and independent from host-specific features as much as
possible. Services should be containerized and configured through portable
Compose files so the system can move from ZimaOS to Ubuntu Server later if
needed.

## Architectural Principles

- Keep application boundaries explicit.
- Keep services containerized and portable across supported hosts.
- Prefer documented decisions over implicit conventions.
- Separate local development infrastructure from application implementation.

## Open Decisions

- Next.js package manager and project layout.
- Authentication and authorization model.
- API migration strategy.
- Production backup, restore, and update strategy.
