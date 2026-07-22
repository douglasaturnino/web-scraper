"""JobSearchProvider repository tests."""

import uuid

from sqlalchemy.orm import Session

from src.database.models.job_search_provider import JobSearchProvider
from src.repositories.job_search_provider_repository import JobSearchProviderRepository


def _build_association(
    search_id: uuid.UUID | None = None, **kwargs: bool | str
) -> JobSearchProvider:
    """Build a provider association with default values."""
    defaults: dict[str, bool | str | uuid.UUID] = {
        "search_id": search_id or uuid.uuid4(),
        "provider": "linkedin",
        "active": True,
    }
    defaults.update(kwargs)
    return JobSearchProvider(**defaults)


def test_add_job_search_provider(db: Session) -> None:
    """Verify adding a provider association."""
    repo = JobSearchProviderRepository(db)
    association = _build_association()

    result = repo.add(association)

    assert result.id is not None
    assert result.provider == "linkedin"


def test_get_by_search_id(db: Session) -> None:
    """Verify retrieval of providers by search id."""
    repo = JobSearchProviderRepository(db)
    search_id = uuid.uuid4()
    db.add_all(
        [
            _build_association(search_id=search_id, provider="linkedin"),
            _build_association(search_id=uuid.uuid4(), provider="gupy"),
        ]
    )
    db.commit()

    results = repo.get_by_search_id(search_id)

    assert len(results) == 1
    assert results[0].provider == "linkedin"


def test_get_active_providers(db: Session) -> None:
    """Verify only active provider associations are returned."""
    repo = JobSearchProviderRepository(db)
    db.add_all(
        [
            _build_association(provider="linkedin", active=True),
            _build_association(provider="gupy", active=False),
        ]
    )
    db.commit()

    results = repo.get_active_providers()

    assert len(results) == 1
    assert results[0].provider == "linkedin"
