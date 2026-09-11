"""Database session and engine configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=False)

SessionLocal = sessionmaker[Session](autocommit=False, autoflush=False, bind=engine)


def get_session() -> sessionmaker[Session]:
    """Return database session factory."""
    return SessionLocal
