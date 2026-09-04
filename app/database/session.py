from sqlalchemy import DateTime, inspect, text

from app.core.dependencies import Base, get_engine, SessionLocal
from app.database.models import (
    User, Workspace, Project, Course, Module, Presentation,
    PresentationVersion, Slide, Job, Asset, QAResult
)


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _upgrade_postgres_timestamps(engine)
    # ``create_all`` does not add indexes to tables that predate a model
    # change. Creating each declared index with ``checkfirst`` keeps startup
    # safe while also bringing an existing development database up to date.
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            index.create(bind=engine, checkfirst=True)


def _upgrade_postgres_timestamps(engine) -> None:
    """Migrate legacy UTC-naive timestamps to PostgreSQL timestamptz safely."""
    if engine.dialect.name != "postgresql":
        return

    inspector = inspect(engine)
    with engine.begin() as connection:
        for table in Base.metadata.tables.values():
            existing_columns = {column["name"]: column for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if not isinstance(column.type, DateTime) or not column.type.timezone:
                    continue
                existing = existing_columns.get(column.name)
                if existing is None or getattr(existing["type"], "timezone", False):
                    continue
                # All legacy values were produced by datetime.utcnow(), so
                # interpret them as UTC while converting the database type.
                connection.execute(text(
                    f'ALTER TABLE "{table.name}" ALTER COLUMN "{column.name}" '
                    f'TYPE TIMESTAMP WITH TIME ZONE USING "{column.name}" AT TIME ZONE \'UTC\''
                ))


def get_session():
    return SessionLocal()


__all__ = ["init_db", "get_session"]
