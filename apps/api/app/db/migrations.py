"""Lightweight local-only schema migrations.

These run at startup before seeding and are idempotent.  They exist to
upgrade SQLite databases created by earlier Kairos versions without
requiring Alembic or a full migration framework.

Each migration function must be safe to call repeatedly: check first,
act only if needed.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy import Engine

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Individual migration steps
# ------------------------------------------------------------------


def _ensure_memories_project_id(engine: "Engine") -> None:
    """Add ``memories.project_id`` if the column does not exist (v0.7)."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"))
        if not result.fetchone():
            return
        result = conn.execute(text("PRAGMA table_info(memories)"))
        columns = {row[1] for row in result}

        if "project_id" not in columns:
            logger.info("Migration: adding memories.project_id column")
            conn.execute(text("ALTER TABLE memories ADD COLUMN project_id TEXT"))
            conn.commit()
        else:
            logger.debug("Migration: memories.project_id already exists — skipping")


def _migrate_projects_v340(engine: "Engine") -> None:
    """Add mission lifecycle columns to projects (v3.4.0)."""
    new_cols = {
        "trigger_kind": "TEXT",
        "trigger_source_id": "TEXT",
        "trigger_description": "TEXT",
        "context": "TEXT",
        "plans": "TEXT",
        "active_plan_version": "INTEGER",
        "approvals": "TEXT",
        "step_executions": "TEXT",
        "artifacts": "TEXT",
        "outcome": "TEXT",
        "triggered_at": "TEXT",
    }
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"))
        if not result.fetchone():
            logger.debug("Migration: projects table not found — skipping v3.4.0 migration")
            return
        result = conn.execute(text("PRAGMA table_info(projects)"))
        columns = {row[1] for row in result}
        for col_name, col_type in new_cols.items():
            if col_name not in columns:
                logger.info("Migration: adding projects.%s column", col_name)
                conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def _migrate_memories_v340(engine: "Engine") -> None:
    """Add title, visibility, status, is_pinned, source fields to memories (v3.4.0)."""
    new_cols = {
        "title": "TEXT",
        "visibility": "TEXT",
        "status": "TEXT DEFAULT 'active'",
    }
    nullable_cols = {
        "is_pinned": "INTEGER DEFAULT 0",
        "source_kind": "TEXT",
        "source_id": "TEXT",
        "source_label": "TEXT",
    }
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='memories'"))
        if not result.fetchone():
            logger.debug("Migration: memories table not found — skipping v3.4.0 migration")
            return
        result = conn.execute(text("PRAGMA table_info(memories)"))
        columns = {row[1] for row in result}
        for col_name, col_type in {**new_cols, **nullable_cols}.items():
            if col_name not in columns:
                logger.info("Migration: adding memories.%s column", col_name)
                conn.execute(text(f"ALTER TABLE memories ADD COLUMN {col_name} {col_type}"))
        conn.commit()


def _migrate_timeline_v340(engine: "Engine") -> None:
    """Create timeline_events table if it doesn't exist (v3.4.0)."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='timeline_events'"))
        if not result.fetchone():
            logger.info("Migration: creating timeline_events table")
            conn.execute(text("""
                CREATE TABLE timeline_events (
                    id TEXT PRIMARY KEY,
                    type VARCHAR(100) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    description TEXT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    actor_kind VARCHAR(50),
                    actor_id VARCHAR(255),
                    actor_label VARCHAR(255),
                    source_kind VARCHAR(50),
                    source_reference VARCHAR(255),
                    scope VARCHAR(50) DEFAULT 'global',
                    severity VARCHAR(50) DEFAULT 'info',
                    mission_id VARCHAR(255),
                    workspace_id VARCHAR(255),
                    memory_id VARCHAR(255),
                    decision_id VARCHAR(255),
                    attachments TEXT DEFAULT '[]',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        else:
            logger.debug("Migration: timeline_events table already exists — skipping")


def _migrate_workspace_v340(engine: "Engine") -> None:
    """Create workspace_states table if it doesn't exist (v3.4.0)."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='workspace_states'"))
        if not result.fetchone():
            logger.info("Migration: creating workspace_states table")
            conn.execute(text("""
                CREATE TABLE workspace_states (
                    id TEXT PRIMARY KEY,
                    goal VARCHAR(500) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    context TEXT DEFAULT '{}',
                    plan_json TEXT DEFAULT '[]',
                    decisions TEXT DEFAULT '[]',
                    notes TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        else:
            logger.debug("Migration: workspace_states table already exists — skipping")


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

_MIGRATIONS = [
    _ensure_memories_project_id,
    _migrate_projects_v340,
    _migrate_memories_v340,
    _migrate_timeline_v340,
    _migrate_workspace_v340,
]


def run_migrations(engine: "Engine") -> None:
    """Execute every registered migration against *engine*."""
    for migration in _MIGRATIONS:
        migration(engine)
