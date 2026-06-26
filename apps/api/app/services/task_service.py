from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def list_tasks(db: Session, offset: int = 0, limit: int = 100) -> list[Task]:
    statement = select(Task).offset(offset).limit(limit).order_by(Task.created_at.desc())
    return list(db.scalars(statement).all())


def get_task(db: Session, task_id: UUID) -> Task | None:
    return db.get(Task, task_id)


def create_task(db: Session, payload: TaskCreate) -> Task:
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, task: Task, payload: TaskUpdate) -> Task:
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()
