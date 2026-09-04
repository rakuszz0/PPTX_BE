from sqlalchemy import event
from app.core.dependencies import Base, get_engine, SessionLocal
from app.database.models import (
    User, Workspace, Project, Course, Module, Presentation,
    PresentationVersion, Slide, Job, Asset, QAResult
)


def init_db() -> None:
    engine = get_engine()

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        if engine.url.drivername == "sqlite":
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


__all__ = ["init_db", "get_session"]
