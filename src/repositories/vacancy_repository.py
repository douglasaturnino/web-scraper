"""Vacancy repository for persistence operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.vacancy import Vacancy


class VacancyRepository:
    """Repository for vacancy database operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session (Session): SQLAlchemy database session.
        """
        self._session = session

    def add(self, vacancy: Vacancy) -> Vacancy | None:
        """Persist a vacancy if it does not exist yet.

        Args:
            vacancy (Vacancy): Vacancy entity to persist.

        Returns:
            Vacancy | None: Persisted vacancy or None if a duplicate
            was found based on provider, external_id and url.
        """
        existing = self._session.scalar(
            select(Vacancy).where(
                Vacancy.provider == vacancy.provider,
                Vacancy.external_id == vacancy.external_id,
                Vacancy.url == vacancy.url,
            )
        )
        if existing is not None:
            return None
        self._session.add(vacancy)
        self._session.flush()
        return vacancy

    def get_by_external_id(self, external_id: str) -> Vacancy | None:
        """Retrieve vacancy by external identifier.

        Args:
            external_id (str): Provider external identifier.

        Returns:
            Vacancy | None: Found vacancy or None.
        """
        return self._session.scalar(
            select(Vacancy).where(Vacancy.external_id == external_id)
        )

    def get_by_provider_and_external_id(
        self, provider: str, external_id: str
    ) -> list[Vacancy]:
        """Retrieve vacancies by provider and external identifier.

        Args:
            provider (str): Provider name.
            external_id (str): Provider external identifier.

        Returns:
            list[Vacancy]: List of matching vacancies.
        """
        return list(
            self._session.scalars(
                select(Vacancy).where(
                    Vacancy.provider == provider,
                    Vacancy.external_id == external_id,
                )
            ).all()
        )

    def get_by_url(self, url: str) -> Vacancy | None:
        """Retrieve vacancy by URL.

        Args:
            url (str): Vacancy URL.

        Returns:
            Vacancy | None: Found vacancy or None.
        """
        return self._session.scalar(select(Vacancy).where(Vacancy.url == url))
