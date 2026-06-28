import os
import tempfile
from pathlib import Path

TEST_DATABASE_PATH = Path(tempfile.gettempdir()) / "kairos-api-test.sqlite3"
if TEST_DATABASE_PATH.exists():
    TEST_DATABASE_PATH.unlink()

os.environ["CREATE_TABLES_ON_STARTUP"] = "true"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH}"
os.environ["USE_MOCK_DATA"] = "false"

from app.core.config import get_settings  # noqa: E402
get_settings.cache_clear()

from fastapi.testclient import TestClient  # noqa: E402

from app.db.base import initialize_database  # noqa: E402
from app.main import app  # noqa: E402

initialize_database()

client = TestClient(app)


def test_root_health():
    response = client.get("/health")

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "ok"
    assert res_data["service"] == "kairos-api"
    assert res_data["version"] == "2.1.0"
    assert "uptime" in res_data
    assert res_data["database"] in ("connected", "mock")
    assert "docker_mode" in res_data


def test_api_v1_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "ok"
    assert res_data["service"] == "kairos-api"
    assert res_data["version"] == "2.1.0"
    assert "uptime" in res_data
    assert res_data["database"] in ("connected", "mock")
    assert "docker_mode" in res_data


def test_health_allows_dashboard_origin():
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_database_initialization_seeds_default_data():
    # `session.py` builds its engine at *import time* from whatever DATABASE_URL
    # was in the environment when it was first imported. If another test module
    # (e.g. test_ai.py) was imported first, that engine points to a different
    # SQLite file. This test therefore constructs a *local* engine pointing
    # directly at TEST_DATABASE_PATH, runs the full initialization sequence on
    # it, and verifies both the file existence and the seeded data through that
    # engine — making the test completely order-independent.
    import sqlalchemy as sa
    from sqlalchemy import text
    from app.db.migrations import run_migrations
    from app.db.seed import seed_default_data_if_empty
    from app.db.base import Base
    from app.models import Memory, Project, Task  # noqa: F401

    url = f"sqlite:///{TEST_DATABASE_PATH}"
    local_engine = sa.create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=local_engine)
    run_migrations(local_engine)
    LocalSession = sa.orm.sessionmaker(autocommit=False, autoflush=False, bind=local_engine)
    with LocalSession() as db:
        seed_default_data_if_empty(db)

    # File must exist after initialization
    assert TEST_DATABASE_PATH.exists(), (
        f"Expected SQLite database at {TEST_DATABASE_PATH} after explicit initialization"
    )

    # Verify seeded data directly via SQLAlchemy (order-independent)
    with local_engine.connect() as conn:
        projects = conn.execute(text("SELECT name FROM projects")).fetchall()
        tasks = conn.execute(text("SELECT title FROM tasks")).fetchall()
        memories = conn.execute(text("SELECT type FROM memories")).fetchall()

    project_names = [r[0] for r in projects]
    task_titles = [r[0] for r in tasks]
    memory_types = [r[0] for r in memories]

    assert any(name == "Kairos OS" for name in project_names)
    assert any(title == "Connect Kairos Dashboard to the Core API" for title in task_titles)
    assert any(t == "technical_context" for t in memory_types)

    project_count = len(project_names)
    task_count = len(task_titles)
    memory_count = len(memory_types)

    # Re-seeding must be idempotent — no duplicate rows
    with LocalSession() as db:
        seed_default_data_if_empty(db)

    with local_engine.connect() as conn:
        assert len(conn.execute(text("SELECT 1 FROM projects")).fetchall()) == project_count
        assert len(conn.execute(text("SELECT 1 FROM tasks")).fetchall()) == task_count
        assert len(conn.execute(text("SELECT 1 FROM memories")).fetchall()) == memory_count

    local_engine.dispose()


def test_dashboard_read_endpoints_return_sqlite_data():
    created_project = client.post(
        "/api/v1/projects",
        json={
            "name": "SQLite Project",
            "description": "Created during API tests.",
            "priority": "high",
        },
    )
    assert created_project.status_code == 201
    project_id = created_project.json()["id"]

    created_task = client.post(
        "/api/v1/tasks",
        json={
            "project_id": project_id,
            "title": "Persist task in SQLite",
            "priority": "medium",
        },
    )
    assert created_task.status_code == 201

    created_memory = client.post(
        "/api/v1/memories",
        json={
            "type": "technical_context",
            "content": "Kairos API v0.3 stores local records in SQLite.",
            "tags": ["kairos", "sqlite"],
        },
    )
    assert created_memory.status_code == 201

    projects = client.get("/api/v1/projects")
    tasks = client.get("/api/v1/tasks")
    memories = client.get("/api/v1/memories")

    assert projects.status_code == 200
    assert any(project["name"] == "SQLite Project" for project in projects.json())

    assert tasks.status_code == 200
    assert any(task["title"] == "Persist task in SQLite" for task in tasks.json())

    assert memories.status_code == 200
    assert any(memory["type"] == "technical_context" for memory in memories.json())


