# Kairos v1.0 Release Notes

Welcome to Kairos v1.0.0, the first stable local-first MVP release.

## Kairos v1.0.0
**Date:** June 2026

This release solidifies the foundation of Kairos OS as a local-first personal API and dashboard.

### Features
- **Local Persistence**: Data is saved directly to local SQLite databases without cloud requirements.
- **Projects, Tasks, and Memories**: Full CRUD capabilities for tracking work and context.
- **Search and Filter**: Client-side quick-filtering on text and descriptions.
- **Project Views (Deep Links)**: Focus the dashboard on a single project via `?project_id=<id>`.
- **Stats Overview**: Global and per-project stats, including a visual completion progress bar.
- **Accessibility & Theming**: Clean responsive layouts with Dark Mode support and keyboard navigation improvements.

## Historical Milestones Summary
- **v0.9**: Dashboard responsive polish and basic accessibility improvements.
- **v0.8**: Added dashboard stats overview with global and per-project metrics.
- **v0.7.1**: Fixed SQLite startup migration for `memories.project_id`.
- **v0.7**: Implemented project views and deep links.
- **v0.6**: Implemented simple client-side search and filters.
- **v0.5**: Added lightweight inline edit and delete actions.
- **v0.4**: Implemented lightweight create actions for dashboard.
- **v0.3**: Established persistent local SQLite storage.
- **v0.2**: Dockerized API development environment.
- **v0.1**: Initial foundation layout and FastAPI stub.

## Known Limitations
- Advanced state management or optimistic UI updates are minimal; the dashboard fetches fresh data after mutations.
- No remote sync or multi-user authentication in this local-first version.
- SQLite schema migrations are simple startup checks (not using Alembic yet).

## Next Recommended Milestone
**v1.1**: Dashboard UI polish, custom component refinement, and potentially introducing lightweight tag management or markdown rendering for memory content.
