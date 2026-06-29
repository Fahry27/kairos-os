# Kairos OS Architecture

## Overview

Kairos OS is planned as a modular system with an API service, a dashboard
experience, shared documentation, and supporting infrastructure. Kairos Core API
v2.9.0 is the current workflow run history and audit trail milestone.

## Repository Boundaries

```text
apps/api/        FastAPI service code.
apps/dashboard/  Next.js dashboard code.
data/            Reserved data workspace.
docs/            Architecture, development, and product documentation.
infra/           Infrastructure definitions and local service orchestration.
infra/config/    Portable infrastructure configuration.
scripts/         Development and operations helper scripts.
```

The `apps/dashboard/` directory contains the dashboard application.

## Planned Components

### API

The API is implemented with FastAPI and SQLAlchemy. It exposes health checks,
basic CRUD modules for Projects, Tasks, and Memories, approval management, one
controlled n8n webhook trigger endpoint tied to approved workflow approval
requests, and read-only workflow run history endpoints. Direct local
development uses persistent SQLite storage in the
repository `data/` workspace. Docker Compose runs use PostgreSQL through
environment-based configuration.

### Dashboard

The dashboard is implemented with Next.js as a local interface for Kairos Core
API health, projects, tasks, memories, registries, AI runtime status, and
approval management, and workflow run history. v2.9.0 keeps workflow run
history read-only and does not add trigger or retry controls.

### Controlled n8n Trigger

Kairos v2.8.0 uses the existing Approval Gate as the single source of truth.
Approving an `ApprovalRequest` only changes status to `approved`; it does not
execute anything. A separate `POST /api/v1/approvals/{approval_id}/trigger-n8n`
call may trigger one configured n8n webhook only when the approval is approved,
has `action_type=workflow`, and is marked as `n8n_webhook`.

Trigger attempts are recorded as sanitized `WorkflowRun` history. The history
does not store webhook URLs, tokens, credentials, environment values, raw n8n
response bodies, or raw LLM responses. No connector fan-out, local command
execution, Hermes/OpenClaw trigger, cloud provider call, background worker,
automatic retry, or autonomous agent loop is introduced.

### Workflow Run Audit Trail

Kairos v2.9.0 exposes sanitized `WorkflowRun` history through read-only API
endpoints and a dashboard audit card. Operators can filter by status, approval
ID, and target type, then inspect request and response summaries. The audit
surface does not add trigger, retry, approve/reject, or execution controls.

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

The `data/` directory is reserved for seed data, fixtures, exports, and local
runtime data workflows. Direct local API runs store the SQLite database there by
default. Runtime database files are local-only and ignored by Git.

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
