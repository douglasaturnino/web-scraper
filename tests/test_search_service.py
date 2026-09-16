"""Search service tests."""

from sqlalchemy.orm import Session

from src.database.models.job_search import JobSearch
from src.database.models.job_search_provider import JobSearchProvider
from src.repositories.job_search_provider_repository import (
    JobSearchProviderRepository,
)
from src.repositories.search_repository import SearchRepository
from src.services.search_service import SearchService


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


def test_get_elegible_searches_returns_active(db: Session) -> None:
    """Verify only active searches are returned as elegible."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    service = SearchService(search_repo, provider_repo)

    db.add_all(
        [
            _build_search(keyword="python", active=True),
            _build_search(keyword="java", active=False),
        ]
    )
    db.commit()

    elegible = service.get_elegible_searches()

    assert len(elegible) == 1
    assert elegible[0].keyword == "python"


def test_get_elegible_searches_sorted_by_created_at(db: Session) -> None:
    """Verify elegible searches are sorted by creation date."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    service = SearchService(search_repo, provider_repo)

    older = _build_search(keyword="older")
    newer = _build_search(keyword="newer")
    db.add_all([older, newer])
    db.commit()

    elegible = service.get_elegible_searches()

    assert elegible[0].keyword == "older"


def test_get_providers_for_search(db: Session) -> None:
    """Verify providers for a search are returned."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    service = SearchService(search_repo, provider_repo)

    search = _build_search()
    db.add(search)
    db.commit()

    provider = JobSearchProvider(search_id=search.id, provider="linkedin", active=True)
    provider_repo.add(provider)

    providers = service.get_providers_for_search(search.id)

    assert len(providers) == 1
    assert providers[0].provider == "linkedin"


def test_is_search_elegible_with_active_providers(db: Session) -> None:
    """Verify search is elegible when it has active providers."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    service = SearchService(search_repo, provider_repo)

    search = _build_search()
    db.add(search)
    db.commit()

    provider_repo.add(
        JobSearchProvider(search_id=search.id, provider="linkedin", active=True)
    )

    assert service.is_search_elegible(search) is True


def test_is_search_elegible_inactive_search(db: Session) -> None:
    """Verify inactive search is not elegible."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    service = SearchService(search_repo, provider_repo)

    search = _build_search(active=False)
    db.add(search)
    db.commit()

    assert service.is_search_elegible(search) is False


def test_is_search_elegible_no_providers(db: Session) -> None:
    """Verify search with no providers is not elegible."""
    search_repo = SearchRepository(db)
    provider_repo = JobSearchProviderRepository(db)
    service = SearchService(search_repo, provider_repo)

    search = _build_search()
    db.add(search)
    db.commit()

    assert service.is_search_elegible(search) is False
