"""Scheduler tests."""

from sqlalchemy.orm import Session

from src.database.models.job_search_provider import JobSearchProvider
from src.providers.factory import ProviderFactory
from src.repositories.job_search_provider_repository import (
    JobSearchProviderRepository,
)
from src.repositories.search_repository import SearchRepository
from src.repositories.vacancy_repository import VacancyRepository
from src.scheduler.scheduler import Scheduler
from src.services.scraper_service import ScraperService
from src.services.search_service import SearchService
from src.services.vacancy_service import VacancyService
from tests.test_scraper_service import _build_search, _build_vacancy


def test_scheduler_run_executes_active_searches(db: Session) -> None:
    """Verify scheduler run executes active searches."""
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
    factory = ProviderFactory()
    from tests.test_scraper_service import FakeProvider

    factory.register("linkedin", FakeProvider([vacancy]))
    scraper = ScraperService(search_service, vacancy_service, factory)
    scheduler = Scheduler(scraper)

    metrics = scheduler.run()

    assert metrics["searches"] == 1
    assert metrics["vacancies"] == 1


def test_scheduler_run_skips_inactive_searches(db: Session) -> None:
    """Verify scheduler run skips inactive searches."""
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

    scraper = ScraperService(search_service, vacancy_service, ProviderFactory())
    scheduler = Scheduler(scraper)

    metrics = scheduler.run()

    assert metrics["searches"] == 0
    assert metrics["vacancies"] == 0
