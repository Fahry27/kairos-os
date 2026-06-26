from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def create_db_and_tables() -> None:
    from app.db.session import engine
    from app.models import Memory, Project, Task  # noqa: F401

    Base.metadata.create_all(bind=engine)
