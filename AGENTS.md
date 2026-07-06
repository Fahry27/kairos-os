# Agent Guidelines

Authoritative sources for all future agent sessions:

- **[KAIROS_CONSTITUTION.md](KAIROS_CONSTITUTION.md)** — product vision, engineering constitution, agent behavior rules, sprint roadmap, stop conditions
- **[ROADMAP.md](ROADMAP.md)** — completed sprints, current sprint, upcoming sprints, post-v1 roadmap
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — system layers, seven engines, data flow, governance flow, file organization, key design decisions

## Working Principles

- Follow the Kairos Constitution. Architecture first, Mission first, AI second.
- No fake backend. No fake AI. No mock data. Everything production-quality.
- Keep changes small, explicit, and easy to review.
- Prefer deleting dead code over preserving it.
- Keep secrets out of Git.

## Repository Layout

- `apps/api/` — FastAPI backend (Kairos Core API)
- `apps/dashboard/` — Next.js frontend (Kairos Shell)
- `data/` — seed data, fixtures, exports, runtime data
- `docs/` — product, architecture, development documentation
- `infra/` — Docker Compose, Caddy, Postgres, Qdrant, Redis configs
- `scripts/` — development, maintenance, deployment helpers
