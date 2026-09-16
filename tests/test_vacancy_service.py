"""Vacancy service tests."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.database.models.vacancy import Vacancy
from src.repositories.vacancy_repository import VacancyRepository
from src.services.vacancy_service import VacancyService


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


def test_validate_vacancy_valid(db: Session) -> None:
    """Verify a valid vacancy passes validation."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy()

    assert service.validate_vacancy(vacancy) is True


def test_validate_vacancy_missing_provider(db: Session) -> None:
    """Verify validation fails when provider is missing."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy(provider="")

    assert service.validate_vacancy(vacancy) is False


def test_validate_vacancy_missing_description(db: Session) -> None:
    """Verify validation fails when description is missing."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy(description="")

    assert service.validate_vacancy(vacancy) is False


def test_save_vacancies_persists_new_vacancies(db: Session) -> None:
    """Verify new vacancies are persisted."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy()

    saved, ignored = service.save_vacancies([vacancy])

    assert len(saved) == 1
    assert len(ignored) == 0
    assert saved[0].url == vacancy.url


def test_save_vacancies_ignores_duplicates(db: Session) -> None:
    """Verify duplicate vacancies are ignored."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy()
    repo.add(vacancy)

    saved, ignored = service.save_vacancies([vacancy])

    assert len(saved) == 0
    assert len(ignored) == 1
    assert ignored[0].url == vacancy.url


def test_save_vacancies_ignores_invalid(db: Session) -> None:
    """Verify invalid vacancies are counted as ignored."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy(external_id="")

    saved, ignored = service.save_vacancies([vacancy])

    assert len(saved) == 0
    assert len(ignored) == 1
    assert ignored[0].external_id == ""


def test_save_vacancies_mixed(db: Session) -> None:
    """Verify save handles valid, invalid and duplicate vacancies."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    existing = _build_vacancy(url="https://linkedin.com/jobs/view/1")
    repo.add(existing)
    new = _build_vacancy(url="https://linkedin.com/jobs/view/2")
    invalid = _build_vacancy(title="")
    duplicate = _build_vacancy(url="https://linkedin.com/jobs/view/1")

    saved, ignored = service.save_vacancies([new, invalid, duplicate])

    assert len(saved) == 1
    assert saved[0].url == new.url
    assert len(ignored) == 2


def test_get_unique_key(db: Session) -> None:
    """Verify unique key extraction."""
    repo = VacancyRepository(db)
    service = VacancyService(repo)
    vacancy = _build_vacancy()

    key = service.get_unique_key(vacancy)

    assert key == ("linkedin", "ext-123", "https://linkedin.com/jobs/view/123")
