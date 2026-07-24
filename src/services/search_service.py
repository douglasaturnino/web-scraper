"""Search service for business rules."""

from uuid import UUID

from src.database.models.job_search import JobSearch
from src.database.models.job_search_provider import JobSearchProvider
from src.repositories.job_search_provider_repository import (
    JobSearchProviderRepository,
)
from src.repositories.search_repository import SearchRepository


class SearchService:
    """Service responsible for search business rules."""

    def __init__(
        self,
        search_repository: SearchRepository,
        job_search_provider_repository: JobSearchProviderRepository,
    ) -> None:
        """Initialize service with repositories.

        Args:
            search_repository (SearchRepository): Search persistence.
            job_search_provider_repository (JobSearchProviderRepository):
                Search-provider association persistence.
        """
        self._search_repository = search_repository
        self._provider_repository = job_search_provider_repository

    def get_elegible_searches(self) -> list[JobSearch]:
        """Return active searches sorted by creation date.

        Returns:
            list[JobSearch]: Sorted active searches.
        """
        searches = self._search_repository.get_all_active()
        return sorted(searches, key=lambda search: search.created_at)

    def get_providers_for_search(self, search_id: UUID) -> list[JobSearchProvider]:
        """Return active providers associated with a search.

        Args:
            search_id (UUID): Job search identifier.

        Returns:
            list[JobSearchProvider]: List of active provider associations.
        """
        return self._provider_repository.get_by_search_id(search_id)

    def is_search_elegible(self, search: JobSearch) -> bool:
        """Check if a search is eligible for execution.

        Args:
            search (JobSearch): Job search to validate.

        Returns:
            bool: True if search can be executed.
        """
        if not search.active:
            return False

        providers = self._provider_repository.get_by_search_id(search.id)
        if not providers:
            return False

        return any(provider.active for provider in providers)
