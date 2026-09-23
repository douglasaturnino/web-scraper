"""API endpoint tests."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.base import Base
from src.database.models.job_search import JobSearch
from src.database.models.job_search_provider import JobSearchProvider
from src.main import app

client = TestClient(app)


def _in_memory_session_factory() -> sessionmaker[Session]:
    """Return a sessionmaker bound to a fresh in-memory database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker[Session](bind=engine, autocommit=False, autoflush=False)


def test_health_check() -> None:
    """Verify health endpoint returns healthy status."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = ""
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_metrics_endpoint() -> None:
    """Verify metrics endpoint returns provider metrics."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = ""
        response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data


def test_run_scheduler_endpoint() -> None:
    """Verify scheduler endpoint returns execution metrics."""
    mock_metrics = {"searches": 1, "vacancies": 2}
    with (
        patch("src.api.scraper._build_scraper_service") as mock_build,
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        mock_scraper = MagicMock()
        mock_scraper.run_scheduler.return_value = mock_metrics
        mock_build.return_value = (mock_scraper, MagicMock())

        response = client.post("/scraper/run")
        assert response.status_code == 200
        assert response.json() == mock_metrics


def test_search_by_provider_endpoint() -> None:
    """Verify search-by-provider endpoint executes a search."""
    mock_vacancies = [
        MagicMock(url="https://example.com/job/1"),
        MagicMock(url="https://example.com/job/2"),
        MagicMock(url="https://example.com/job/3"),
    ]
    with (
        patch("src.api.scraper._build_scraper_service") as mock_build,
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        mock_scraper = MagicMock()
        mock_scraper.execute_search.return_value = mock_vacancies
        mock_build.return_value = (mock_scraper, MagicMock())

        response = client.post(
            "/scraper/search",
            json={
                "provider": "linkedin",
                "keyword": "python",
                "state": "SP",
                "municipality": "São Paulo",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "linkedin"
        assert data["vacancies_found"] == 3


def test_search_by_provider_invalid_provider() -> None:
    """Verify search-by-provider handles unknown provider gracefully."""
    with (
        patch("src.api.scraper._build_scraper_service") as mock_build,
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        mock_scraper = MagicMock()
        mock_scraper.execute_search.return_value = []
        mock_build.return_value = (mock_scraper, MagicMock())

        response = client.post(
            "/scraper/search",
            json={
                "provider": "unknown",
                "keyword": "python",
                "state": "SP",
                "municipality": "São Paulo",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vacancies_found"] == 0


def test_search_by_url_endpoint() -> None:
    """Verify URL search endpoint returns persisted vacancy data."""
    mock_vacancy = MagicMock()
    mock_vacancy.id = "test-uuid"
    mock_vacancy.provider = "linkedin"
    mock_vacancy.title = "Python Developer"
    mock_vacancy.company = "Acme Corp"
    mock_vacancy.url = "https://www.linkedin.com/jobs/view/123"
    mock_vacancy.state = "SP"
    mock_vacancy.municipality = "São Paulo"

    with (
        patch("src.api.scraper._build_scraper_service") as mock_build,
        patch("src.api.scraper.ManualQueue") as mock_queue_cls,
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        mock_queue = MagicMock()
        mock_queue.process_all.return_value = [mock_vacancy]
        mock_queue_cls.return_value = mock_queue

        mock_scraper = MagicMock()
        mock_build.return_value = (mock_scraper, MagicMock())

        response = client.post(
            "/scraper/url",
            json={"url": "https://www.linkedin.com/jobs/view/123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "linkedin"
        assert data["title"] == "Python Developer"


def test_search_by_url_unsupported_provider() -> None:
    """Verify URL search endpoint returns 400 for unsupported domain."""
    with (
        patch("src.api.scraper._build_scraper_service") as mock_build,
        patch("src.api.scraper.ManualQueue") as mock_queue_cls,
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        mock_queue = MagicMock()
        mock_queue.process_all.return_value = []
        mock_queue_cls.return_value = mock_queue

        mock_scraper = MagicMock()
        mock_build.return_value = (mock_scraper, MagicMock())

        response = client.post(
            "/scraper/url",
            json={"url": "https://www.example.com/jobs/view/123"},
        )
        assert response.status_code == 400


def test_create_search_endpoint() -> None:
    """Verify create_search endpoint persists a new search."""
    factory = _in_memory_session_factory()
    with (
        patch("src.api.scraper.SessionLocal", factory),
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""

        response = client.post(
            "/scraper/search/create",
            json={
                "provider": "linkedin",
                "keyword": "python",
                "state": "SP",
                "municipality": "São Paulo",
                "active": True,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "linkedin"
    assert data["keyword"] == "python"
    assert data["state"] == "SP"
    assert data["municipality"] == "São Paulo"
    assert data["active"] is True
    assert "id" in data

    with factory() as session:
        search = session.scalar(select(JobSearch))
        provider = session.scalar(select(JobSearchProvider))
        assert search is not None
        assert provider is not None
        assert provider.search_id == search.id


def test_create_search_single_transaction() -> None:
    """Verify search and provider persist atomically in a single commit."""
    commits: list[int] = []

    class CountingSession(Session):
        """Session subclass that records each commit."""

        def commit(self) -> None:
            """Record the commit before delegating to the parent session."""
            commits.append(1)
            super().commit()

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker[Session](
        bind=engine, class_=CountingSession, autocommit=False, autoflush=False
    )

    with (
        patch("src.api.scraper.SessionLocal", factory),
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        response = client.post(
            "/scraper/search/create",
            json={
                "provider": "gupy",
                "keyword": "python",
                "state": "SP",
                "municipality": "São Paulo",
                "active": True,
            },
        )

    assert response.status_code == 200
    assert len(commits) == 1  # one transaction, not two

    with factory() as session:
        search = session.scalar(select(JobSearch))
        provider = session.scalar(select(JobSearchProvider))
        assert search is not None
        assert provider is not None
        assert provider.search_id == search.id


def test_create_search_rolls_back_on_failure() -> None:
    """Verify a failed commit rolls back and persists no rows."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    class FailingSession(Session):
        """Session subclass whose commit always raises."""

        def commit(self) -> None:
            """Raise to simulate a database failure."""
            raise RuntimeError("simulated commit failure")

    factory = sessionmaker[Session](
        bind=engine, class_=FailingSession, autocommit=False, autoflush=False
    )

    failing_client = TestClient(app, raise_server_exceptions=False)
    with (
        patch("src.api.scraper.SessionLocal", factory),
        patch("src.config.security.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = ""
        response = failing_client.post(
            "/scraper/search/create",
            json={
                "provider": "gupy",
                "keyword": "python",
                "state": "SP",
                "municipality": "São Paulo",
                "active": True,
            },
        )

    assert response.status_code == 500
    with factory() as session:
        assert session.scalar(select(JobSearch)) is None
        assert session.scalar(select(JobSearchProvider)) is None
