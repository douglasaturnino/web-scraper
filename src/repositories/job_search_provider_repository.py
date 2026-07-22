"""JobSearchProvider repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.job_search_provider import JobSearchProvider


class JobSearchProviderRepository:
    """Repository for job search provider persistence operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session (Session): SQLAlchemy database session.
        """
        self._session = session

    def add(self, job_search_provider: JobSearchProvider) -> JobSearchProvider:
        """Persist a job search provider association.

        Args:
            job_search_provider (JobSearchProvider): Association to persist.

        Returns:
            JobSearchProvider: Persisted association.
        """
        self._session.add(job_search_provider)
        self._session.flush()
        return job_search_provider

    def get_by_search_id(self, search_id: UUID) -> list[JobSearchProvider]:
        """Retrieve provider associations by search identifier.

        Args:
            search_id (UUID): Job search identifier.

        Returns:
            list[JobSearchProvider]: List of provider associations.
        """
        return list(
            self._session.scalars(
                select(JobSearchProvider).where(
                    JobSearchProvider.search_id == search_id
                )
            ).all()
        )

    def get_active_providers(self) -> list[JobSearchProvider]:
        """Retrieve all active provider associations.

        Returns:
            list[JobSearchProvider]: List of active provider associations.
        """
        return list(
            self._session.scalars(
                select(JobSearchProvider).where(JobSearchProvider.active.is_(True))
            ).all()
        )
