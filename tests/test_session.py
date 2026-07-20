"""Database session tests."""

from src.database.session import SessionLocal


def test_session_factory_returns_sessionmaker() -> None:
    """Verify session factory returns a callable sessionmaker."""
    session_factory = SessionLocal
    assert session_factory is not None
    assert callable(session_factory)
