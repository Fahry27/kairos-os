# Kairos Dashboard

Kairos Dashboard v3.3.0 is a lightweight Next.js App Router app for viewing API
health, managing local projects, tasks, and memories, reviewing approvals, and
operating approved n8n workflow triggers and AI workspace planning.

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
- Approval requests from `GET /api/v1/approvals`
- Workflow run history from `GET /api/v1/workflow-runs`
- AI workspace data from `GET /api/v1/ai/provider-router/route`, `GET /api/v1/ai/provider-router/models`, `POST /api/v1/ai/provider-router/dispatch`, `POST /api/v1/ai/plan`, `POST /api/v1/ai/prompt/dry-run`, and `POST /api/v1/ai/parse-plan`

## Features

- **Create**: Add new projects, tasks, and memories via the UI.
- **Edit**: Inline editing for all resources (toggles on click).
- **Delete**: Remove resources with a confirmation prompt.
- **Search & Filter**: Client-side filtering to quickly find and sort local data.
- **Project Views**: Focus the dashboard on a single project via `?project_id=` deep links to filter related tasks and memories automatically.
- **Stats & Overview**: A compact dashboard-wide stats panel showing project, task, and memory counts. When a project is focused, it shows linked task/memory counts and a visual completion progress bar.
- **AI Workspace**: Enter goals, add optional context, choose a provider/model through the provider router, generate advisory plans, parse output, and optionally create approval requests.
- **Approval Management**: Inspect and decide pending approval requests without executing anything.
- **Operator Token**: Save `X-Kairos-Operator-Token` in browser `localStorage` only for protected approve, reject, and trigger actions.
- **Controlled n8n Trigger**: Trigger approved n8n workflow approvals and explicitly retry failed n8n triggers from the approval detail pane.
- **Workflow Run History**: Inspect sanitized run metadata and latest run status.
- **Accessibility & Responsive Polish**: Improved layout for mobile devices, proper focus states for keyboard navigation, and ARIA labels for action buttons.
- **Theming**: Dark mode support via CSS media queries.

The API must be running before the dashboard can load live data.
