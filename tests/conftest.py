"""Shared fixtures for tests."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.base import Base

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker[Session](
    bind=engine, autocommit=False, autoflush=False
)


@pytest.fixture(scope="session", autouse=True)
def _setup_database() -> Generator[None]:
    """Create database schema for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db() -> Generator[Session]:
    """Return an isolated database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
