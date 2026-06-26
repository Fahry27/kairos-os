# Kairos Dashboard

Kairos Dashboard v0.1 is a read-only Next.js App Router app for viewing Kairos
Core API health, projects, tasks, and memories.

## Setup

```sh
npm install
```

## Run

```sh
npm run dev
```

The dashboard is available at:

```text
http://localhost:3000
```

By default it reads from:

```text
http://localhost:8000
```

Override the API URL if needed:

```sh
NEXT_PUBLIC_KAIROS_API_URL=http://localhost:8000 npm run dev
```

## Build

```sh
npm run build
```

## Environment Variables

Create `.env.local` from `.env.example` when you need local overrides:

```sh
cp .env.example .env.local
```

## Data Displayed

- API health from `GET /health`
- Projects from `GET /api/v1/projects`
- Tasks from `GET /api/v1/tasks`
- Memories from `GET /api/v1/memories`

The API must be running before the dashboard can load live data.
