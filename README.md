# Kairos OS

Kairos OS is a development-stage operating layer for personal and team workflows.
This repository contains the project foundation and the first Kairos Core API
implementation.

The dashboard application now provides a read-only view of the Kairos Core API.

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
- Kairos Core API v0.1 is implemented with FastAPI under `apps/api/`.
- Kairos Core API is Dockerized for local development through
  `infra/docker-compose.dev.yml`.
- Current milestone: Kairos Core API v0.2 adds the Docker Compose API service.
- Kairos Dashboard v0.1 is implemented with Next.js under `apps/dashboard/`.
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
   docker compose -f infra/docker-compose.dev.yml up -d --build kairos-api
   ```

4. Verify the API:

   ```sh
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/health
   ```

5. Run the API without Docker if needed:

   ```sh
   cd apps/api
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -e .
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Run the dashboard:

   ```sh
   cd apps/dashboard
   npm install
   npm run dev
   ```

   Open `http://localhost:3000`.

   Set `NEXT_PUBLIC_KAIROS_API_URL` if the API is not running at
   `http://localhost:8000`.

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Agent Guidelines](AGENTS.md)
