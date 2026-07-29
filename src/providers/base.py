"""Base provider protocol definition."""

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from src.database.models.vacancy import Vacancy


@runtime_checkable
class BaseProvider(Protocol):
    """Provider interface for collection orchestration."""

    def search(self, keyword: str, state: str, municipality: str) -> list[Vacancy]:
        """Search vacancies.

        Args:
            keyword (str): Search keyword.
            state (str): State filter.
            municipality (str): Municipality filter.

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

    def normalize(self, raw_data: Mapping[str, object]) -> Vacancy:
        """Normalize raw provider data into a vacancy.

        Args:
            raw_data (Mapping[str, object]): Raw vacancy data.

        Returns:
            Vacancy: Normalized vacancy.
        """
