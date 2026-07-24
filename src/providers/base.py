"""Base provider protocol definition."""

from typing import Protocol, runtime_checkable

from src.database.models.vacancy import Vacancy


@runtime_checkable
class BaseProvider(Protocol):
    """Provider interface for collection orchestration."""

    def search(
        self, keyword: str, state: str, municipality: str, remote: bool
    ) -> list[Vacancy]:
        """Search vacancies.

        Args:
            keyword (str): Search keyword.
            state (str): State filter.
            municipality (str): Municipality filter.
            remote (bool): Remote vacancy filter.

        Returns:
            list[Vacancy]: Found vacancies.
        """

    def get_job(self, url: str) -> Vacancy | None:
        """Get a single vacancy by URL.

        Args:
            url (str): Vacancy URL.

        Returns:
            Vacancy | None: Found vacancy or None.
        """
