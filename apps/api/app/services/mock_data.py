from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

KAIROS_PROJECT_ID = "5159d21b-e03c-43d1-b1a2-dac2a01d51fb"
KAIROS_TASK_ID = "59c9bf24-21cd-48be-ad9d-3aeb74b2b299"
KAIROS_MEMORY_ID = "c2228dd7-4718-4d28-8469-47b59b83ac8d"
MOCK_TIMESTAMP = "2026-06-27T00:00:00Z"


PROJECTS = [
    {
        "id": KAIROS_PROJECT_ID,
        "name": "Kairos OS",
        "description": (
            "Local-first personal AI operating system for projects, memory, "
            "knowledge, and automation."
        ),
        "status": "active",
        "priority": "high",
        "created_at": MOCK_TIMESTAMP,
        "updated_at": MOCK_TIMESTAMP,
    }
]


def current_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def list_records(records: list[dict[str, Any]], offset: int, limit: int) -> list[dict[str, Any]]:
    return deepcopy(records[offset : offset + limit])


def get_record(records: list[dict[str, Any]], record_id: UUID) -> dict[str, Any] | None:
    for record in records:
        if record["id"] == str(record_id):
            return record
    return None


def create_record(records: list[dict[str, Any]], payload: Any) -> dict[str, Any]:
    now = current_timestamp()
    record = payload.model_dump(mode="json")
    record.update(
        {
            "id": str(uuid4()),
            "created_at": now,
            "updated_at": now,
        }
    )
    records.append(record)
    return deepcopy(record)


def update_record(record: dict[str, Any], payload: Any) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True, mode="json")
    record.update(updates)
    record["updated_at"] = current_timestamp()
    return deepcopy(record)


def delete_record(records: list[dict[str, Any]], record: dict[str, Any]) -> None:
    records.remove(record)


TASKS = [
    {
        "id": KAIROS_TASK_ID,
        "project_id": KAIROS_PROJECT_ID,
        "title": "Connect Kairos Dashboard to the Core API",
        "description": "Serve local-first dashboard data through FastAPI.",
        "status": "todo",
        "priority": "high",
        "due_date": None,
        "created_at": MOCK_TIMESTAMP,
        "updated_at": MOCK_TIMESTAMP,
    }
]

MEMORIES = [
    {
        "id": KAIROS_MEMORY_ID,
        "project_id": KAIROS_PROJECT_ID,
        "title": "Kairos Dashboard API Context",
        "type": "reference",
        "content": (
            "Kairos Dashboard v0.2 reads health, projects, tasks, and memories "
            "from the local FastAPI service."
        ),
        "source_kind": "system",
        "source_id": None,
        "source_label": "kairos-api",
        "tags": ["kairos", "dashboard", "api"],
        "importance": "high",
        "visibility": "mission",
        "status": "active",
        "is_pinned": True,
        "created_at": MOCK_TIMESTAMP,
        "updated_at": MOCK_TIMESTAMP,
    }
]

TIMELINE_EVENTS: list[dict[str, object]] = []
WORKSPACES: list[dict[str, object]] = []
