"""Database model tests."""

from datetime import datetime

from src.database.models.job_search import JobSearch
from src.database.models.vacancy import Vacancy


def test_job_search_defaults() -> None:
    """Verify JobSearch model default field values."""
    job_search = JobSearch(
        keyword="python",
        state="SP",
        municipality="São Paulo",
        remote=False,
        active=True,
    )
    assert job_search.keyword == "python"
    assert job_search.state == "SP"
    assert job_search.municipality == "São Paulo"
    assert job_search.remote is False
    assert job_search.active is True


def test_vacancy_defaults() -> None:
    """Verify Vacancy model default field values."""
    vacancy = Vacancy(
        provider="gupy",
        external_id="123",
        company="Test Corp",
        title="Python Developer",
        url="https://example.com",
        publication_date=datetime.now(),
        state="SP",
        municipality="São Paulo",
        description="Test description",
    )
    assert vacancy.provider == "gupy"
    assert vacancy.external_id == "123"
    assert vacancy.company == "Test Corp"
    assert vacancy.title == "Python Developer"
    assert vacancy.url == "https://example.com"
    assert vacancy.state == "SP"
    assert vacancy.municipality == "São Paulo"
    assert vacancy.description == "Test description"
