"""Scraper service tests."""

from typing import Any

from sqlalchemy.orm import Session

from src.database.models.job_search import JobSearch
from src.database.models.job_search_provider import JobSearchProvider
from src.database.models.vacancy import Vacancy
from src.providers.base import BaseProvider
from src.repositories.job_search_provider_repository import (
    JobSearchProviderRepository,
)
from src.repositories.search_repository import SearchRepository
from src.repositories.vacancy_repository import VacancyRepository
from src.services.scraper_service import ScraperService
from src.services.search_service import SearchService
from src.services.vacancy_service import VacancyService


def _build_search(**kwargs: bool | str) -> JobSearch:
    """Build a job search with default values."""
    defaults: dict[str, bool | str] = {
        "keyword": "python",
        "state": "SP",
        "municipality": "São Paulo",
        "remote": False,
        "active": True,
    }
    defaults.update(kwargs)
    return JobSearch(**defaults)


class FakeProvider(BaseProvider):
    """Fake provider for tests."""

    def __init__(self, vacancies: list[Vacancy]) -> None:
        """Initialize with fake vacancies."""
        self._vacancies = vacancies

    def search(self, keyword: str, state: str, municipality: str) -> list[Vacancy]:
        """Return fake vacancies."""
        return self._vacancies

    def get_job(self, url: str) -> Vacancy | None:
        """Return a single fake vacancy."""
        return self._vacancies[0] if self._vacancies else None

    def normalize(self, raw_data: dict[str, object]) -> Vacancy:
        """Return the first fake vacancy."""
        return self._vacancies[0] if self._vacancies else _build_vacancy()


def _build_vacancy(**kwargs: str | Any) -> Vacancy:
    """Build a vacancy with default values."""
    from datetime import UTC, datetime

    defaults: dict[str, Any] = {
        "provider": "linkedin",
        "external_id": "ext-123",
        "company": "Acme Corp",
        "title": "Python Developer",
        "url": "https://linkedin.com/jobs/view/123",
        "publication_date": datetime.now(UTC),
        "state": "SP",
        "municipality": "São Paulo",
        "description": "Test description",
    }
    defaults.update(kwargs)
    return Vacancy(**defaults)


def test_execute_search_persists_vacancies(db: Session) -> None:
    """Verify execute_search persists vacancies from a provider."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    search = _build_search()
    db.add(search)
    db.commit()

    vacancy = _build_vacancy()
    providers = {"linkedin": FakeProvider([vacancy])}
    scraper = ScraperService(search_service, vacancy_service, providers)

    provider_repo.add(
        JobSearchProvider(search_id=search.id, provider="linkedin", active=True)
    )

    saved = scraper.execute_search(search, "linkedin")

    assert len(saved) == 1
    assert saved[0].url == vacancy.url


def test_execute_search_handles_missing_provider(db: Session) -> None:
    """Verify execute_search handles missing provider gracefully."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    search = _build_search()
    scraper = ScraperService(search_service, vacancy_service, {})

    saved = scraper.execute_search(search, "unknown")

    assert saved == []


def test_execute_search_handles_provider_error(db: Session) -> None:
    """Verify execute_search handles provider exceptions gracefully."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    class ErrorProvider(BaseProvider):
        def search(self, keyword: str, state: str, municipality: str) -> list[Vacancy]:
            raise RuntimeError("Provider failed")

        def get_job(self, url: str) -> Vacancy | None:
            return None

        def normalize(self, raw_data: dict[str, object]) -> Vacancy:
            raise RuntimeError("Provider failed")

    search = _build_search()
    providers = {"linkedin": ErrorProvider()}
    scraper = ScraperService(search_service, vacancy_service, providers)

    saved = scraper.execute_search(search, "linkedin")

    assert saved == []


def test_execute_by_url_persists_vacancy(db: Session) -> None:
    """Verify execute_by_url persists a single vacancy."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    vacancy = _build_vacancy(url="https://linkedin.com/jobs/view/999")
    providers = {"linkedin": FakeProvider([vacancy])}
    scraper = ScraperService(search_service, vacancy_service, providers)

    result = scraper.execute_by_url("https://linkedin.com/jobs/view/999", "linkedin")

    assert result is not None
    assert result.url == vacancy.url


def test_execute_by_url_returns_none_for_missing_provider(db: Session) -> None:
    """Verify execute_by_url returns None for unknown provider."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    scraper = ScraperService(search_service, vacancy_service, {})

    result = scraper.execute_by_url("https://linkedin.com/jobs/view/999", "unknown")

    assert result is None


def test_run_scheduler_executes_elegible_searches(db: Session) -> None:
    """Verify run_scheduler executes elegible searches."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    search = _build_search(keyword="python", active=True)
    db.add(search)
    db.commit()

    provider_repo.add(
        JobSearchProvider(search_id=search.id, provider="linkedin", active=True)
    )

    vacancy = _build_vacancy()
    providers = {"linkedin": FakeProvider([vacancy])}
    scraper = ScraperService(search_service, vacancy_service, providers)

    metrics = scraper.run_scheduler()

    assert metrics["searches"] == 1
    assert metrics["vacancies"] == 1


def test_run_scheduler_skips_inactive_searches(db: Session) -> None:
    """Verify run_scheduler skips inactive searches."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    vacancy_repo = VacancyRepository(db)
    search_service = SearchService(search_repo, provider_repo)
    vacancy_service = VacancyService(vacancy_repo)

    search = _build_search(keyword="python", active=False)
    db.add(search)
    db.commit()

    provider_repo.add(
        JobSearchProvider(search_id=search.id, provider="linkedin", active=True)
    )

    scraper = ScraperService(search_service, vacancy_service, {})

    metrics = scraper.run_scheduler()

    assert metrics["searches"] == 0
    assert metrics["vacancies"] == 0
