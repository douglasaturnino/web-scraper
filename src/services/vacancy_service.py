"""Vacancy service for business rules."""

from typing import ClassVar

from loguru import logger

from src.database.models.vacancy import Vacancy
from src.repositories.vacancy_repository import VacancyRepository


class VacancyService:
    """Service responsible for vacancy business rules."""

    REQUIRED_FIELDS: ClassVar[list[str]] = [
        "provider",
        "external_id",
        "company",
        "title",
        "url",
        "state",
        "municipality",
        "description",
    ]

    def __init__(self, vacancy_repository: VacancyRepository) -> None:
        """Initialize service with repository.

        Args:
            vacancy_repository (VacancyRepository): Vacancy persistence.
        """
        self._vacancy_repository = vacancy_repository

    def validate_vacancy(self, vacancy: Vacancy) -> bool:
        """Validate required vacancy fields.

        Args:
            vacancy (Vacancy): Vacancy to validate.

        Returns:
            bool: True if vacancy is valid.
        """
        for field in self.REQUIRED_FIELDS:
            if not getattr(vacancy, field, None):
                logger.warning(
                    "Vacancy validation failed: missing {}",
                    field,
                )
                return False
        return True

    def save_vacancies(
        self, vacancies: list[Vacancy]
    ) -> tuple[list[Vacancy], list[Vacancy]]:
        """Persist vacancies, ignoring duplicates.

        Args:
            vacancies (list[Vacancy]): Vacancies to persist.

        Returns:
            tuple[list[Vacancy], list[Vacancy]]: Saved and ignored vacancies.
        """
        saved: list[Vacancy] = []
        ignored: list[Vacancy] = []

        for vacancy in vacancies:
            if not self.validate_vacancy(vacancy):
                ignored.append(vacancy)
                continue

            persisted = self._vacancy_repository.add(vacancy)
            if persisted is None:
                ignored.append(vacancy)
                logger.debug(
                    "Vacancy ignored as duplicate: {}",
                    vacancy.url,
                )
            else:
                saved.append(persisted)
                logger.debug(
                    "Vacancy persisted: {}",
                    vacancy.url,
                )

        logger.info(
            "Vacancies saved: {} | ignored: {}",
            len(saved),
            len(ignored),
        )
        return saved, ignored

    def get_unique_key(self, vacancy: Vacancy) -> tuple[str, str, str]:
        """Return the unique key for a vacancy.

        Args:
            vacancy (Vacancy): Vacancy to extract key from.

        Returns:
            tuple[str, str, str]: Unique key tuple.
        """
        return (vacancy.provider, vacancy.external_id, vacancy.url)