def test_sqlite_project_crud_is_consistent():
    created = client.post(
        "/api/v1/projects",
        json={
            "name": "SQLite CRUD Project",
            "description": "Created during API tests.",
            "priority": "medium",
        },
    )

    assert created.status_code == 201
    project_id = created.json()["id"]

    listed = client.get("/api/v1/projects")
    assert any(project["id"] == project_id for project in listed.json())

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"status": "paused", "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "paused"
    assert updated.json()["priority"] == "low"

    deleted = client.delete(f"/api/v1/projects/{project_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/projects/{project_id}")
    assert missing.status_code == 404


def test_sqlite_task_crud_is_consistent():
    created = client.post(
        "/api/v1/tasks",
        json={
            "title": "SQLite CRUD Task",
            "description": "Created during API tests.",
            "priority": "medium",
        },
    )

    assert created.status_code == 201
    task_id = created.json()["id"]

    listed = client.get("/api/v1/tasks")
    assert any(task["id"] == task_id for task in listed.json())

    updated = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"status": "done", "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["priority"] == "low"

    deleted = client.delete(f"/api/v1/tasks/{task_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/tasks/{task_id}")
    assert missing.status_code == 404


def test_sqlite_memory_crud_is_consistent():
    created = client.post(
        "/api/v1/memories",
        json={
            "type": "note",
            "content": "SQLite CRUD memory.",
            "tags": ["sqlite", "test"],
            "importance": "normal",
        },
    )

    assert created.status_code == 201
    memory_id = created.json()["id"]

    listed = client.get("/api/v1/memories")
    assert any(memory["id"] == memory_id for memory in listed.json())

    updated = client.patch(
        f"/api/v1/memories/{memory_id}",
        json={"importance": "high", "tags": ["sqlite", "updated"]},
    )
    assert updated.status_code == 200
    assert updated.json()["importance"] == "high"
    assert updated.json()["tags"] == ["sqlite", "updated"]

    deleted = client.delete(f"/api/v1/memories/{memory_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/memories/{memory_id}")
    assert missing.status_code == 404


def test_startup_migration_adds_memories_project_id():
    """Simulate a pre-v0.7 DB lacking memories.project_id and ensure the
    migration adds it safely and is idempotent."""
    import sqlite3

    from app.db.migrations import run_migrations

    legacy_db = Path(tempfile.gettempdir()) / "kairos-migration-test.sqlite3"
    if legacy_db.exists():
        legacy_db.unlink()

    # Create a legacy memories table WITHOUT project_id
    conn = sqlite3.connect(str(legacy_db))
    conn.execute(
        """
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL DEFAULT 'note',
            content TEXT NOT NULL,
            source TEXT,
            tags TEXT,
            importance TEXT NOT NULL DEFAULT 'normal',
            created_at TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO memories (id, type, content, importance, created_at, updated_at) "
        "VALUES ('aaa', 'note', 'old memory', 'normal', '2026-01-01', '2026-01-01')"
    )
    conn.commit()
    conn.close()

    # Run the migration via SQLAlchemy engine
    from sqlalchemy import create_engine, text

    legacy_engine = create_engine(f"sqlite:///{legacy_db}")
    run_migrations(legacy_engine)

    # Column should now exist
    with legacy_engine.connect() as c:
        cols = {row[1] for row in c.execute(text("PRAGMA table_info(memories)"))}
        assert "project_id" in cols

        # Existing data should be intact
        row = c.execute(text("SELECT content FROM memories WHERE id = 'aaa'")).fetchone()
        assert row is not None
        assert row[0] == "old memory"

    # Running again should be a no-op (idempotent)
    run_migrations(legacy_engine)

    with legacy_engine.connect() as c:
        cols = {row[1] for row in c.execute(text("PRAGMA table_info(memories)"))}
        assert "project_id" in cols

    legacy_engine.dispose()
    legacy_db.unlink()

