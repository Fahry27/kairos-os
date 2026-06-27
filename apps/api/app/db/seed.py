from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.project import Project
from app.models.task import Task
from app.services import mock_data


def parse_seed_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def database_has_records(db: Session) -> bool:
    project_count = db.scalar(select(func.count()).select_from(Project)) or 0
    task_count = db.scalar(select(func.count()).select_from(Task)) or 0
    memory_count = db.scalar(select(func.count()).select_from(Memory)) or 0
    return project_count + task_count + memory_count > 0


def seed_default_data_if_empty(db: Session) -> None:
    if database_has_records(db):
        return

    projects = [
        Project(
            id=UUID(project["id"]),
            name=project["name"],
            description=project["description"],
            status=project["status"],
            priority=project["priority"],
            created_at=parse_seed_datetime(project["created_at"]),
            updated_at=parse_seed_datetime(project["updated_at"]),
        )
        for project in mock_data.PROJECTS
    ]
    tasks = [
        Task(
            id=UUID(task["id"]),
            project_id=UUID(task["project_id"]) if task["project_id"] else None,
            title=task["title"],
            description=task["description"],
            status=task["status"],
            priority=task["priority"],
            due_date=parse_seed_datetime(task["due_date"]) if task["due_date"] else None,
            created_at=parse_seed_datetime(task["created_at"]),
            updated_at=parse_seed_datetime(task["updated_at"]),
        )
        for task in mock_data.TASKS
    ]
    memories = [
        Memory(
            id=UUID(memory["id"]),
            type=memory["type"],
            content=memory["content"],
            source=memory["source"],
            tags=memory["tags"],
            importance=memory["importance"],
            created_at=parse_seed_datetime(memory["created_at"]),
            updated_at=parse_seed_datetime(memory["updated_at"]),
        )
        for memory in mock_data.MEMORIES
    ]

    db.add_all([*projects, *tasks, *memories])
    db.commit()
