from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def create_db_and_tables() -> None:
    from app.db.session import engine
    from app.models import Approval, DecisionPlan, Memory, Project, Task, TimelineEvent, WorkspaceState, WorkflowRun  # noqa: F401

    Base.metadata.create_all(bind=engine)


def initialize_database() -> None:
    from app.db.migrations import run_migrations
    from app.db.seed import seed_default_data_if_empty
    from app.db.session import SessionLocal, engine

    create_db_and_tables()
    run_migrations(engine)
    with SessionLocal() as db:
        seed_default_data_if_empty(db)
