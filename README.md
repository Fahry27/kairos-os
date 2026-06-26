# Kairos OS

Kairos OS is a development-stage operating layer for personal and team workflows.
This repository currently contains only the project foundation: documentation,
environment conventions, infrastructure placeholders, and empty application
directories.

No API or dashboard application code has been implemented yet.

## Repository Structure

```text
.
├── apps/
│   ├── api/
│   └── dashboard/
├── data/
│   ├── exports/
│   ├── imports/
│   ├── knowledge/
│   └── samples/
├── docs/
│   ├── architecture.md
│   └── development.md
├── infra/
│   ├── caddy/
│   ├── config/
│   ├── postgres/
│   ├── qdrant/
│   ├── redis/
│   └── docker-compose.dev.yml
├── scripts/
├── .env.example
├── .gitignore
├── AGENTS.md
└── README.md
```

## Current Status

- Foundation repository initialized.
- API and dashboard directories are reserved but intentionally empty.
- Data, scripts, and infrastructure configuration directories are reserved.
- Local development services are described in `infra/docker-compose.dev.yml`.
- Architecture and development notes live in `docs/`.

## Getting Started

1. Copy the example environment file:

   ```sh
   cp .env.example .env
   ```

2. Review the development guide:

   ```sh
   open docs/development.md
   ```

3. Start local infrastructure when needed:

   ```sh
   docker compose -f infra/docker-compose.dev.yml up -d
   ```

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Agent Guidelines](AGENTS.md)
