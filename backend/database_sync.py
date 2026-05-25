"""Synchronous SQLAlchemy session for Celery workers."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import get_settings


def _sync_database_url(async_url: str) -> str:
    if "+asyncpg" in async_url:
        return async_url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
    return async_url


settings = get_settings()
sync_engine = create_engine(_sync_database_url(settings.database_url), pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)


def get_sync_db() -> Generator[Session, None, None]:
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
