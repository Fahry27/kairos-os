# Kairos OS

Kairos OS is a development-stage operating layer for personal and team workflows.
This repository contains the project foundation and the first Kairos Core API
implementation.

The dashboard application provides a simple local interface for reading from and
creating records through the Kairos Core API.

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

- **Version**: Kairos v1.2.0 (Zima OS Deployment Ready)
- **Local-first**: The Kairos Core API uses persistent local SQLite storage for direct local API development (`data/kairos-local.sqlite3`).
- **Dashboard**: Features projects, tasks, memories, CRUD, filtering, project focus views, and dark mode theming under `apps/dashboard/`.
- **Infrastructure**: Core API and Dashboard can run via root `docker-compose.yml`.
- **Development**: See `docs/development.md` for full setup instructions, test commands, and architectural notes.
- **Zima OS / Homelab**: See `docs/zima-os.md` for LAN deployment instructions and SQLite backup tools (`scripts/backup-sqlite.sh`).

## Getting Started

1. Copy the example environment file:

   ```sh
   cp .env.example .env
   ```

2. Start via Docker (Recommended):

   ```sh
   docker compose up -d --build
   ```
   - Dashboard: http://localhost:3000
   - API: http://localhost:8000

3. Verify the API:

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

   Direct local runs store API data in `data/kairos-local.sqlite3` by default.

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
