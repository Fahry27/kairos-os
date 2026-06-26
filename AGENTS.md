# Agent Guidelines

These guidelines apply to AI and human-assisted development work in this
repository.

## Project State

Kairos OS is in its foundation phase. The repository should remain free of API
and dashboard application code until implementation work is explicitly
requested.

## Working Principles

- Preserve the current repository boundaries.
- Keep foundation changes small, explicit, and easy to review.
- Prefer documentation and configuration over speculative implementation.
- Do not add production services, frameworks, or generated application files
  without a clear task.
- Keep secrets out of Git. Add required variables to `.env.example` with safe
  placeholder values.

## Expected Layout

- `apps/api/` is reserved for the future FastAPI service.
- `apps/dashboard/` is reserved for the future Next.js dashboard.
- `data/` is reserved for local seed data, fixtures, exports, and generated
  runtime data that should be reviewed before committing.
- `docs/` contains product, architecture, and development documentation.
- `infra/` contains local and deployable infrastructure definitions.
- `infra/config/` is reserved for portable infrastructure configuration.
- `scripts/` is reserved for development, maintenance, and deployment helper
  scripts.

## Verification

Before handing off foundation work, confirm that:

- Required files exist.
- Reserved application directories contain no implementation code.
- Reserved data, scripts, and infrastructure configuration directories exist.
- Docker Compose configuration is syntactically valid when Docker is available.
- Documentation reflects the actual repository state.
