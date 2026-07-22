"""Vacancy repository tests."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.database.models.vacancy import Vacancy
from src.repositories.vacancy_repository import VacancyRepository


def _build_vacancy(**kwargs: str | datetime) -> Vacancy:
    """Build a vacancy with default values."""
    defaults: dict[str, str | datetime] = {
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


def test_add_vacancy_returns_persisted(db: Session) -> None:
    """Verify add persists a new vacancy."""
    repo = VacancyRepository(db)
    vacancy = _build_vacancy()

    result = repo.add(vacancy)

    assert result is not None
    assert result.id is not None
    assert result.provider == "linkedin"
    assert result.external_id == "ext-123"


def test_add_vacancy_duplicate_ignored(db: Session) -> None:
    """Verify duplicate vacancies are ignored based on unique fields."""
    repo = VacancyRepository(db)
    vacancy = _build_vacancy()
    repo.add(vacancy)

    duplicate = _build_vacancy()
    result = repo.add(duplicate)

    assert result is None


def test_get_by_external_id(db: Session) -> None:
    """Verify vacancy retrieval by external_id."""
    repo = VacancyRepository(db)
    vacancy = _build_vacancy(external_id="ext-456")
    repo.add(vacancy)

    result = repo.get_by_external_id("ext-456")

    assert result is not None
    assert result.external_id == "ext-456"


def test_get_by_external_id_not_found(db: Session) -> None:
    """Verify None returned when external_id does not exist."""
    repo = VacancyRepository(db)

    result = repo.get_by_external_id("missing")

    assert result is None


def test_get_by_url(db: Session) -> None:
    """Verify vacancy retrieval by URL."""
    repo = VacancyRepository(db)
    vacancy = _build_vacancy(url="https://example.com/vacancy")
    repo.add(vacancy)

    result = repo.get_by_url("https://example.com/vacancy")

    assert result is not None
    assert result.url == "https://example.com/vacancy"


def test_get_by_url_not_found(db: Session) -> None:
    """Verify None returned when URL does not exist."""
    repo = VacancyRepository(db)

    result = repo.get_by_url("https://example.com/missing")

    assert result is None


def test_get_by_provider_and_external_id(db: Session) -> None:
    """Verify vacancy retrieval by provider and external_id."""
    repo = VacancyRepository(db)
    vacancy = _build_vacancy(provider="gupy", external_id="gupy-123")
    repo.add(vacancy)

    results = repo.get_by_provider_and_external_id("gupy", "gupy-123")

    assert len(results) == 1
    assert results[0].provider == "gupy"
