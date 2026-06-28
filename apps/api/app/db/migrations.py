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
        result = conn.execute(text("PRAGMA table_info(memories)"))
        columns = {row[1] for row in result}

        if "project_id" not in columns:
            logger.info("Migration: adding memories.project_id column")
            conn.execute(text("ALTER TABLE memories ADD COLUMN project_id TEXT"))
            conn.commit()
        else:
            logger.debug("Migration: memories.project_id already exists — skipping")


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------

_MIGRATIONS = [
    _ensure_memories_project_id,
]


def run_migrations(engine: "Engine") -> None:
    """Execute every registered migration against *engine*."""
    for migration in _MIGRATIONS:
        migration(engine)
