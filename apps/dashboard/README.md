# Kairos Dashboard

Kairos Dashboard v0.9 is a lightweight Next.js App Router app for viewing API
health and managing local projects, tasks, and memories.

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

## Features

- **Create**: Add new projects, tasks, and memories via the UI.
- **Edit**: Inline editing for all resources (toggles on click).
- **Delete**: Remove resources with a confirmation prompt.
- **Search & Filter**: Client-side filtering to quickly find and sort local data.
- **Project Views**: Focus the dashboard on a single project via `?project_id=` deep links to filter related tasks and memories automatically.
- **Stats & Overview**: A compact dashboard-wide stats panel showing project, task, and memory counts. When a project is focused, it shows linked task/memory counts and a visual completion progress bar.
- **Accessibility & Responsive Polish**: Improved layout for mobile devices, proper focus states for keyboard navigation, and ARIA labels for action buttons.

The API must be running before the dashboard can load live data.

