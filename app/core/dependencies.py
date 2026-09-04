from typing import Generator, Optional
from contextvars import ContextVar

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.core.config import get_settings
from app.core.security import DevelopmentAuthProvider

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

Base = declarative_base()


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_provider() -> DevelopmentAuthProvider:
    return DevelopmentAuthProvider()
