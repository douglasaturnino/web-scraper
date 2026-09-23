"""Database session tests."""

from src.database.session import SessionLocal, get_session


def test_session_factory_returns_sessionmaker() -> None:
    """Verify session factory returns a callable sessionmaker."""
    session_factory = SessionLocal
    assert session_factory is not None
    assert callable(session_factory)


def test_get_session_returns_sessionmaker() -> None:
    """Verify get_session returns the session factory."""
    session_factory = get_session()
    assert session_factory is SessionLocal
    assert callable(session_factory)
