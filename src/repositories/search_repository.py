"""Search repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models.job_search import JobSearch


class SearchRepository:
    """Repository for job search persistence operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository with database session.

        Args:
            session (Session): SQLAlchemy database session.
        """
        self._session = session

    def get_all_active(self) -> list[JobSearch]:
        """Retrieve all active job searches.

        Returns:
            list[JobSearch]: List of active job searches.
        """
        return list(
            self._session.scalars(
                select(JobSearch).where(JobSearch.active.is_(True))
            ).all()
        )

    def get_by_id(self, search_id: UUID) -> JobSearch | None:
        """Retrieve job search by identifier.

        Args:
            search_id (UUID): Job search identifier.

        Returns:
            JobSearch | None: Found job search or None.
        """
        return self._session.scalar(select(JobSearch).where(JobSearch.id == search_id))

    def get_by_status(self, active: bool) -> list[JobSearch]:
        """Retrieve job searches by status.

        Args:
            active (bool): Active status filter.

        Returns:
            list[JobSearch]: List of job searches matching the status.
        """
        return list(
            self._session.scalars(
                select(JobSearch).where(JobSearch.active == active)
            ).all()
        )
